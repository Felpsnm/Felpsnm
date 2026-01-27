import argparse
import os
import html
import requests
from datetime import datetime
import hashlib
from pathlib import Path

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

def write_id(out_svg_path: str, line: str):
    # hash baseado no "nome da música" (artist — track)
    h = hashlib.sha1(line.encode("utf-8")).hexdigest()[:12]  # curto e estável
    Path("assets").mkdir(parents=True, exist_ok=True)
    Path("assets/now-playing.id").write_text(h, encoding="utf-8")
    return h

def write_svg(out_path: str, title: str, line: str):
    stamp = datetime.utcnow().strftime("UTC %Y-%m-%d %H:%M")
    svg = SVG_TEMPLATE.format(
        title=html.escape(title),
        line=html.escape(line),
        stamp=html.escape(stamp),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

def main(out_path: str):
    user = os.environ.get("LASTFM_USER", "").strip()
    api_key = os.environ.get("LASTFM_API_KEY", "").strip()
    if not user or not api_key:
        write_svg(out_path, "Now playing", "Missing LASTFM_USER / LASTFM_API_KEY")
        raise SystemExit("Missing LASTFM_USER or LASTFM_API_KEY env vars.")

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": user,
        "api_key": api_key,
        "format": "json",
        "limit": 1
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        write_svg(out_path, "Now playing", f"Last.fm request failed")
        raise

    # Last.fm error payloads sometimes include { "error": ..., "message": ... }
    if isinstance(data, dict) and "error" in data:
        msg = data.get("message", "Last.fm API error")
        write_svg(out_path, "Now playing", f"{msg}")
        raise SystemExit(f"Last.fm API error: {msg}")

    recent = (data.get("recenttracks") or {}).get("track")

    # track can be [] or a dict if only one item (API quirk)
    if recent is None:
        write_svg(out_path, "Now playing", "No data from Last.fm")
        return

    if isinstance(recent, list):
        if len(recent) == 0:
            write_svg(out_path, "Now playing", "No recent tracks yet")
            return
        track = recent[0]
    elif isinstance(recent, dict):
        track = recent
    else:
        write_svg(out_path, "Now playing", "Unexpected Last.fm response")
        return

    artist = ((track.get("artist") or {}).get("#text")) or "Unknown artist"
    name = track.get("name") or "Unknown track"
    now = (track.get("@attr") or {}).get("nowplaying") == "true"

    title = "Now playing" if now else "Last played"
    line = f"{artist} — {name}"

    write_id(out_path, line)

    write_svg(out_path, title, line)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/now-playing.svg")
    args = ap.parse_args()
    main(args.out)
    print(f"Saved: {args.out}")
