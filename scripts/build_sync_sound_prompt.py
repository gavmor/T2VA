#!/usr/bin/env python3
"""Emit the MiniMax H3 T2VA API-format prompt JSON for the H3 Sync Sound
Challenge entry (feature/h3-sync-sound-challenge).

Ported from build_t2va_prompt.py (same node graph, same audio-capable
MiniMaxH3ReferenceToVideo path -- T2VA already generates native, in-sync
audio for every roster render, confirmed via ffprobe on an existing real
render, real stereo AAC content, not silence). The one difference: this
script takes --length as a CLI arg instead of a fixed 107-frame constant,
since the contest entry's shot count (turn -> weapon-raise -> dialogue)
needs more room than T2VA's turnaround-sheet clips do. Length must still
land on H3's native 17k+5 frame grid.

Usage:
    python3 build_sync_sound_prompt.py --prompt "..." --seed 900001 \
        --length 158 --output-prefix t2va-sync-sound/raven_v1 \
        --client-id t2va-sync-sound-raven-v1 > /tmp/prompt.json
"""
import argparse
import json

WIDTH = 480
HEIGHT = 864
STEPS = 8


def build_api_prompt(prompt_text, seed, length_frames, output_prefix):
    return {
        "119": {"inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}, "class_type": "VAELoader"},
        "120": {"inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}, "class_type": "VAELoader"},
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
        "136": {
            "inputs": {
                "clip": ["128", 0],
                "vae": ["119", 0],
                "audio_vae": ["120", 0],
                "prompt": prompt_text,
                "width": WIDTH,
                "height": HEIGHT,
                "length": length_frames,
                "ref_image_size": "match",
            },
            "class_type": "MiniMaxH3ReferenceToVideo",
        },
        "122": {"inputs": {"samples": ["125", 0], "vae": ["119", 0]}, "class_type": "VAEDecode"},
        "121": {"inputs": {"samples": ["125", 0], "vae": ["120", 0]}, "class_type": "VAEDecodeAudio"},
        "605": {
            "inputs": {"fps": 24, "bit_depth": 8, "images": ["122", 0], "audio": ["121", 0]},
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
    ap.add_argument("--length", type=int, required=True)
    ap.add_argument("--output-prefix", required=True)
    ap.add_argument("--client-id", required=True)
    args = ap.parse_args()

    api_prompt = build_api_prompt(args.prompt, args.seed, args.length, args.output_prefix)
    print(json.dumps({"prompt": api_prompt, "client_id": args.client_id}))


if __name__ == "__main__":
    main()
