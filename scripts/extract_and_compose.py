#!/usr/bin/env python3
"""
Frame extraction + composition for T2VA character-reference clips: turns
each 4-shot T2VA clip into a single 2x2 reference-sheet still (head
closeup / full-body front / back / side).

Ported unchanged (ffmpeg scdet cut detection, ImageMagick montage) from
blades68-lora's projects/blades68/scripts/charref_extract_and_compose.py --
that script's docstring has the full rationale for the scdet-based cut
detection over fixed timestamps.

Usage:
    python3 extract_and_compose.py --all --manifest gen/manifest.json \
        --video-dir raw-videos --stills-dir /tmp/stills --sheets-dir sheets
    python3 extract_and_compose.py --slug raven ...
"""
import argparse
import json
import os
import re
import subprocess

SHOT_LABELS = ["Head", "Front", "Back", "Side"]
N_SHOTS = 4
CUT_SCORE_FLOOR = 1.0
DEFAULT_FONT = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"


def write_description_sidecar(entry, sheet_path):
    """Writes a plain-text <sheet>.description.txt next to the composed
    reference sheet so immich-concourse-resource's out script (>=
    edge-1b08091) auto-detects and binds it, landing the render prompt in
    the Immich asset's exifInfo.description field via a direct, synchronous
    PUT /api/assets/{id} -- no XML envelope or escaping needed on this side.
    Supersedes an earlier hand-rolled XMP-sidecar version of this function
    (this repo's own history, feature/immich-prompt-egress) once the
    resource grew this convention natively -- see
    gavmor/immich-concourse-resource#1 and gavmor/comfyui-workflows#13,
    which made the identical swap in blades68-lora's own pipeline."""
    description_path = sheet_path + ".description.txt"
    with open(description_path, "w", encoding="utf-8") as f:
        f.write(entry["prompt"])
    return description_path


def ffprobe_duration(video_path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def detect_cut_times(video_path):
    result = subprocess.run(
        ["ffmpeg", "-i", video_path, "-vf", "scdet=t=0", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    candidates = []
    for line in result.stderr.splitlines():
        m = re.search(r"lavfi\.scd\.score:\s*([\d.]+),\s*lavfi\.scd\.time:\s*([\d.]+)", line)
        if m:
            score, t = float(m.group(1)), float(m.group(2))
            if score > CUT_SCORE_FLOOR:
                candidates.append((t, score))
    candidates.sort()
    return candidates


def segment_boundaries(video_path, duration):
    candidates = detect_cut_times(video_path)
    need = N_SHOTS - 1
    if len(candidates) >= need:
        cuts = [t for t, _ in candidates[-need:]]
        source = "scdet"
    else:
        cuts = [duration * i / N_SHOTS for i in range(1, N_SHOTS)]
        source = "even-fallback"
    return [0.0] + cuts + [duration], source, candidates


def extract_stills(entry, video_dir, stills_dir):
    slug = entry["slug"]
    video_path = os.path.join(video_dir, f"{slug}.mp4")
    duration = ffprobe_duration(video_path)
    bounds, source, candidates = segment_boundaries(video_path, duration)
    print(f"[{slug}] duration={duration:.3f}s cut-detect={source} "
          f"candidates={[round(t, 3) for t, s in candidates]} bounds={[round(b, 3) for b in bounds]}")

    still_paths = []
    for i in range(N_SHOTS):
        mid = (bounds[i] + bounds[i + 1]) / 2
        out_path = os.path.join(stills_dir, f"{slug}_{i}_{SHOT_LABELS[i].lower()}.jpg")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{mid:.3f}", "-i", video_path, "-vframes", "1", out_path],
            check=True, capture_output=True,
        )
        still_paths.append(out_path)
    return still_paths


def compose_sheet(entry, still_paths, sheets_dir):
    slug = entry["slug"]
    out_path = os.path.join(sheets_dir, f"{slug}_charref.png")
    labeled = []
    for path, label in zip(still_paths, SHOT_LABELS):
        cap_path = path.replace(".jpg", "_cap.jpg")
        subprocess.run(
            ["convert", path, "-gravity", "South", "-background", "#0d3b3b",
             "-fill", "white", "-font", os.environ.get("T2VA_LABEL_FONT", DEFAULT_FONT),
             "-pointsize", "22", "-splice", "0x30",
             "-annotate", "+0+4", label, cap_path],
            check=True, capture_output=True,
        )
        labeled.append(cap_path)
    subprocess.run(
        ["montage"] + labeled + [
            "-font", os.environ.get("T2VA_LABEL_FONT", DEFAULT_FONT),
            "-tile", "2x2", "-geometry", "+6+6", "-background", "#0d3b3b",
            out_path,
        ],
        check=True, capture_output=True,
    )
    description_path = write_description_sidecar(entry, out_path)
    print(f"[{slug}] wrote {out_path} (+ {os.path.basename(description_path)})")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--slug")
    ap.add_argument("--manifest", default="gen/manifest.json")
    ap.add_argument("--video-dir", default="raw-videos")
    ap.add_argument("--stills-dir", default="/tmp/t2va-stills")
    ap.add_argument("--sheets-dir", default="sheets")
    args = ap.parse_args()

    os.makedirs(args.stills_dir, exist_ok=True)
    os.makedirs(args.sheets_dir, exist_ok=True)

    with open(args.manifest) as f:
        manifest = json.load(f)

    if args.slug:
        entries = [e for e in manifest if e["slug"] == args.slug]
    elif args.all:
        entries = manifest
    else:
        ap.error("specify --all or --slug")
        return

    for entry in entries:
        stills = extract_stills(entry, args.video_dir, args.stills_dir)
        compose_sheet(entry, stills, args.sheets_dir)


if __name__ == "__main__":
    main()
