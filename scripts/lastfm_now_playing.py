import argparse
import os
import html
import requests
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import glob

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

def svg_text(title: str, line: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("UTC %Y-%m-%d %H:%M")
    return SVG_TEMPLATE.format(
        title=html.escape(title),
        line=html.escape(line),
        stamp=html.escape(stamp),
    )

def fetch_lastfm() -> tuple[str, str]:
    user = os.environ.get("LASTFM_USER", "").strip()
    api_key = os.environ.get("LASTFM_API_KEY", "").strip()
    if not user or not api_key:
        return ("Now playing", "Missing LASTFM_USER / LASTFM_API_KEY")

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getrecenttracks",
        "user": user,
        "api_key": api_key,
        "format": "json",
        "limit": 1
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    if isinstance(data, dict) and "error" in data:
        return ("Now playing", data.get("message", "Last.fm API error"))

    recent = (data.get("recenttracks") or {}).get("track")
    if isinstance(recent, list) and len(recent) == 0:
        return ("Now playing", "No recent tracks yet")
    if recent is None:
        return ("Now playing", "No data from Last.fm")

    track = recent[0] if isinstance(recent, list) else recent
    artist = ((track.get("artist") or {}).get("#text")) or "Unknown artist"
    name = track.get("name") or "Unknown track"
    now = (track.get("@attr") or {}).get("nowplaying") == "true"

    title = "Now playing" if now else "Last played"
    line = f"{artist} — {name}"
    return (title, line)

def make_id(title: str, line: str) -> str:
    # muda quando mudar música OU status (Now/Last)
    base = f"{title}|{line}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]

def cleanup_old_svgs(keep: int = 6):
    files = sorted(glob.glob("assets/now-playing-*.svg"))
    if len(files) <= keep:
        return
    for f in files[:-keep]:
        Path(f).unlink(missing_ok=True)

def main():
    Path("assets").mkdir(parents=True, exist_ok=True)

    title, line = fetch_lastfm()
    hid = make_id(title, line)

    out_file = Path(f"assets/now-playing-{hid}.svg")
    out_file.write_text(svg_text(title, line), encoding="utf-8")

    # salva o id pra workflow usar se quiser
    Path("assets/now-playing.id").write_text(hid, encoding="utf-8")
    Path("assets/now-playing.latest").write_text(out_file.name, encoding="utf-8")

    cleanup_old_svgs(keep=6)

    print("id:", hid)
    print("file:", out_file.as_posix())

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.parse_args()
    main()