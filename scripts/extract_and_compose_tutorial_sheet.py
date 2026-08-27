#!/usr/bin/env python3
"""
Frame extraction + composition for the h3-drawing-tutorial-sheet experiment:
turns one continuous "blank canvas -> final image" H3 construction video
into a single 4x2 progressive-build-up still (8 stages, doubled from the
first validation's 4 per Gavin's feedback for finer-grained progression).

Unlike extract_and_compose.py (T2VA's charref-sheet script), this does NOT
use ffmpeg scdet cut detection -- that script's discrete 4-shot clips have
real hard cuts between shots; this experiment's video is one continuous
morph with no cuts, so cut detection would find nothing (or noise) and
even-spaced timestamps across the duration are the correct sampling
strategy. Same montage/labeling mechanics reused otherwise.

Usage:
    python3 extract_and_compose_tutorial_sheet.py --slug raven \
        --video raw-videos/raven_tutorial.mp4 --stills-dir /tmp/stills \
        --out sheets/raven_tutorial_sheet.png
"""
import argparse
import os
import subprocess

STAGE_LABELS = [
    "Blank Canvas", "Basic Forms", "Rough Structure", "Detail Pass",
    "Line Refinement", "Base Color", "Rendering", "Final Render",
]
N_STAGES = 8
DEFAULT_FONT = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"


def ffprobe_duration(video_path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def extract_stills(slug, video_path, stills_dir):
    duration = ffprobe_duration(video_path)
    # Sample at the midpoint of each of N_STAGES even segments -- stage 0's
    # midpoint (duration/8) is close enough to t=0 to still read as "early
    # canvas" while avoiding a literal first-frame that some codecs pad.
    timestamps = [duration * (i + 0.5) / N_STAGES for i in range(N_STAGES)]
    print(f"[{slug}] duration={duration:.3f}s timestamps={[round(t, 3) for t in timestamps]}")

    still_paths = []
    for i, ts in enumerate(timestamps):
        out_path = os.path.join(stills_dir, f"{slug}_{i}_{STAGE_LABELS[i].lower().replace(' ', '_').replace('&', 'and')}.jpg")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{ts:.3f}", "-i", video_path, "-vframes", "1", out_path],
            check=True, capture_output=True,
        )
        still_paths.append(out_path)
    return still_paths


def compose_sheet(slug, still_paths, out_path):
    labeled = []
    for path, label in zip(still_paths, STAGE_LABELS):
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
            "-tile", "4x2", "-geometry", "+6+6", "-background", "#0d3b3b",
            out_path,
        ],
        check=True, capture_output=True,
    )
    print(f"[{slug}] wrote {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--stills-dir", default="/tmp/t2va-tutorial-stills")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    os.makedirs(args.stills_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    stills = extract_stills(args.slug, args.video, args.stills_dir)
    compose_sheet(args.slug, stills, args.out)


if __name__ == "__main__":
    main()
