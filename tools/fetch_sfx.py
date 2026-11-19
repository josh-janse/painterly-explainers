#!/usr/bin/env python3
"""Download the HQ preview mp3 of every sound in assets/sfx/manifest.json into assets/sfx/raw/<id>.mp3.

Run from the repo root:  python3 tools/fetch_sfx.py [--force]
Method: fetch https://freesound.org/s/<id>/ (redirects followed), take the preview URL from the bw-player's
data-mp3 attribute (or any cdn.freesound.org preview URL on the page), swap -lq.mp3 for -hq.mp3 and download it.
"""
import json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAN = os.path.join(ROOT, "assets", "sfx", "manifest.json")
UA = {"User-Agent": "Mozilla/5.0 (painterly-explainers sfx fetch)"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

def preview_url(sid):
    html = get(f"https://freesound.org/s/{sid}/").decode("utf-8", "replace")
    m = re.search(r'data-mp3="([^"]+)"', html) or re.search(r'(https://cdn\.freesound\.org/previews/[^"\']+-[lh]q\.mp3)', html)
    if not m:
        raise RuntimeError("no preview URL on page")
    return m.group(1).replace("-lq.mp3", "-hq.mp3")

def main():
    force = "--force" in sys.argv
    man = json.load(open(MAN))
    failed = []
    for name, s in man["sounds"].items():
        path = os.path.join(ROOT, s["file"])
        if os.path.exists(path) and not force:
            print(f"have  {name:12s} {s['id']}"); continue
        try:
            data = get(preview_url(s["id"]))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").write(data)
            print(f"got   {name:12s} {s['id']}  {len(data) // 1024} KB")
        except Exception as e:
            failed.append(name); print(f"FAIL  {name:12s} {s['id']}  {e}")
        time.sleep(1)
    if failed:
        sys.exit(f"{len(failed)} failed: {', '.join(failed)}")

if __name__ == "__main__":
    main()
