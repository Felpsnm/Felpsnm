# scripts/lastfm_now_playing.py
import argparse
import os
import html
import requests
from datetime import datetime

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="720" height="90" viewBox="0 0 720 90">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0b0f14"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="720" height="90" rx="18" fill="url(#g)" />
  <text x="26" y="34" fill="#cbd5e1" font-size="14" font-family="monospace">{title}</text>
  <text x="26" y="62" fill="#e5e7eb" font-size="18" font-family="monospace">{line}</text>
  <text x="690" y="78" fill="#64748b" font-size="10" font-family="monospace" text-anchor="end">{stamp}</text>
</svg>
"""

def main(out_path: str):
    user = os.environ.get("LASTFM_USER", "").strip()
    api_key = os.environ.get("LASTFM_API_KEY", "").strip()
    if not user or not api_key:
        raise SystemExit("Missing LASTFM_USER or LASTFM_API_KEY env vars.")

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": user,
        "api_key": api_key,
        "format": "json",
        "limit": 1
    }
    data = requests.get(url, params=params, timeout=15).json()
    track = data["recenttracks"]["track"][0]

    artist = track["artist"]["#text"]
    name = track["name"]
    now = track.get("@attr", {}).get("nowplaying") == "true"

    title = "Now playing" if now else "Last played"
    line = f"{artist} — {name}"

    # escape for SVG
    title = html.escape(title)
    line = html.escape(line)

    stamp = datetime.utcnow().strftime("UTC %Y-%m-%d %H:%M")

    svg = SVG_TEMPLATE.format(title=title, line=line, stamp=stamp)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/now-playing.svg")
    args = ap.parse_args()
    main(args.out)
    print(f"Saved: {args.out}")