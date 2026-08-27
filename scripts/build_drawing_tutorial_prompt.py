#!/usr/bin/env python3
"""Emit the MiniMax H3 API-format prompt JSON for the drawing-tutorial-sheet
experiment (feature/h3-drawing-tutorial-sheet).

Ported node-loader boilerplate (VAE/UNET/CLIP/turbo-LoRA/sampler chain)
from build_t2va_prompt.py. Differs at the conditioning node: swaps
MiniMaxH3ReferenceToVideo (T2VA, no image, +audio) for
MiniMaxH3ImageToVideo (first_frame/last_frame IMAGE inputs, video-only --
no audio_vae/VAEDecodeAudio branch). first_frame/last_frame must already
be present in ComfyUI's input directory (the calling task uploads them via
POST /upload/image before submitting this graph) -- see EXPERIMENT.md for
why last_frame is a real prior T2VA render standing in for "finished
reference artwork" (no Esoteria roster asset has decodable source pixel
art yet, per data/raw_texture_status.md).

Usage:
    python3 build_drawing_tutorial_prompt.py --prompt "..." --seed 900000 \
        --first-frame blank_canvas.png --last-frame raven_reference_still.png \
        --output-prefix t2va-tutorial/raven --client-id t2va-tutorial-raven \
        > /tmp/prompt.json
"""
import argparse
import json

WIDTH = 480
HEIGHT = 864
LENGTH_FRAMES = 124  # ~5.17s @ 24fps, snapped to the model's 17k+5 grid
STEPS = 8


def build_api_prompt(prompt_text, seed, first_frame, last_frame, output_prefix):
    return {
        "119": {"inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}, "class_type": "VAELoader"},
        "127": {
            "inputs": {
                "unet_name": "MinimaxH3/minimax_h3_ref2va_pruned_int8_convrot.safetensors",
                "weight_dtype": "default",
            },
            "class_type": "UNETLoader",
        },
        "128": {
            "inputs": {
                "clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
                "type": "minimax",
                "device": "default",
            },
            "class_type": "CLIPLoader",
        },
        "596": {
            "inputs": {"sage_attention": "auto", "allow_compile": False, "model": ["127", 0]},
            "class_type": "PathchSageAttentionKJ",
        },
        "800": {
            "inputs": {
                "lora_name": "minimax_h3_turbo_v4_step600_ema.safetensors",
                "strength": 1,
                "low_vram": True,
                "model": ["596", 0],
            },
            "class_type": "MiniMaxH3TurboLoRA",
        },
        "801": {"inputs": {}, "class_type": "MiniMaxH3TurboSampler"},
        "129": {"inputs": {"noise_seed": seed}, "class_type": "RandomNoise"},
        "124": {
            "inputs": {"scheduler": "simple", "steps": STEPS, "denoise": 1, "model": ["800", 0]},
            "class_type": "BasicScheduler",
        },
        "126": {
            "inputs": {"model": ["800", 0], "conditioning": ["136", 0]},
            "class_type": "BasicGuider",
        },
        "125": {
            "inputs": {
                "noise": ["129", 0],
                "guider": ["126", 0],
                "sampler": ["801", 0],
                "sigmas": ["124", 0],
                "latent_image": ["136", 1],
            },
            "class_type": "SamplerCustomAdvanced",
        },
        "900": {"inputs": {"image": first_frame}, "class_type": "LoadImage"},
        "901": {"inputs": {"image": last_frame}, "class_type": "LoadImage"},
        "136": {
            "inputs": {
                "clip": ["128", 0],
                "vae": ["119", 0],
                "prompt": prompt_text,
                "width": WIDTH,
                "height": HEIGHT,
                "length": LENGTH_FRAMES,
                "first_frame": ["900", 0],
                "last_frame": ["901", 0],
            },
            "class_type": "MiniMaxH3ImageToVideo",
        },
        "122": {"inputs": {"samples": ["125", 0], "vae": ["119", 0]}, "class_type": "VAEDecode"},
        "605": {
            "inputs": {"fps": 24, "bit_depth": 8, "images": ["122", 0]},
            "class_type": "CreateVideo",
        },
        "612": {
            "inputs": {
                "filename_prefix": output_prefix,
                "format": "auto",
                "codec": "auto",
                "video": ["605", 0],
            },
            "class_type": "SaveVideo",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--first-frame", required=True)
    ap.add_argument("--last-frame", required=True)
    ap.add_argument("--output-prefix", required=True)
    ap.add_argument("--client-id", required=True)
    args = ap.parse_args()

    api_prompt = build_api_prompt(
        args.prompt, args.seed, args.first_frame, args.last_frame, args.output_prefix
    )
    print(json.dumps({"prompt": api_prompt, "client_id": args.client_id}))


if __name__ == "__main__":
    main()
