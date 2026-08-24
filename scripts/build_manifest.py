#!/usr/bin/env python3
"""Build the T2VA render manifest from data/roster.json.

Follows blades68-lora's "script committed, manifest generated fresh at
build time" convention (see build_charref_fullredo.py): this file is
committed, gen/manifest.json is gitignored and rebuilt on every Concourse
run so the roster is the single source of truth.

4-shot prompt template (head closeup / full-body front / back / side,
neutral A-pose) is ported unchanged from the validated h3-charref-fullredo
technique -- only STYLE_ANCHOR differs, swapped for Esoteria's own
in-fiction setting (Regime-controlled dystopian city, per the OCR'd
in-game datapad transcripts in esoteria-diegetic-text/textures-ocr/) instead
of blades68's mid-century Pop Art anchor.

Usage:
    python3 build_manifest.py                  # full 30-entry roster
    python3 build_manifest.py --slug raven      # single entry, for a
                                                 # workshop/regen run
    python3 build_manifest.py --limit 2         # first N, for cheaply
                                                 # validating the pipeline
"""
import argparse
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROSTER_PATH = os.path.join(BASE_DIR, "data", "roster.json")
OUT_DIR = os.path.join(BASE_DIR, "gen")

STYLE_ANCHOR = (
    "Style: gritty late-1990s 3D action-game concept art, industrial "
    "dystopian sci-fi, cold fluorescent and neon-signage lighting, worn "
    "metal and riveted plating textures, CRT scanline sheen. Setting: "
    "Esoteria, a Regime-controlled industrial city under Master Control's "
    "surveillance -- checkpoint fencing, cable-strewn corridors, muted "
    "teal-and-rust palette. Static character-reference turnaround sheet, "
    "locked-off camera, hard cuts between shots, no camera movement, no "
    "set dressing beyond a plain backdrop, no props beyond those held. No "
    "dialogue, no ambient sound, no music, non_diegetic_music: N/A."
)


# Categories with no body/limbs to pose -- the organism-shaped "full-body
# A-pose" template (below) makes the model hallucinate a human body wearing
# the vehicle/drone as a head (confirmed live 2026-08-24 on carrier/tank/
# probe's first batch render: shot 1 correctly showed the machine, shots
# 2-4 showed a soldier instead). These get an object-appropriate template:
# no pose language, just camera angle around the whole machine.
OBJECT_CATEGORIES = {"vehicle", "drone"}


def build_prompt(entry):
    desc = entry["description"]
    if entry["category"] in OBJECT_CATEGORIES:
        return (
            f"[Shot 1, 0:00-0:01, static freeze-frame] Close-up detail "
            f"shot, no motion: {desc}. "
            f"[Shot 2, 0:01-0:02, hard cut] Full view of the entire "
            f"machine from the front, three-quarter angle: {desc}. "
            f"[Shot 3, 0:02-0:03, hard cut] Full view of the entire "
            f"machine from directly behind: {desc}. "
            f"[Shot 4, 0:03-0:04, hard cut] Full view of the entire "
            f"machine from the side, profile facing camera-right: {desc}. "
            f"{STYLE_ANCHOR}"
        )
    return (
        f"[Shot 1, 0:00-0:01, static freeze-frame] Head-and-shoulders "
        f"close-up, direct-to-camera neutral gaze, no motion: {desc}. "
        f"[Shot 2, 0:01-0:02, hard cut] Full-body shot, head to toe, "
        f"facing camera, standing in a neutral A-pose with limbs slightly "
        f"away from the body: {desc}. "
        f"[Shot 3, 0:02-0:03, hard cut] Full-body shot, head to toe, "
        f"viewed directly from behind, same neutral A-pose: {desc}. "
        f"[Shot 4, 0:03-0:04, hard cut] Full-body shot, head to toe, side "
        f"profile facing camera-right, same neutral A-pose: {desc}. "
        f"{STYLE_ANCHOR}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="only emit this one roster entry, by slug")
    ap.add_argument("--limit", type=int, default=None,
                     help="only emit the first N entries, for cheaply "
                          "validating the render pipeline before "
                          "committing to the full roster batch")
    args = ap.parse_args()

    with open(ROSTER_PATH) as f:
        roster = json.load(f)

    if args.slug:
        roster = [e for e in roster if e["slug"] == args.slug]
        if not roster:
            raise SystemExit(f"no roster entry with slug={args.slug!r}")
    elif args.limit is not None:
        roster = roster[:args.limit]

    manifest = []
    for i, e in enumerate(roster):
        manifest.append({
            "slug": e["slug"],
            "category": e["category"],
            "target_filename": f"{e['slug']}.png",
            "seed": 700000 + i,
            "prompt": build_prompt(e),
        })

    os.makedirs(OUT_DIR, exist_ok=True)
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Wrote {manifest_path} with {len(manifest)} entries")
    for e in manifest:
        print(f"  - {e['slug']} (seed={e['seed']})")


if __name__ == "__main__":
    main()
