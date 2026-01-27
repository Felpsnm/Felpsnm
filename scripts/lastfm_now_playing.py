import os
import re
import html
import requests
from datetime import datetime, timezone

START = "<!-- NOW_PLAYING:START -->"
END = "<!-- NOW_PLAYING:END -->"

def fetch_lastfm_now():
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

def build_svg(title: str, line: str):
    title_e = html.escape(title)
    line_e = html.escape(line)
    stamp = datetime.now(timezone.utc).strftime("UTC %Y-%m-%d %H:%M")

    return f"""{START}
      <svg xmlns="http://www.w3.org/2000/svg" width="720" height="90" viewBox="0 0 720 90">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#0b0f14"/>
            <stop offset="100%" stop-color="#111827"/>
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="720" height="90" rx="18" fill="url(#g)" />
        <text x="26" y="34" fill="#cbd5e1" font-size="14" font-family="monospace">{title_e}</text>
        <text x="26" y="62" fill="#e5e7eb" font-size="18" font-family="monospace">{line_e}</text>
        <text x="690" y="78" fill="#64748b" font-size="10" font-family="monospace" text-anchor="end">{stamp}</text>
      </svg>
      {END}
      """

def patch_readme(path="README.md"):
    title, line = fetch_lastfm_now()
    block = build_svg(title, line)

    s = open(path, "r", encoding="utf-8").read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(s):
        raise SystemExit("NOW_PLAYING block not found in README.md")

    s2 = pattern.sub(block.strip(), s)
    open(path, "w", encoding="utf-8").write(s2)

if __name__ == "__main__":
    patch_readme()
    print("README updated (inline SVG).")