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

**v1 (4-panel, live-scene background): ran, validated qualitatively.**
Build #1 on `t2va-drawing-tutorial-validate` succeeded end-to-end --
sheet legible as a real progressive sketch->structure->color->final
build-up, not a blurry interpolation. Gavin's verdict: "kind ok," with
two changes requested before iterating further:
1. The composited background was the live rendered alley scene (carried
   through every panel by the source video), not a paper/instructional
   look.
2. 4 panels felt coarse; wants 8 for finer-grained progression.

**v2 (8-panel, paper background): built, not yet run at time of writing.**
Both endpoint images changed:
- `blank_canvas_paper.png` -- a synthesized parchment-toned (232,220,194)
  textured canvas replacing the flat off-white `blank_canvas.png`.
- `raven_reference_paper_bg.png` -- `raven_reference_still.png` run
  through the genops `edit-image` skill (Krea 2 Identity Edit LoRA,
  local, no external calls) with an explicit full-background-replacement
  instruction (parchment/paper, no scene remnants). Chose this over
  post-hoc masking + paper composite of each extracted frame: fewer
  seams/edge artifacts, and it lets the whole H3 morph (not just the
  final frame) render against paper from the start, since v1 showed the
  model fills in background detail within the first ~0.6s regardless of
  what the literal first_frame pixel content was.
- `extract_and_compose_tutorial_sheet.py`: `N_STAGES` 4 -> 8, labels
  expanded to 8 stages, montage tile `2x2` -> `4x2`.
- Seed held at 900001 (unchanged from v1) to isolate the background/
  frame-count change as the only variable versus v1.

Same validation discipline as v1: single asset (Raven), isolated
`t2va-drawing-tutorial-validate` pipeline, no expansion until Gavin signs
off on this iteration.

**v2 ran.** Paper background and 8-panel count both landed cleanly. Bonus,
unprompted: a drawing hand appeared mid-stroke through the sketch/lineart
stages, dropping out once the piece moved into color/rendering -- reads
as a genuine "how it was drawn" tutorial rather than a static morph.

Gavin's verdict: "Not great. We want the shape primitives." The early
panels ("Basic Forms"/"Rough Structure"/"Detail Pass") rendered as a
flat gesture-outline sketch (head circle -> torso blob -> body contour),
not the classic Loomis/Reilly geometric-primitive blocking-in method
(sphere skull, box ribcage, box pelvis, cylinder limbs, visibly
three-dimensional) that the original Reddit prompt's "basic forms,
shapes, rectangles, cylinders, cones" phrasing was meant to produce.

**v3 (prompt rewrite, same images/frame-count/seed): ran, succeeded**
(`t2va-drawing-tutorial-validate` build 3, 2026-08-26). Loomis-primitive
construction stages rendered as intended (visible dimensional sphere/box/
cylinder/cone blocking, not a flat gesture outline). Output:
`raven_tutorial_sheet.png`. Also generalized to a second asset, constbot
(robot), same prompt unchanged (`t2va-drawing-tutorial-validate-constbot`).

**v4 (raven-nohand, same v3 prompt + one added sentence: "no hand, pencil,
or other drawing implement is ever visible in frame"): ran, succeeded**
(`t2va-drawing-tutorial-validate-raven-nohand` build 1, 2026-08-27).
**Did not work** -- Gavin reviewed `raven-nohand_tutorial_sheet.png` and a
hand/pencil is still clearly visible in 6 of 8 panels (everything except
"Blank Canvas" and "Final Render"). Pure negation ("no hand ever visible")
did not suppress the concept; naming "hand"/"pencil" in the prompt at all
appears to prime the model to render them regardless of the negating
language, a known failure mode for negative instructions in text-to-video
generation.

**v5 (raven-nohand-v2, affirmative rephrasing): built, dispatched via
Concourse, not yet reviewed.**

Hypothesis: rewriting the instruction to never name "hand," "pencil," or
"drawing implement" at all -- instead framing the shot as a locked-off
overhead view where the page fills the entire frame at all times, and
lines/shading/color "appear on the page on their own, as though drawn by
an unseen artist" -- will suppress the hand/pencil concept where pure
negation failed, since the model has nothing to attend to as a visual
target for that concept.

Dependent variable: same as v4 -- does a hand or pencil/tool appear in
any of the 8 panels. Binary pass/fail this time, not the original
gesture-vs-primitive legibility judgment.

Held constant vs. v4: asset (Raven), seed (900001), first/last-frame
images (`blank_canvas_paper.png`, `raven_reference_paper_bg.png`),
frame count (124), 8-panel extraction. Only the prompt text's phrasing
of the hand-suppression instruction changed (negative -> affirmative,
no more "hand"/"pencil"/"drawing implement" tokens anywhere in the
prompt). New job `t2va-drawing-tutorial-validate-raven-nohand-v2` in
`concourse/pipeline.yml`, output slug `raven-nohand-v2`.
