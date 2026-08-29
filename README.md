# charref-gen

MiniMax H3 T2VA (text-to-video+audio) character-reference-sheet generation
for the full **Esoteria** (1998, Kirin Entertainment / Mobeus Designs)
playable-character + enemy roster, run through the same Concourse-gated
generative pipeline as `blades68-lora`'s `h3-charref-fullredo` job.

Standalone repo by design: separate from both `blades68-lora` (the Concourse
job architecture this ports) and `esoteria-remaster` (the in-engine asset
port, a distinct parallel effort -- see `data/raw_texture_status.md`). This
repo only reads roster names/lore from the Esoteria asset RE work; it does
not vendor or modify that codebase.

## Origin

The 4-shot template (head closeup / full-body front / back / side, neutral
A-pose) traces back to [u/bstr3k's "Using H3 as a Character Reference Sheet
Generator"](https://www.reddit.com/r/StableDiffusion/comments/1vr5nvc/using_h3_as_a_character_reference_sheet_generator/)
(r/StableDiffusion, 2026-08-17) -- multi-image reference (up to 9 images)
generating a static 360-degree character sheet, with the same "neutral A
pose" fixed prompt and a 4-panel/6-panel workflow choice. This wasn't
documented anywhere in this repo's or `blades68-lora`'s history until now
(found 2026-08-29); the technique itself was ported from `blades68-lora`'s
`h3-charref-fullredo` job, whose first ad hoc pilot (`gen_charref/`,
2026-08-17, gitignored, never committed) landed the same day as this post.

## Why T2VA mode (not image-conditioned R2V)

The Esoteria asset formats haven't been decoded far enough to produce real
character texture images to condition on -- see
[`data/raw_texture_status.md`](data/raw_texture_status.md) for the full
finding. Every roster entry renders as pure text-to-video (name + a short
description grounded in what's known about the character/enemy from the
game's OCR'd in-fiction lore), same technique as blades68-lora's validated
pilot.

## Roster

30 entries in [`data/roster.json`](data/roster.json), sourced from
`PKDTEXTS.E3`'s 30 named character/enemy slugs (the full known Esoteria
roster under the current asset-extraction understanding).

## Regenerating one character ("workshop" a single entry)

```sh
fly -t blades68 set-pipeline -p charref-gen -c concourse/pipeline.yml \
  -l concourse/vars.default.yml \
  -l ~/code/blades68-lora/concourse/.secrets/vars.yml \
  -v char_slug=raven
fly -t blades68 unpause-pipeline -p charref-gen
fly -t blades68 trigger-job -j charref-gen/charref-single -w
```

Swap `char_slug` and re-run to regenerate a different (or the same, with a
tweaked `data/roster.json` description) character. Output reference sheet
lands in `charref-sheets/<slug>_charref.png` inside that build.

## Running the full 30-character batch

```sh
fly -t blades68 set-pipeline -p charref-gen -c concourse/pipeline.yml \
  -l concourse/vars.default.yml \
  -l ~/code/blades68-lora/concourse/.secrets/vars.yml \
  -v charref_limit=""
fly -t blades68 trigger-job -j charref-gen/charref-batch-all -w
```

Set `-v charref_limit=2` first to cheaply validate the mechanism on 2 entries
before committing to the full batch -- same convention as blades68-lora's
`charref_limit`.

Finished sheets are packaged and published to the shared MinIO bucket under
the `t2va/` prefix (`t2va-sheets-s3` resource) as
`t2va-sheets-<timestamp>.tar.gz`.

## GPU safety

Both jobs acquire the same `gpu-lock` pool resource blades68-lora's pipeline
uses (this box has one physical 3090) -- `serial_groups: [gpu]` plus the
pool resource give cross-pipeline mutual exclusion. There is still no real
VRAM headroom pre-flight check on this Concourse deployment; don't run this
alongside another GPU job expecting both to fit.

## Layout

- `data/roster.json` -- the 30-character/enemy manifest source (slug,
  category, description)
- `data/raw_texture_status.md` -- what's actually been extracted from the
  Esoteria asset containers, and why it's not yet usable for R2V
- `scripts/build_manifest.py` -- roster.json -> full T2VA prompt manifest
  (gitignored `gen/manifest.json`, rebuilt fresh every run)
- `scripts/build_t2va_prompt.py` -- MiniMax H3 T2VA ComfyUI API-format
  prompt builder (node graph ported unchanged from blades68-lora)
- `scripts/extract_and_compose.py` -- ffmpeg cut-detection + ImageMagick
  2x2 reference-sheet compositing (ported unchanged from blades68-lora)
- `concourse/pipeline.yml` -- `charref-single` (one character, parameterized)
  and `charref-batch-all` (full roster) jobs
