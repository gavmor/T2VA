# Raw texture extraction status (read-only, from the Esoteria asset RE work)

Source: Esoteria's `PKDTEXTS.E3` / `SPRITES.E3` containers (30-entry named
roster, matching `data/roster.json`'s slugs), extracted read-only via the
separate `esoteria-diegetic-text` reverse-engineering effort (not vendored
here — see that workspace's `e3_unpack.py`/`decode_textures.py` for the
extraction code itself).

**Current state: no character has a decodable pixel image yet.** This
pipeline runs in **T2VA (text-to-video+audio) mode** — no reference image
input — for every entry, matching the validated `h3-charref-fullredo`
technique in `blades68-lora`.

**2026-08-28 correction:** the "5 of 30" framing below was wrong — checked
directly against `PKDTEXTS.E3` with the `esoteria-diegetic-text` workspace's
own `e3_unpack.py` (the same parser that cracked 1009/1136 `TEXTURES.E3`
entries) rather than re-deriving a parse from scratch. **All 30 top-level
entries** parse cleanly as named nested `E3v1.0` sub-containers (one per
roster slug), ranging 18KB (`probe`) to 2.1MB (`raven`, the single largest
entry in the file) — not "5 large, 25 unparseable." `raven.e3` was
spot-checked in detail (see `data/reference/raven-1998-screenshots/SOURCE.md`):
it does *not* fit `TEXTURES.E3`'s `CAnimatedTextureDef` layout (that decoder
produces garbage on it), but manual byte inspection shows a real object-name
string (`"raven\x00"`) followed by what looks like a 256-entry palette/remap
table — consistent with the RLE theory below, just not yet confirmed
end-to-end on any single entry.

| Finding | Detail |
|---|---|
| `SPRITES.E3` (28 entries) | NOT frame/dimension metadata as originally hoped — each is a tiny (42-76 byte) float-heavy blob (scale/radius pairs, a frame-count field), i.e. animation/transform data for the game's renderer, not image data. |
| `PKDTEXTS.E3` (30 entries, all of them) | All 30 named entries (`raven.e3`, `rival.e3`, `guardian.e3`, etc. — the full `roster.json` slug list) are large (18KB-2.1MB) nested sub-containers, not plain `CAnimatedTextureDef` structures like `TEXTURES.E3`. No confirmed width/height header found yet on any entry. |
| Byte inspection (`raven.e3`, `waterbot` and others) | Short ascending-run patterns consistent with **RLE-compressed palette-indexed pixel data** (not raw uncompressed pixels — file sizes don't factor into plausible width×height products), e.g. `(run_length, palette_index)` pairs. Confirmed prime/awkward-factoring byte counts (e.g. `waterbot` = 460721, prime) rule out a simple raw-bitmap read. |
| `.PAL` files | Present and trivially parseable (JASC-PAL text format) once/if pixel decode succeeds — color mapping is not the blocker. |

**Upgrade path (not started):** decoding the RLE structure would potentially
unlock real reference-image conditioning (R2V mode, `ref_image_0` input) for
*all 30* roster entries, not just the 5 previously assumed — since all 30
now look like the same structural format, just none of them decoded yet.
This is a nontrivial format reverse-engineering task on its own, tracked as
follow-up, not blocking this pipeline. In the meantime, for `raven` at least,
real 1998 game screenshots (not a sprite decode) already gave enough visual
grounding to fix a real prompt mismatch — see
`data/reference/raven-1998-screenshots/SOURCE.md`.
