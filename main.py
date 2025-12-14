#!/usr/bin/env python3
"""
YT Streams - Wrapper Playlist Generator

Bu script youtube/googlevideo signed m3u8'leri repoya yazmaz.
Bunun yerine repo içine endpoint'e işaret eden "wrapper" m3u8 yazar.

- turkish.json içindeki type=channel/video destekler
- subfolder varsa TR/<subfolder>/<slug>.m3u8 oluşturur
- ENDPOINT1..ENDPOINT10 (veya ENDPOINT) fallback listesi ile
  tek dosyada birden çok endpoint verir (player sırayla dener).

Not: Endpoint'in /yt.php?c=... veya /yt.php?v=... çağrısına m3u8 döndürmesi gerekir.
"""

import os
import sys
import json
import argparse
from pathlib import Path

DEFAULT_ENDPOINT = os.environ.get("ENDPOINT")
ENDPOINTS = [os.environ.get(f"ENDPOINT{i}") for i in range(1, 11) if os.environ.get(f"ENDPOINT{i}")]
if not ENDPOINTS:
    ENDPOINTS = [DEFAULT_ENDPOINT] if DEFAULT_ENDPOINT else []

FOLDER_NAME = os.environ.get("FOLDER_NAME", "TR")


def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_output_path(stream: dict, folder: str) -> Path:
    subfolder = stream.get("subfolder", "").strip()
    slug = stream["slug"].strip()
    base = Path(folder)
    if subfolder:
        base = base / subfolder
    return base / f"{slug}.m3u8"


def build_endpoint_url(endpoint: str, stream: dict) -> str:
    endpoint = endpoint.rstrip("/")
    stream_type = stream.get("type", "channel")
    stream_id = stream["id"]

    if stream_type == "video":
        return f"{endpoint}/yt.php?v={stream_id}"
    elif stream_type == "channel":
        return f"{endpoint}/yt.php?c={stream_id}"
    else:
        raise ValueError(f"Unknown type: {stream_type}")


def make_wrapper_m3u8(endpoints: list[str], stream: dict) -> str:
    """
    Birden fazla endpoint varsa, hepsini ayrı variant olarak yazar.
    Çoğu player ilkini dener; ilk variant patlarsa sonraki satıra geçebilen playerlar da var.
    (Tam garanti değil, ama pratikte iş görür.)
    """
    lines = ["#EXTM3U"]
    # endpoint sayısına göre artan bandwidth verelim
    bw_start = 8_000_000
    bw_step = 200_000

    for idx, ep in enumerate([e for e in endpoints if e], start=0):
        url = build_endpoint_url(ep, stream)
        bw = bw_start - (idx * bw_step)
        # Basit variant satırı (resolution/frame-rate sabit)
        lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION=1920x1080,FRAME-RATE=30")
        lines.append(url)

    # Hiç endpoint yoksa boş dönmeyelim, hata verelim
    if len(lines) == 1:
        raise RuntimeError("No endpoints configured. Set ENDPOINT or ENDPOINT1..ENDPOINT10 secrets.")

    return "\n".join(lines) + "\n"


def save_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("config_files", nargs="+", help="JSON config file(s)")
    p.add_argument("--folder", default=FOLDER_NAME, help=f"Output folder (default: {FOLDER_NAME})")
    p.add_argument("--endpoint", default=(ENDPOINTS[0] if ENDPOINTS else DEFAULT_ENDPOINT),
                   help="Primary endpoint (overrides first endpoint)")
    return p.parse_args()


def main():
    global ENDPOINTS

    args = parse_args()

    # Primary endpoint override
    primary = (args.endpoint or "").strip()
    if not primary:
        print("ERROR: endpoint not set. Provide --endpoint or set ENDPOINT/ENDPOINT1..10")
        sys.exit(1)

    if ENDPOINTS:
        ENDPOINTS[0] = primary
    else:
        ENDPOINTS = [primary]

    total = 0
    for cfg in args.config_files:
        streams = load_config(cfg)
        print(f"Config: {cfg} ({len(streams)} streams)")
        for s in streams:
            out_path = get_output_path(s, args.folder)
            wrapper = make_wrapper_m3u8(ENDPOINTS, s)
            save_text(out_path, wrapper)
            total += 1
            print(f"  ✓ {out_path}")

    print(f"Done. Wrote {total} wrapper playlist(s) into '{args.folder}'.")


if __name__ == "__main__":
    main()
