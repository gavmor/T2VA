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

| Finding | Detail |
|---|---|
| `SPRITES.E3` (28 entries) | NOT frame/dimension metadata as originally hoped — each is a tiny (42-76 byte) float-heavy blob (scale/radius pairs, a frame-count field), i.e. animation/transform data for the game's renderer, not image data. |
| `PKDTEXTS.E3` (30 entries) | 25 of 30 don't parse at all under the current format understanding. 5 (`waterbot`, `fbot`, `scubagun`, `maqua`, `heli`) resolve to large (70KB-513KB) raw binary blobs with no discovered width/height header. |
| Byte inspection of the 5 blobs | Short ascending-run patterns consistent with **RLE-compressed palette-indexed pixel data** (not raw uncompressed pixels — file sizes don't factor into plausible width×height products), e.g. `(run_length, palette_index)` pairs. Confirmed prime/awkward-factoring byte counts (e.g. `waterbot` = 460721, prime) rule out a simple raw-bitmap read. |
| `.PAL` files | Present and trivially parseable (JASC-PAL text format) once/if pixel decode succeeds — color mapping is not the blocker. |

**Upgrade path (not started):** decoding the RLE structure for the 5
available blobs would unlock real reference-image conditioning (R2V mode,
`ref_image_0` input) for `waterbot`/`fbot`/`scubagun`/`maqua`/`heli` only —
the other 25 entries have no extractable image data under any current
finding and would need either further format RE or would stay in text-only
T2VA mode regardless. This is a nontrivial format reverse-engineering task
on its own, tracked as follow-up, not blocking this pipeline.
