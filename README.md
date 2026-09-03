<div align="center">
  <img src="assets/silverwolf-comfyui-sticker.png" width="360" alt="Silver Wolf using a colorful ComfyUI node graph">

  # Shenrui ComfyUI Toolkit

  **Agent-friendly tools and practical playbooks for running ComfyUI locally or remotely.**

  [简体中文](README.zh-CN.md) · [Skill entry](SKILL.md) · [Local guide](references/local.md) · [Remote guide](references/remote-server.md)
</div>

> [!IMPORTANT]
> This is an unofficial community project. It is not affiliated with or endorsed by ComfyUI, Nous Research, HoYoverse, or any model provider.

## What it does today

- Routes image-generation jobs to a local ComfyUI instance or an authorized remote instance.
- Runs API-format workflows with parameter injection, uploads, progress monitoring, and original-output downloads.
- Converts common editor-format workflows for controlled batch execution with independent random seeds.
- Verifies completion through ComfyUI history instead of treating a returned `prompt_id` as success.
- Preserves original output files and guards downloads against path traversal.
- Keeps machine-specific paths, server names, accounts, and credentials out of the repository.

The repository is intentionally small today. Its scope will grow toward reusable model-sync procedures, workflow curation, image/video recipes, and prompt-adaptation notes.

## Requirements

- Python 3.10+
- A reachable [ComfyUI](https://github.com/comfyanonymous/ComfyUI) instance
- A ComfyUI workflow in API format, or a compatible editor-format workflow
- Optional: `requests` for uploads and more robust HTTP handling
- Optional: `websocket-client` for live WebSocket progress

No credential is bundled. Supply connection details at runtime through environment variables, an SSH configuration you already control, or command-line options where appropriate.

## Install as an agent skill

Clone the repository and copy or symlink it into the skills directory used by your agent. For Hermes:

```bash
git clone https://github.com/Shenrui-Ma/shenrui-comfyui-toolkit.git
mkdir -p ~/.hermes/skills/creative
ln -s "$(pwd)/shenrui-comfyui-toolkit" \
  ~/.hermes/skills/creative/shenrui-comfyui-toolkit
```

The entry point is [`SKILL.md`](SKILL.md). The repository does not overwrite an existing ComfyUI installation or skill.

## Quick start

### Local ComfyUI

```bash
export COMFY_URL='http://127.0.0.1:8188'

python3 scripts/run_workflow.py \
  --host "$COMFY_URL" \
  --workflow /path/to/workflow_api.json \
  --args '{"prompt":"your prompt","seed":-1}' \
  --output-dir ./outputs \
  --ws
```

### Remote ComfyUI

Expose only an instance you are authorized to use. A typical SSH tunnel looks like:

```bash
export REMOTE_USER='your-user'
export REMOTE_HOST='your-host'
export LOCAL_PORT='8188'
export REMOTE_PORT='8188'

ssh -N \
  -L "127.0.0.1:${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" \
  "${REMOTE_USER}@${REMOTE_HOST}"

export COMFY_URL="http://127.0.0.1:${LOCAL_PORT}"
```

Then use the same runner with `--host "$COMFY_URL"`. See the [remote guide](references/remote-server.md) for preflight and ownership checks.

### Saved editor-format workflow

```bash
python3 scripts/run_saved_workflow_batch.py \
  --host "$COMFY_URL" \
  --workflow /path/to/saved_editor_workflow.json \
  --prompt 'your prompt' \
  --count 1 \
  --output-dir ./outputs
```

Run one image and validate its parameters before starting a large batch.

## Repository layout

```text
.
├── SKILL.md                         # Agent instructions and routing rules
├── references/
│   ├── local.md                     # Local ComfyUI playbook
│   └── remote-server.md             # Authorized remote execution playbook
├── scripts/
│   ├── _common.py                   # Shared transport and safety helpers
│   ├── run_workflow.py              # API-format workflow runner
│   └── run_saved_workflow_batch.py  # Editor-format batch runner
├── tests/                            # Regression tests
└── assets/                           # Repository artwork
```

## Safety and privacy

- Never commit API keys, passwords, cookies, SSH keys, private hostnames, or real infrastructure paths.
- Review workflow JSON and image metadata before publishing them; both may contain prompts, local paths, model names, or input filenames.
- Treat third-party custom nodes and workflows as executable code.
- Do not stop remote processes or occupy GPUs until ownership and authorization are clear.
- Prefer environment variables over command-line credentials because command lines may be retained in shell history or process listings.

## Roadmap

- Model inventory, verification, and synchronization recipes
- Curated and reproducible image-generation workflows
- Image-to-video and text-to-video execution guides
- Prompt adaptation notes across model families
- Workflow dependency inspection and recovery tools
- Additional agent skills under a stable repository structure

## Development

Run the dependency-free regression suite:

```bash
python3 -B -m unittest discover -s tests -v
```

Both runners expose `--help` without writing bytecode caches when invoked with `python3 -B`.

## Credits and license

Parts of the shared runner implementation are adapted from the ComfyUI skill in [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), with contributions credited in [`NOTICE.md`](NOTICE.md). The software and documentation in this repository are released under the [MIT License](LICENSE), except for third-party names, trademarks, and character depictions.

The Silver Wolf sticker is unofficial fan art generated for this repository. Silver Wolf and *Honkai: Star Rail* belong to their respective rights holders; the character depiction is not offered under the MIT software license.
