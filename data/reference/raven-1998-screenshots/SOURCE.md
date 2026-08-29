# Raven visual reference (real, not lore-text guesswork)

Source: MyAbandonware's screenshot gallery for the original 1998 retail
release (`myabandonware.com/game/esoteria-techno-assassin-of-the-future-dqi`,
screenshots 2/3/9/10 of 12) and the Internet Archive's playable demo listing
(`archive.org/details/estdemo`). Pulled 2026-08-28 in response to Gavin's
report that renders were misrepresenting Raven -- these are genuine
in-engine screenshots from the original game, not AI-generated or fan art.

## What they actually show (Raven, gameplay_back_view_1/2, gameplay_third_person)

Third-person view of the player-controlled Raven model:

- **Bulky, blocky powered-armor / mini-mech suit** -- not a lean/slim
  bodysuit. Wide boxy shoulders, thick articulated limbs.
- **Color scheme**: white/light-gray primary plating, black/dark-navy
  joints and trim, a distinct red/orange accent on the back of the
  helmet (reads as a rear sensor or visor).
- **Loadout per the in-game HUD**: machine gun, "Gyrex cannon," missiles
  (homing), V-bomb, trigger bomb, time bomb -- a heavy-ordnance arsenal,
  not a single sleek "energy weapon."
- Gender is not visually determinable -- the suit and helmet are fully
  enclosing in every available shot.

## rival_data_transmission_portrait

The in-game "Final Transmission" data-file screen (introduces the RIVAL
antagonist, a second Raven-Project clone with "all of your capabilities
and ... some others"). Same white/black armored silhouette as Raven, plus
a blue energy/wing motif not present on Raven's own model.

## What this fixed

`data/roster.json`'s `raven`/`raven4`/`rival` descriptions previously said
"lean tactical bodysuit, energy weapon" -- invented language with no real
source, since none of the OCR'd in-game lore text (`esoteria-diegetic-text`
workspace) describes physical appearance at all. Updated to match what's
actually on screen (2026-08-28).

## Broader implication (not yet acted on)

All 30 `roster.json` entries were written the same way -- OCR'd lore-text
only, no visual cross-check against any screenshot/sprite. Raven wasn't
special-cased; it's just the one that got checked. Worth auditing the
rest against MyAbandonware/Internet Archive screenshots (or a real
PKDTEXTS.E3 sprite decode, see below) before trusting their renders either.

## Sprite-decode path: attempted, not solved

`PKDTEXTS.E3` (in `/tmp/esoteria_extract/ESOTERIA/`) has real named entries
for Raven: `raven.e3` (2,115,588 bytes -- the single largest entry in the
whole 30-entry container) and `raven4.e3` (718,406 bytes). This is a real,
substantial per-character data blob, not a placeholder.

Tried applying `esoteria-diegetic-text/textures-ocr/decode_textures.py`'s
`CAnimatedTextureDef` parser (the one that successfully cracked 1009/1136
`TEXTURES.E3` entries) directly to `raven.e3`'s bytes -- it does **not**
fit that layout; the fields decode to garbage. Manual byte inspection
shows the object name "raven\x00" followed by what looks like a 256-byte
palette/remap table (near-sequential byte values 0x00-0xff), consistent
with `T2VA/data/raw_texture_status.md`'s existing theory that
`PKDTEXTS.E3`/`SPRITES.E3` use RLE-compressed palette-indexed pixel data,
a structurally different and still-uncracked format from `TEXTURES.E3`'s
simpler raw-grayscale one. Nobody has actually attempted this decode
before now (the diegetic-text OCR effort explicitly skipped
`PKDTEXTS.E3`/`SPRITES.E3` as non-text-bearing by name inspection alone,
never tried to decode pixels from it). Real sprite data for Raven likely
exists in there, but cracking it is a genuine, nontrivial RLE-format
reverse-engineering task on its own -- not done here, not blocking this
fix since the 1998 screenshots already gave real, sufficient grounding.

## Cutscene footage: also checked directly, not just summarized

`esoteria-diegetic-text/frames-ending/scene_0005.png` (Ending.avi, in front
of the "SANGUINE DRAK"/"HUEY HUNTER" wall posters the README already
identified) shows a bulky white-and-blue armored humanoid walking beside a
large silver mech -- corroborates the gameplay-screenshot finding above
(bulky powered armor, not lean) from a second, independent source. Accent
color reads blue here vs. red in the daylight gameplay screenshots, which
could be scene lighting (dim blue-lit night street) rather than a real
palette difference -- not fully resolved, noted as a caveat.

`scene_0009.png`/`scene_0013.png` (later in the same cutscene) show a
different, sleek dark-suited humanoid with a glowing red eye and a
swept-back head crest -- clearly not the bulky armored figure from
scene_0005. Identity not determined (Rival? a separate antagonist? the
"Solbzen" the RIVAL transmission text mentions?) -- flagging as an open
question rather than guessing; did not fold this into any roster.json
description.
