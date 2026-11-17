"""Check inline media, HTML asset references, and script syntax in a standalone YDS file."""
import argparse
import base64
from collections import Counter
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

from lxml import html
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("book", type=Path)
parser.add_argument("--all-audio", action="store_true", help="Decode every unique track. Otherwise select 24 spread across the book.")
args = parser.parse_args()
raw = args.book.read_bytes()
matches = list(re.finditer(rb'data:((?:image|audio)/[-\w.+]+);base64,([\w+/=]+)', raw))
counts = Counter(m[1].decode() for m in matches)
unique = {}
errors = []
for match in matches:
    medium = match[1].decode()
    media = base64.b64decode(match[2], validate=True)
    unique[(medium, hashlib.sha256(media).hexdigest())] = media

audios = [(key, media) for key, media in unique.items() if key[0].startswith("audio/")]
images = [(key, media) for key, media in unique.items() if key[0].startswith("image/")]


def decode_audio(item):
    key, data = item
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", "pipe:", "-f", "s16le", "pipe:"],
        input=data, capture_output=True, check=False,
    )
    if result.returncode or not result.stdout:
        return f"{key}: {result.stderr.decode(errors='replace') or 'empty PCM output'}"

for key, data in images:
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            if not all(image.size):
                raise ValueError("empty dimensions")
    except Exception as error:
        errors.append(f"{key}: {error}")

chosen = audios
if not args.all_audio and len(audios) > 24:
    chosen = [audios[round(i * (len(audios) - 1) / 23)] for i in range(24)]
with ThreadPoolExecutor(max_workers=4) as pool:
    errors.extend(error for error in pool.map(decode_audio, chosen) if error)

stripped = re.sub(rb'(data:(?:image|audio)/[-\w.+]+;base64,)[\w+/=]+', rb'\1PLACEHOLDER', raw)
root = html.fromstring(stripped)
attrs = ["src", "srcset", "poster", "data", "href"]
resource_tags = {"img", "audio", "video", "source", "script", "track", "iframe", "embed", "object", "image", "link"}
resources = []
for item in root.iter():
    if item.tag not in resource_tags:
        continue
    for name in attrs:
        value = item.get(name)
        if value and not value.startswith(("data:", "#")):
            resources.append((item.tag, name, value[:180]))

for style in root.xpath("//style"):
    for match in re.finditer(r'url\(\s*["\']?([^"\')]+)', style.text or ""):
        value = match[1].strip()
        if not value.startswith(("data:", "#")):
            resources.append(("style", "url", value[:180]))
ids = Counter(element.get("id") for element in root.xpath("//*[@id]"))
duplicate_ids = sorted(key for key, count in ids.items() if count > 1)
anchor_targets = [unquote(item.get("href")[1:]) for item in root.xpath('//a[starts-with(@href, "#")]')]
missing_anchors = sorted({target for target in anchor_targets if target and target not in ids})
if duplicate_ids:
    errors.append(f"Duplicate DOM IDs: {duplicate_ids}")
if missing_anchors:
    errors.append(f"Missing internal anchor targets: {missing_anchors}")
if resources:
    errors.append(f"Potential non-inline resources: {resources}")
scripts = list(root.xpath("//script"))
for number, script in enumerate(scripts, 1):
    if script.get("type", "") not in {"", "text/javascript", "module", "application/javascript"}:
        continue
    result = subprocess.run(["node", "--check"], input=(script.text or "").encode(), capture_output=True)
    if result.returncode:
        errors.append(f"Script {number}: {result.stderr.decode(errors='replace')[:500]}")

print(json.dumps({
    "book": str(args.book),
    "inline_references": counts,
    "unique_images_decoded": len(images),
    "unique_audio_total": len(audios),
    "unique_audio_decoded": len(chosen),
    "scripts": len(scripts),
    "internal_anchor_references_checked": len(anchor_targets),
    "errors": errors,
}, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
