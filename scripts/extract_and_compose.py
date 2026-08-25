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
from xml.sax.saxutils import escape as xml_escape

SHOT_LABELS = ["Head", "Front", "Back", "Side"]
N_SHOTS = 4
CUT_SCORE_FLOOR = 1.0
DEFAULT_FONT = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"

XMP_TEMPLATE = """<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:description>
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{description}</rdf:li>
        </rdf:Alt>
      </dc:description>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>
"""


def write_xmp_sidecar(entry, sheet_path):
    """Writes a <sheet>.xmp next to the composed reference sheet so
    immich-concourse-resource's out script auto-detects and binds it,
    landing the ComfyUI render prompt in the Immich asset's
    exifInfo.description field (verified live against Immich v3.1.0:
    dc:description in an XMP sidecar is extracted into exifInfo.description
    immediately on upload -- no async lag, unlike sidecarPath linking)."""
    xmp_path = sheet_path + ".xmp"
    xmp = XMP_TEMPLATE.format(description=xml_escape(entry["prompt"]))
    with open(xmp_path, "w", encoding="utf-8") as f:
        f.write(xmp)
    return xmp_path


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
    xmp_path = write_xmp_sidecar(entry, out_path)
    print(f"[{slug}] wrote {out_path} (+ {os.path.basename(xmp_path)})")
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
