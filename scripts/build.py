#!/usr/bin/env python3
"""Build the entirely static Decay knowledgebase from authored and Sindri data."""

from __future__ import annotations

import argparse, html, json, re, shutil, subprocess
from pathlib import Path
from urllib.parse import quote

import markdown

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://decay.vardir.no"


def esc(value: object) -> str:
    return html.escape(str(value))


def slug(value: str) -> str:
    return quote(value, safe="-._~")


def inline(text: str) -> str:
    """Escape upstream prose, rendering its `code` spans."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(text))


def signature(item: dict, owner: str | None = None) -> str:
    name = f"{owner}.{item['name']}" if owner else item["name"]
    if item["kind"] == "function":
        types = item.get("parameters", [])
        names = item.get("parameter_names") or []
        params = ", ".join(
            f"{names[i]}: {ty}" if i < len(names) else ty for i, ty in enumerate(types)
        )
        return f"{name}({params}) -> {item.get('returns', 'unit')}"
    return f"{name}: {item.get('type', 'unknown')}"


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing front matter")
    raw, body = text[4:].split("\n---\n", 1)
    meta = {}
    for line in raw.splitlines():
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def page(
    title: str,
    body: str,
    route: str,
    sha: str,
    description: str = "Decay documentation",
) -> str:
    canonical = f"{SITE}{route}"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Decay</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="/assets/site.css"></head><body><header><a class="brand" href="/">Decay</a><nav aria-label="Primary"><a href="/learn/">Learn</a><a href="/cookbook/">Cookbook</a><a href="/concepts/">Concepts</a><a href="/reference/api/">API</a><button id="searchTrigger" type="button">Search <kbd>/</kbd></button></nav></header><main>{body}</main><footer>Generated from Sindri <code>{esc(sha[:12])}</code> · <a href="https://github.com/vardirhq/sindri-engine/commit/{esc(sha)}">source</a></footer><dialog id="searchDialog"><form method="dialog"><button aria-label="Close">×</button></form><label for="searchInput">Search Decay documentation</label><input id="searchInput" autocomplete="off"><div id="searchResults"></div></dialog><script src="/assets/site.js"></script></body></html>"""


def write(out: Path, route: str, data: str) -> None:
    target = out / route.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=ROOT / "_site")
    args = ap.parse_args()
    engine = args.engine_dir.resolve()
    source = engine / "docs/generated/decay-api.json"
    api = json.loads(source.read_text())
    if api.get("schema_version") != 1:
        raise SystemExit(f"unsupported API schema {api.get('schema_version')}")
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=engine, text=True
    ).strip()
    out = args.output.resolve()
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", out / "assets")
    shutil.copy(ROOT / "CNAME", out / "CNAME")
    (out / ".nojekyll").touch()
    search = []
    routes = ["/"]

    def add(title, kind, text, href, aliases=""):
        search.append(
            {
                "title": title,
                "kind": kind,
                "text": text,
                "href": href,
                "aliases": aliases,
            }
        )

    types = {t["name"]: t for t in api["types"]}

    def describe(item: dict) -> str:
        """The upstream description, when the engine provides one."""
        text = item.get("description")
        return f'<p class="lead">{inline(text)}</p>' if text else ""

    def provenance(api: dict, sha: str) -> str:
        """Engine version and a short, linked commit that cannot overflow."""
        return (
            f'<dt>Engine version</dt><dd>{esc(api["engine_version"])}</dd>'
            f'<dt>Source commit</dt><dd><a href="https://github.com/vardirhq/sindri-engine/commit/{esc(sha)}" title="{esc(sha)}"><code>{esc(sha[:12])}</code></a></dd>'
        )
    cards = []
    for item in api["globals"]:
        route = f"/reference/api/globals/{slug(item['name'])}/"
        sig = signature(item)
        body = f'<p class="eyebrow">Global {esc(item["kind"])}</p><h1>{esc(item["name"])}</h1>{describe(item)}<pre><code>{esc(sig)}</code></pre><dl>{provenance(api, sha)}</dl>'
        write(out, route, page(item["name"], body, route, sha, item.get("description") or "Decay documentation"))
        routes.append(route)
        add(item["name"], f"Global {item['kind']}", " ".join(filter(None, [sig, item.get("description")])), route)
    for owner, members in [(t["name"], t["members"]) for t in api["types"]] + [
        ("this", api["this"])
    ]:
        owner_route = f"/reference/api/{slug(owner)}/"
        links = []
        for item in members:
            route = owner_route + slug(item["name"]) + "/"
            sig = signature(item, owner)
            related = []
            for typ in item.get("parameters", []) + [
                item.get("returns"),
                item.get("type"),
            ]:
                if typ in types:
                    related.append(
                        f'<a href="/reference/api/{slug(typ)}/">{esc(typ)}</a>'
                    )
            body = (
                f'<p class="eyebrow">{esc(owner)} · {esc(item["kind"])}</p><h1>{esc(owner)}.<wbr>{esc(item["name"])}</h1>{describe(item)}<pre><code>{esc(sig)}</code></pre><dl><dt>Owner</dt><dd><a href="{owner_route}">{esc(owner)}</a></dd>{provenance(api, sha)}</dl>'
                + (
                    f'<h2>Related types</h2><p>{" · ".join(related)}</p>'
                    if related
                    else ""
                )
            )
            write(
                out,
                route,
                page(
                    f"{owner}.{item['name']}",
                    body,
                    route,
                    sha,
                    item.get("description") or "Decay documentation",
                ),
            )
            routes.append(route)
            summary = (
                f'<span class="summary">{inline(item["description"])}</span>'
                if item.get("description")
                else ""
            )
            links.append(
                f'<li><a href="{route}"><code>{esc(sig)}</code></a>{summary}</li>'
            )
            add(f"{owner}.{item['name']}", item["kind"], " ".join(filter(None, [sig, item.get("description")])), route)
        kind = "this members" if owner == "this" else "Host type"
        owner_text = (
            "What a script can reach on the object it is attached to, beyond its own fields."
            if owner == "this"
            else types.get(owner, {}).get("description")
        )
        body = f'<p class="eyebrow">{kind}</p><h1>{esc(owner)}</h1>{describe({"description": owner_text})}<p>{len(members)} exported members in engine {esc(api["engine_version"])}.</p><ul class="symbol-list">{"".join(links)}</ul>'
        generated_aliases = {
            "Input": "controller gamepad input",
            "Gamepad": "controller input",
            "World": "spawn object spawning",
            "Time": "delta time dt update",
        }
        write(
            out,
            owner_route,
            page(owner, body, owner_route, sha, owner_text or "Decay documentation"),
        )
        routes.append(owner_route)
        add(
            owner,
            kind,
            " ".join(m["name"] for m in members),
            owner_route,
            generated_aliases.get(owner, ""),
        )
        cards.append(
            f'<li><a href="{owner_route}">{esc(owner)}</a> <span>{len(members)} members</span></li>'
        )
    api_route = "/reference/api/"
    globals_links = "".join(
        f'<li><a href="/reference/api/globals/{slug(x["name"])}/">{esc(signature(x))}</a></li>'
        for x in api["globals"]
    )
    body = f'<p class="eyebrow">Generated reference</p><h1>Sindri Decay API</h1><p>Executable truth from engine <strong>{esc(api["engine_version"])}</strong> at <a href="https://github.com/vardirhq/sindri-engine/commit/{esc(sha)}" title="{esc(sha)}"><code>{esc(sha[:12])}</code></a>. This index is generated; do not edit signatures here.</p><h2>Host types and namespaces</h2><ul class="symbol-list">{"".join(cards)}</ul><h2>Globals</h2><ul class="symbol-list">{globals_links}</ul>'
    write(out, api_route, page("Sindri API", body, api_route, sha))
    routes.append(api_route)
    add("Sindri API", "Reference", "host namespaces types globals functions", api_route)
    section_pages = {}
    language_source = engine / "decay/LANGUAGE.md"
    if not language_source.is_file():
        raise SystemExit(f"missing authoritative language reference: {language_source}")
    language_markdown = language_source.read_text()
    language_route = "/reference/language/"
    language_body = (
        '<p class="eyebrow">Generated from the authoritative engine document</p>'
        + markdown.markdown(language_markdown, extensions=["fenced_code", "tables"])
    )
    write(
        out,
        language_route,
        page("Decay language reference", language_body, language_route, sha),
    )
    routes.append(language_route)
    add(
        "Decay language reference",
        "Language reference",
        re.sub(r"\W+", " ", language_markdown),
        language_route,
        "syntax keywords types operators vectors lists text events state collections timers",
    )
    language_target = out / "reference/language/source.md"
    language_target.write_text(language_markdown)

    for path in sorted((ROOT / "content").glob("*/*.md")):
        if path.name == "README.md":
            continue
        meta, md = frontmatter(path)
        section = path.parent.name
        route = f"/{section}/" if path.stem == "index" else f"/{section}/{path.stem}/"
        rendered = markdown.markdown(md, extensions=["fenced_code"])
        write(
            out, route, page(meta["title"], rendered, route, sha, meta["description"])
        )
        routes.append(route)
        add(
            meta["title"],
            section.title(),
            re.sub(r"\W+", " ", md),
            route,
            meta.get("aliases", ""),
        )
        if path.stem != "index":
            section_pages.setdefault(section, []).append(
                (meta["title"], route, meta["description"])
            )
    for section, items in section_pages.items():
        route = f"/{section}/"
        body = (
            f'<h1>{esc(section.title())}</h1><ul class="cards">'
            + "".join(
                f'<li><a href="{r}"><strong>{esc(t)}</strong><span>{esc(d)}</span></a></li>'
                for t, r, d in items
            )
            + "</ul>"
        )
        write(out, route, page(section.title(), body, route, sha))
        routes.append(route)
    home = '<section class="hero"><p class="eyebrow">The gameplay language for Sindri</p><h1>Learn Decay from executable truth.</h1><p>Handwritten teaching, automatically checked against the same engine metadata and compiler that run your game.</p><p><a class="button" href="/learn/first-script/">Write your first script</a> <a href="/reference/api/">Browse the API</a></p></section>'
    write(out, "/", page("Language and API documentation", home, "/", sha))
    notfound = '<h1>Page not found</h1><p>The documentation may have moved. <a href="/">Return home</a> or use search.</p>'
    (out / "404.html").write_text(page("Not found", notfound, "/404.html", sha))
    (out / "search-index.json").write_text(
        json.dumps(
            {"schema_version": 1, "engine_commit": sha, "entries": search}, indent=2
        )
    )
    (out / "build-metadata.json").write_text(
        json.dumps(
            {
                "engine_commit": sha,
                "engine_version": api["engine_version"],
                "api_schema": api["schema_version"],
            },
            indent=2,
        )
    )
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{r}</loc></url>" for r in routes)
        + "</urlset>"
    )
    print(f"built {len(routes)} routes and {len(search)} search entries from {sha}")


if __name__ == "__main__":
    main()
