# Heartache native AV latent graphs

Recovered graph data for the bit-by-bit-heartache recipe by Shenrui Ma（四倍体果蝇）. These are **sanitized reconstructions**, not original ComfyUI editor workflows or complete historical POST bodies. See `manifest.json` for every file hash, node source, sanitization and missing dependency. No GPU inference has been rerun for this package.

- `recovered-segment-01..04.api.json`: historical comparison only; replace input and continuation paths before use. Seeds are decimal strings and must be parsed to integers before API submission.
- `first.api.template.json`: first segment.
- `continue.api.template.json`: repeat for any subsequent segment, after its predecessor's canonical AV latent has completed.

## Parameters and binding

Whole-value `{{name}}` placeholders must be replaced with typed values, not string interpolation. Integer fields: `width`, `height`, `sample_frames`, `seed`, `steps`, `visible_frames`. String fields: `diffusion_model`, `text_encoder`, `video_vae`, `audio_vae`, `prompt`, `video_prefix`, `latent_prefix`, `metadata_json`, `reference_image`, `reference_video`, and continuation-only `previous_latent`.

`metadata_json` is a serialized JSON object containing at least width, height, fps (24), transformer, video_vae, audio_vae and the actual seed/prompt. The Save node also writes canonical schema, visible/trim and context endpoint fields. Model names must match the loader and predecessor. Reference paths are ComfyUI input names; previous_latent is a path accessible to the installed Load node on that server. Never guess an output suffix: obtain the saved latent from execution output/history.

Plan sample frames on the `17k+5` grid including context. The continuation template uses the historical 22-frame video context and audio parameter24. The actual MotionContext output drives Trim. Visible frames must fit after trimming. These two templates do not impose a four-segment schedule. For a changed frame rate or context policy, verify the node implementation rather than changing only CreateVideo.

The first-segment graph saves the entire decoded sample. If sample_frames exceeds visible_frames, trim the first clip to the planned visible range during postprocessing; setting the Save-latent metadata alone does not trim the MP4.

After binding, verify that no placeholders remain, check every node against the target `/object_info`, then submit the API graph. This package does not yet contain an end-to-end installer or orchestration runner. Do not treat the repository's generic prompt injection runner as a `{{...}}` template renderer without verifying its behavior.

## Dependencies and blockers

Core nodes and all four non-Core classes are individually listed in `manifest.json`. `MiniMaxH3MotionContext` comes from [NikoDemon80/ComfyUI-H3-Motion-Context](https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context), GPL-3.0; the inspected current checkout is f80e36bc1d7887a143b12e6645313fd6b9cd2aee, with local nodes.py modifications, not a historical lock.

`SaveMiniMaxH3AVLatent`, `LoadMiniMaxH3AVLatent` and `TrimMiniMaxH3MotionContext` come from the author's local HermesH3Continuation package. Its source has been located but the complete public install package and license are not established here. No third-party node Python is redistributed in this graph directory. `install_ready=false` remains until this dependency and compatible Core/patch versions are published and tested.

The historical driver has no audio connection to Ref2VA. Continuation carries generated AV context; the final soundtrack is replaced in editing. The historical prompt's audio-copy statements do not prove a connected source soundtrack.
