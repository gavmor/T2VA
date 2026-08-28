# Experiment: Comfy H3 Sync Sound Challenge entry (v1)

## Origin

Gavin flagged the official Comfy H3 Sync Sound Community Challenge
(blog.comfy.org/p/comfy-h3-sync-sound-community-challenge, verified
directly against the primary source, not the relay). Deadline 2026-09-01.
Hard rule confirmed from the post itself: audio must be generated natively
by H3 in the same pass -- no post-hoc stitching of a separately-made track.

## Why native audio isn't a blocker here

Already proven on this rig before starting this branch: `raven_00005_.mp4`
(an existing real T2VA production render) has genuine stereo AAC audio,
32kHz, mean volume -26.9dB / max -14.7dB, confirmed via `ffprobe` -- real
generated content, not silence. T2VA's production graph
(`scripts/build_t2va_prompt.py`) already exercises the audio-capable
`MiniMaxH3ReferenceToVideo` path for every roster entry. This entry reuses
that same node graph unchanged (see `scripts/build_sync_sound_prompt.py`,
the only difference is a parameterized `length` instead of the fixed
107-frame default, since this concept needs more room for two beats).

## Concept

A short tactical sync-cut vignette using Raven (T2VA's existing
protagonist asset, `data/roster.json` slug `raven`): a turn, a weapon-ready
foley beat, and one line of terse dialogue, all timed tightly to on-screen
motion -- plays to H3's demonstrated strength (audio-motion sync
precision) rather than a talking-head monologue or something requiring
multi-shot continuity H3 hasn't been validated on.

## Hypothesis

A single MiniMax H3 `ReferenceToVideo` render, prompted with an explicit
shot-by-shot description that ties each sound event (footfall, fabric
rustle, weapon servo-lock, dialogue) to a specific on-screen action beat,
will produce audio that is audibly synced to that motion -- not generic
ambience laid under unrelated visuals.

## Dependent variable

Qualitative human judgment (Gavin's) on: (a) do the footstep/turn sounds
land on the actual pivot motion, (b) does the weapon-lock sound land on
the weapon reaching ready position, (c) is the dialogue line's mouth
movement roughly lip-synced. Not an automated metric -- this is a
feasibility/quality probe for v1, same as the drawing-tutorial-sheet's own
first pass.

## Held constant / varied

Single-arm probe, not an A/B -- nothing to hold constant against yet.
Fixed for this run: asset (Raven, same `data/roster.json` description
used in production), seed (900001, same convention as every other
genops H3 experiment this session), resolution (480x864, matches T2VA
production), steps (8, matches production turbo-LoRA config), length
(158 frames / ~6.58s @ 24fps, H3's native 17k+5 grid, k=9 -- longer than
production's default 107/4.46s since this concept needs two shots instead
of one, but still a single native H3 generation, not the longer/unvalidated
LongMedia chaining path).

## Isolation

New branch `feature/h3-sync-sound-challenge`, own worktree, own isolated
Concourse pipeline `t2va-sync-sound-challenge` (gets `t2va-repo-experiment`
pointed at this branch, never applied over the live `t2va` pipeline).
Immich egress included for easy review, same `.description.txt` convention
as every other genops Immich-uploading job this session.

## Status

**v1: built, dispatched via Concourse (build 1, succeeded 2026-08-27, 22m26s).**
Technical verification done 2026-08-28: pulled the actual output straight
off `comfyui-local`'s output dir (`t2va-sync-sound/raven_sync_sound_v1_00001_.mp4`)
via ffprobe/ffmpeg, not from a claimed status line. Confirmed h264 480x864,
158 frames / 6.583s (exact match to spec), real stereo AAC audio 32kHz,
mean -20.1dB / max -0.5dB (non-silent, not clipped, hot but not silent).
Also confirmed live in Immich, album "Esoteria T2VA Character Sheets",
asset `28602f82-30d0-4f84-aef2-5fa816672dcd`.

Technical checks pass. **Qualitative call on actual audio-motion sync
(footfall-on-pivot, weapon-lock-on-raise, dialogue lip-sync) is still
Gavin's to make** -- not automated, per the Dependent Variable section
above. Not yet reviewed by him.
