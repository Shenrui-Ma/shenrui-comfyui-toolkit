"""Contract checks for the H3 Core AV latent continuation package.

These read only the package's own metadata and graph files. They do not start
ComfyUI, load weights or reach the network, so passing them says the graphs,
the interface and the dependency pins agree with each other, not that the
chain runs.
"""

import hashlib
import json
import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).parents[1]
INTERFACE = json.loads((PACKAGE / "interface.json").read_text(encoding="utf-8"))
DEPENDENCIES = json.loads((PACKAGE / "dependencies.lock.json").read_text(encoding="utf-8"))
GRAPHS = {name: json.loads((PACKAGE / name).read_text(encoding="utf-8"))
          for name in ("first.api.template.json", "continue.api.template.json")}
TOKEN_RE = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_RE = re.compile(r"(/Users/|/home/[a-z]|C:\\\\|192\.168\.|10\.\d+\.\d+\.\d+)")


class GraphShapeTests(unittest.TestCase):
    def test_package_files_agree_on_workflow_id(self):
        workflow_id = f"h3-{PACKAGE.name}"
        self.assertEqual(INTERFACE["workflow_id"], workflow_id)
        self.assertEqual(DEPENDENCIES["workflow_id"], workflow_id)

    def test_graph_files_are_pinned_by_hash(self):
        for name, digest in INTERFACE["graph"]["sha256"].items():
            self.assertRegex(digest, SHA256_RE)
            actual = hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest()
            self.assertEqual(digest, actual, name)

    def test_every_placeholder_is_declared_as_a_caller_input(self):
        declared = set(INTERFACE["caller_inputs"])
        for name, graph in GRAPHS.items():
            used = set(TOKEN_RE.findall(json.dumps(graph)))
            self.assertFalse(used - declared, f"{name}: {sorted(used - declared)}")

    def test_graphs_carry_no_leftover_concrete_values(self):
        forbidden = ["minimax_h3_ref2va", "qwen3vl", ".safetensors", "character.png",
                     "heartache/", "seg01", "seg02", "1344", "768"]
        for name, graph in GRAPHS.items():
            text = json.dumps(graph)
            for needle in forbidden:
                self.assertNotIn(needle, text, f"{name} still contains {needle}")

    def test_declared_node_classes_match_the_graphs(self):
        in_graph = set()
        for graph in GRAPHS.values():
            in_graph |= {node["class_type"] for node in graph.values()}
        declared = {node["class"] for node in INTERFACE["nodes"]}
        self.assertEqual(in_graph, declared)

    def test_core_and_custom_nodes_are_separated(self):
        core = {n["class"] for n in INTERFACE["nodes"] if n["kind"] == "core"}
        custom = {n["class"] for n in INTERFACE["nodes"] if n["kind"] == "custom"}
        self.assertEqual(custom, {"MiniMaxH3MotionContext"})
        self.assertEqual(core, set(DEPENDENCIES["core"]["required_node_classes"]))

    def test_first_graph_has_no_continuation_inputs(self):
        used = set(TOKEN_RE.findall(json.dumps(GRAPHS["first.api.template.json"])))
        self.assertNotIn("previous_video_latent", used)
        self.assertNotIn("context_length", used)

    def test_acknowledged_continuation_inputs_are_in_the_continue_graph(self):
        used = set(TOKEN_RE.findall(json.dumps(GRAPHS["continue.api.template.json"])))
        for required in ("previous_video_latent", "previous_audio_latent", "context_length"):
            self.assertIn(required, used)


class HonestyTests(unittest.TestCase):
    def test_package_states_it_was_not_run_here(self):
        self.assertIn("未执行", INTERFACE["verified"]["by_this_repository"])
        self.assertFalse(INTERFACE["verified"]["clean_install_inference_verified"])

    def test_no_python_outside_tests(self):
        self.assertEqual([p for p in PACKAGE.rglob("*.py") if "tests" not in p.parts], [])

    def test_no_private_paths_or_hosts_in_package_text(self):
        for path in sorted(PACKAGE.rglob("*")):
            if not path.is_file() or path.suffix not in (".json", ".md"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertIsNone(PRIVATE_RE.search(text), path.name)

    def test_unknown_model_files_stay_null_rather_than_guessed(self):
        for role, model in DEPENDENCIES["models"].items():
            if model["sha256"] is None:
                self.assertIsNone(model["filename"], role)
            else:
                self.assertRegex(model["sha256"], SHA256_RE)


if __name__ == "__main__":
    unittest.main()
