#!/usr/bin/env python3
"""Check generated metadata and internal static links."""

import json, re, sys
from pathlib import Path
from urllib.parse import unquote

root = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
required = [
    "CNAME",
    "404.html",
    "sitemap.xml",
    "search-index.json",
    "build-metadata.json",
    "reference/language/index.html",
    "reference/language/source.md",
    "reference/api/Input/index.html",
    "reference/api/Input/axis/index.html",
    "reference/api/World/index.html",
    "reference/api/Audio/index.html",
    "reference/api/globals/abs/index.html",
    "reference/api/this/transform/index.html",
    "learn/first-script/index.html",
    "diagnostics/index.html",
    "make-a-game/index.html",
]
missing = [x for x in required if not (root / x).is_file()]
for html in root.rglob("*.html"):
    for href in re.findall(r'href="(/[^"]*)"', html.read_text()):
        path = unquote(href.split("#")[0].split("?")[0])
        if not path or path.startswith("//"):
            continue
        target = root / path.lstrip("/")
        if not target.is_file() and not (target / "index.html").is_file():
            missing.append(f"{html.relative_to(root)} -> {path}")
index = json.loads((root / "search-index.json").read_text())
metadata = json.loads((root / "build-metadata.json").read_text())
if index["engine_commit"] != metadata["engine_commit"]:
    missing.append("search engine SHA mismatch")
haystack = " ".join(json.dumps(x).lower() for x in index["entries"])
for query in [
    "input.axis",
    "world",
    "audio",
    "abs",
    "this.transform",
    "your first decay script",
    "global variable",
    "controller",
    "broadcast",
    "delta time",
    "spawn",
    "language reference",
    "keywords",
    "operators",
]:
    if query not in haystack:
        missing.append(f"search term: {query}")
if (root / "CNAME").read_text().strip() != "decay.vardir.no":
    missing.append("CNAME")
if missing:
    print("Missing or invalid:\n" + "\n".join(missing))
    raise SystemExit(1)
print(
    f"checked {sum(1 for _ in root.rglob('*.html'))} HTML pages and {len(index['entries'])} search entries"
)
