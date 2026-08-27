# Experiment: H3 drawing-tutorial construction sheet

## Origin

Gavin flagged a real r/StableDiffusion post (48 upvotes, hosted video,
source art linked to ArtStation): someone fed MiniMax H3 a single finished
painting as `#Image1` with the prompt "Create a video tutorial of how this
particular painting was created... blank canvas -> basic forms -> detail
layer -> color/rendering layer -> final image", and got back a plausible
reverse-engineered construction video. Ask: apply the same idea to a T2VA
/ Esoteria roster asset, but produce a static multi-panel tutorial sheet
(classic art-instruction construction-sheet style) instead of a video.

## Scope note: no roster asset has real reference art

`data/raw_texture_status.md` (verified before starting this branch, not
assumed) is explicit: **no Esoteria character has decodable source pixel
art yet** -- that's the documented reason T2VA's production jobs run pure
text-to-video (`MiniMaxH3ReferenceToVideo`, no image input) for all 30
roster entries. The Reddit technique's literal premise (a real finished
painting as reference) doesn't have a real input to point at today.

**Substitution made for this validation:** used a still frame extracted
from an existing, already-rendered T2VA output --
`comfyui-local:/opt/ComfyUI/output/t2va/raven_00005_.mp4` (the real render
from this session's Immich-prompt-egress validation work, Aug 27 03:21) --
as the "finished artwork" stand-in for Raven. This is a genuine T2VA-native
asset, not invented content, but it is *not* the original game's character
art -- flagging explicitly so the result isn't mistaken for validating
against real Esoteria source material. `raven_reference_still.png` in this
directory is that extracted frame. `blank_canvas.png` is a synthesized flat
off-white 480x864 frame, standing in for "blank canvas" per the source
prompt's own instruction to start there.

## Hypothesis

A single MiniMax H3 `ImageToVideo` render, given a blank-canvas
`first_frame` and a rendered-character `last_frame`, and prompted with the
Reddit post's reverse-engineering-construction instruction (adapted to
reference Raven's roster description instead of "this particular
painting"), will produce a video whose interior frames read as a
plausible progressive build-up (basic forms -> structure/detail -> color)
rather than a degenerate direct interpolation or static-then-jump-cut
between the two endpoints.

## Dependent variable

Visual legibility of the 4-stage composited sheet: do the 2nd and 3rd
panels (sampled at t=5/8 and t=3/8 of duration -- see below) show
recognizable intermediate construction states, or do they look like
blurry linear-interpolation artifacts / near-duplicates of the first or
last panel? This is a qualitative human-judgment call (Gavin's), not an
automated metric -- explicitly a feasibility validation, not a
benchmarked comparison.

## Held constant / varied

This is a single-asset feasibility probe, not an A/B comparison -- no
second arm exists yet, so there's nothing to hold constant *against*. If
this validates, the natural next comparison (not run here) would be:
same asset, same seed, first_frame=blank vs. first_frame=omitted (letting
H3 free-run from `last_frame` alone per the original Reddit-post
mechanism, using `MiniMaxH3ReferenceToVideo`'s `#Image1` convention
instead of `ImageToVideo`'s explicit first/last-frame pinning) -- to see
whether pinning the start frame helps or constrains the construction
narrative.

Fixed for this run: asset (Raven), seed (900001), steps (8, matches T2VA's
existing turbo-LoRA config), resolution (480x864, matches raven's own
prior render), length (124 frames / ~5.17s, H3's default grid-snapped
length -- longer than the ~4.46s existing T2VA clips since a full
construction narrative needs more room than a 4-shot turnaround).

## Extraction method

Even-spaced sampling at the midpoint of 4 equal video segments (not
scdet cut-detection like T2VA's charref-sheets -- this is one continuous
morph with no hard cuts, so cut detection has nothing to find). See
`scripts/extract_and_compose_tutorial_sheet.py`.

## Status

Not yet run. Pushed to a dedicated `t2va-drawing-tutorial-validate`
Concourse pipeline (separate from the live `t2va` pipeline) pointed at
this branch, per this repo's existing "-validate" one-off pipeline
convention.
