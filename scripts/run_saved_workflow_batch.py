#!/usr/bin/env python3
"""
Batch-run a saved editor-format ComfyUI workflow against a remote server.
Converts editor format → API format, submits N jobs with unique seeds,
polls all in parallel, downloads outputs.

Usage:
  python3 scripts/run_saved_workflow_batch.py \
    --workflow /tmp/workflow.json \
    --host http://127.0.0.1:8188 \
    --prompt "a cat" \
    --count 5 \
    --output-dir ./outputs
"""

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import safe_path_join  # noqa: E402


def _safe_component(value):
    """Return a filesystem-safe label for server-controlled metadata."""
    component = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._")
    return component or "unknown"


def _server_basename(filename):
    """Flatten POSIX and Windows-style server paths to one filename."""
    name = str(filename).replace("\\", "/").rsplit("/", 1)[-1]
    if name in ("", ".", ".."):
        raise ValueError(f"Invalid server filename: {filename!r}")
    return name


def local_output_path(output_dir, prompt_id, node_id, filename):
    """Build a flat output path that cannot escape ``output_dir``."""
    local_name = (
        f"{_safe_component(str(prompt_id)[:8])}_"
        f"node{_safe_component(node_id)}_{_server_basename(filename)}"
    )
    return safe_path_join(Path(output_dir), local_name)


def build_view_url(host, filename, subfolder, image_type):
    """Build a correctly encoded ComfyUI output URL."""
    query = urlencode({
        "filename": filename,
        "subfolder": subfolder,
        "type": image_type,
    })
    return f"{host.rstrip('/')}/view?{query}"

def convert_editor_to_api(editor_json, prompt_text, seed, extra_bridges=None):
    """Convert editor-format workflow to ComfyUI API prompt format.

    Handles: PrimitiveNode inlining, seed randomization controls,
    widgets_values alignment (including linked widgets),
    and manual bridge connections (e.g. VAEEncode → KSampler latent_image).
    """
    nodes = editor_json["nodes"]
    links = editor_json["links"]
    link_map = {l[0]: [str(l[1]), l[2]] for l in links}
    node_map = {str(n["id"]): n for n in nodes}

    api_nodes = {}
    for n in nodes:
        nid = str(n["id"])
        ntype = n["type"]
        if ntype == "PrimitiveNode":
            continue

        inputs = {}
        wv = n.get("widgets_values", [])
        wv_idx = 0

        for inp in n.get("inputs", []):
            name = inp["name"]
            link_id = inp.get("link")
            has_widget = "widget" in inp

            if link_id is not None:
                origin = link_map.get(link_id)
                if origin:
                    orig_nid, orig_slot = origin
                    orig_node = node_map.get(orig_nid)
                    if orig_node and orig_node["type"] == "PrimitiveNode":
                        pwv = orig_node.get("widgets_values", [])
                        if pwv:
                            val = pwv[0]
                            is_random = len(pwv) > 1 and pwv[1] == "randomize"
                            if is_random or (isinstance(val, str) and val == "randomize"):
                                val = seed
                            inputs[name] = val
                    else:
                        inputs[name] = [orig_nid, orig_slot]

                if has_widget and wv_idx < len(wv):
                    wv_idx += 1
                    if name in ("seed", "noise_seed") and wv_idx < len(wv):
                        if isinstance(wv[wv_idx], str) and wv[wv_idx] in ("randomize", "fixed"):
                            wv_idx += 1
                continue

            if not has_widget:
                continue

            if wv_idx >= len(wv):
                continue

            val = wv[wv_idx]
            wv_idx += 1

            if name in ("seed", "noise_seed"):
                if wv_idx < len(wv) and isinstance(wv[wv_idx], str) and wv[wv_idx] in ("randomize", "fixed"):
                    wv_idx += 1
                    val = seed

            inputs[name] = val

        api_nodes[nid] = {"class_type": ntype, "inputs": inputs}

    # Override the positive prompt CLIPTextEncode node only — find which
    # node IDs feed into KSampler/FaceDetailer's "positive" input.
    positive_nids = set()
    for nid, node in api_nodes.items():
        for inp_name, inp_val in node.get("inputs", {}).items():
            if inp_name == "positive" and isinstance(inp_val, list) and len(inp_val) == 2:
                positive_nids.add(inp_val[0])
    # If no positive nodes detected via links, fall back to the last CLIPTextEncode
    # (heuristic: positive prompt nodes tend to have longer text)
    if not positive_nids:
        text_nodes = [(nid, len(node["inputs"].get("text", "")))
                      for nid, node in api_nodes.items()
                      if node["class_type"] == "CLIPTextEncode"]
        if text_nodes:
            positive_nids.add(max(text_nodes, key=lambda x: x[1])[0])

    for nid, node in api_nodes.items():
        if nid in positive_nids and node["class_type"] == "CLIPTextEncode":
            node["inputs"]["text"] = prompt_text

    # Apply explicit bridges (missing connections in saved UI workflows)
    if extra_bridges:
        for target_nid, input_name, source_ref in extra_bridges:
            if target_nid in api_nodes:
                api_nodes[target_nid]["inputs"][input_name] = source_ref

    return api_nodes


def submit(host, api_prompt):
    data = json.dumps({"prompt": api_prompt}).encode("utf-8")
    req = urllib.request.Request(f"{host}/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        pid = result.get("prompt_id")
        if pid:
            return pid, None
        return None, json.dumps(result.get("node_errors", {}) or result.get("error", ""))[:300]
    except urllib.error.HTTPError as e:
        return None, e.read().decode("utf-8", errors="replace")[:500]


def wait_all(host, prompt_ids, output_dir, timeout_per_job=600):
    results = {}
    pending = set(prompt_ids)
    start = time.time()

    while pending and (time.time() - start) < timeout_per_job * len(prompt_ids):
        time.sleep(5)
        for pid in list(pending):
            try:
                req = urllib.request.Request(f"{host}/history/{pid}")
                resp = urllib.request.urlopen(req, timeout=10)
                history = json.loads(resp.read())
                if pid in history:
                    entry = history[pid]
                    status = entry.get("status", {})
                    if not status.get("completed", False):
                        continue
                    outputs = entry.get("outputs", {})
                    files = []
                    for node_id, node_output in outputs.items():
                        for img in node_output.get("images", []):
                            filename = img["filename"]
                            subfolder = img.get("subfolder", "")
                            img_type = img.get("type", "output")
                            url = build_view_url(host, filename, subfolder, img_type)
                            local_path = local_output_path(
                                output_dir, pid, node_id, filename
                            )
                            urllib.request.urlretrieve(url, local_path)
                            files.append(str(local_path))
                    results[pid] = files
                    pending.discard(pid)
                    print(f"  {pid[:8]} done: {len(files)} files", file=sys.stderr)
            except Exception:
                continue

    if pending:
        print(f"  {len(pending)} jobs still pending after timeout", file=sys.stderr)
    return results


def main():
    parser = argparse.ArgumentParser(description="Batch-run a saved ComfyUI workflow")
    parser.add_argument("--workflow", required=True, help="Path to editor-format workflow JSON")
    parser.add_argument("--host", default="http://127.0.0.1:8188", help="ComfyUI host")
    parser.add_argument("--prompt", required=True, help="Prompt text to inject")
    parser.add_argument("--count", type=int, default=1, help="Number of jobs")
    parser.add_argument("--output-dir", default="./outputs", help="Output directory")
    parser.add_argument("--bridge", action="append", nargs=3, metavar=("NODE", "INPUT", "REF"),
                        help="Add manual bridge: NODE INPUT REF (e.g. 17 latent_image '[4,0]')")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.workflow) as f:
        editor = json.load(f)

    # Parse bridges
    extra_bridges = []
    if args.bridge:
        for target_nid, input_name, ref_str in args.bridge:
            try:
                ref = json.loads(ref_str)
            except json.JSONDecodeError:
                ref = ref_str
            extra_bridges.append((target_nid, input_name, ref))

    # Submit all jobs
    job_map = {}
    for i in range(args.count):
        seed = random.randint(0, 2**63 - 1)
        api = convert_editor_to_api(editor, args.prompt, seed, extra_bridges)
        pid, err = submit(args.host, api)
        if pid:
            job_map[pid] = (i, seed)
            print(f"  [{i:02d}] {pid[:8]} seed={seed}", file=sys.stderr)
        else:
            print(f"  [{i:02d}] FAILED: {err}", file=sys.stderr)

    print(f"\nSubmitted {len(job_map)}/{args.count} jobs, waiting...", file=sys.stderr)

    # Wait for all and download
    all_results = wait_all(args.host, list(job_map.keys()), args.output_dir)

    # Output JSON map
    final = {}
    for pid, files in all_results.items():
        if pid in job_map:
            idx, seed = job_map[pid]
            final[f"job_{idx:02d}"] = {"seed": seed, "files": files, "prompt_id": pid}

    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()
