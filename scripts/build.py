#!/usr/bin/env python3
"""Build the entirely static Decay knowledgebase from authored and Sindri data."""

from __future__ import annotations

import argparse, html, json, re, shutil, subprocess
from pathlib import Path
from urllib.parse import quote

import markdown

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://decay.vardir.no"
ENGINE_REPO = "https://github.com/vardirhq/sindri-engine"

SECTION_NAMES = {
    "learn": "Learn Decay",
    "make-a-game": "Make a Game",
    "cookbook": "Cookbook",
    "concepts": "Concepts",
    "diagnostics": "Diagnostics",
}

# Lessons that are planned but not yet written, in course order (see
# ROADMAP.md). Remove an entry when its page lands in content/learn/.
PLANNED_LESSONS = [
    ("Values & types", "Values, mutability, primitives and vectors."),
    ("Functions", "Turn behaviour into readable, reusable pieces."),
    ("Control flow", "Branch and loop because the game asks you to."),
    ("Vectors", "Positions, directions and the arithmetic between them."),
    ("Entities & scripts", "Understand where gameplay behaviour lives."),
    ("Typed script communication", "Call one particular script without strings."),
    ("Events", "Announce that something happened to whoever cares."),
    ("Shared state", "Keep data that belongs to the whole game."),
    ("Collections & timers", "Lists of things and things that happen later."),
    ("Putting it together", "Build a small playable system from the pieces."),
]

# The Decay mark: a D whose bowl dissolves. The small cut is for UI sizes.
MARK = '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><rect x="4" y="4" width="10" height="24"/><rect x="15" y="4.5" width="2.2" height="23"/><rect x="18.6" y="5.5" width="1.6" height="21"/><rect x="21.6" y="8" width="1.1" height="16"/></svg>'
MARK_LARGE = (
    '<svg class="mark-large" viewBox="0 0 32 32" aria-hidden="true">'
    + "".join(
        f'<rect x="{x}" y="{y}" width="{s}" height="{s}"/>'
        for x, s, ys in [
            (4.21, 3.02, [4.21, 7.63, 11.06, 17.92, 21.35, 24.78]),
            (7.63, 3.02, [4.21, 11.06, 14.49, 24.78]),
            (11.06, 3.02, [4.21, 17.92, 24.78]),
            (14.91, 2.17, [4.63, 21.77]),
            (18.65, 1.56, [11.79]),
            (22.29, 1.13, [18.87]),
            (26.5, 0.9, [9]),
            (28.5, 0.7, [21]),
        ]
        for y in ys
    )
    + "</svg>"
)
SEARCH_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="7" cy="7" r="5"/><path d="M11 11l3.5 3.5"/></svg>'


def esc(value: object) -> str:
    return html.escape(str(value))


def slug(value: str) -> str:
    return quote(value, safe="-._~")


def inline(text: str) -> str:
    """Escape upstream prose, rendering its `code` spans."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(text))


# --- Decay syntax highlighting -------------------------------------------

KEYWORDS = set(
    "script component fn let var if else while for in break continue return "
    "true false null match this event state enum struct shared".split()
)
PRIMITIVES = {"f32", "i32", "i64", "u32", "u64", "f64", "bool", "str", "unit"}
TOKEN = re.compile(
    r'(?P<cm>//[^\n]*)|(?P<str>"(?:\\.|[^"\\\n])*")|(?P<attr>@[A-Za-z_]\w*)'
    r"|(?P<num>\b\d+(?:\.\d+)?\b)|(?P<word>[A-Za-z_]\w*)"
)


def highlight(source: str) -> str:
    """Escape Decay source and wrap its tokens in highlighting spans."""
    out, pos = [], 0
    for m in TOKEN.finditer(source):
        out.append(esc(source[pos : m.start()]))
        text, kind = m.group(), m.lastgroup
        if kind == "word":
            if text in KEYWORDS:
                kind = "kw"
            elif text in PRIMITIVES or text[0].isupper():
                kind = "ty"
            else:
                kind = None
        out.append(f'<span class="{kind}">{esc(text)}</span>' if kind else esc(text))
        pos = m.end()
    out.append(esc(source[pos:]))
    return "".join(out)


def codeblock(source: str, info: str = "") -> str:
    """A fenced code block; Decay (and LANGUAGE.md's `rust`) is highlighted."""
    lang, _, expect = info.strip().partition(" ")
    expect = expect.split()[0] if expect else ""
    source = source.rstrip("\n")
    if lang in ("decay", "rust"):
        body = highlight(source)
        status = {
            "compile": '<span class="status ok">compiles · checked</span>',
            "fail": '<span class="status fail">fails · checked</span>',
        }.get(expect, "")
        head = f'<div class="codeblock-head"><span>decay</span>{status}</div>'
    else:
        body = esc(source)
        head = f'<div class="codeblock-head"><span>{esc(lang)}</span></div>' if lang and lang != "text" else ""
    return f'<div class="codeblock">{head}<pre><code>{body}</code></pre></div>'


FENCE = re.compile(r"^```([^\n`]*)\n(.*?)^```[ \t]*$", re.M | re.S)


def render_markdown(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Render Markdown with highlighted fences; return HTML and its h2 contents."""
    blocks: list[str] = []

    def stash(m: re.Match) -> str:
        blocks.append(codeblock(m.group(2), m.group(1)))
        return f"\n\nDKFENCE{len(blocks) - 1}X\n\n"

    md = markdown.Markdown(extensions=["tables", "toc"])
    rendered = md.convert(FENCE.sub(stash, text))
    for i, block in enumerate(blocks):
        rendered = rendered.replace(f"<p>DKFENCE{i}X</p>", block)

    def h2s(tokens):
        for t in tokens:
            if t["level"] == 2:
                yield t["id"], html.unescape(t["name"])
            yield from h2s(t["children"])

    return rendered, list(h2s(md.toc_tokens))


# --- API signatures -------------------------------------------------------


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


# --- Page shell -----------------------------------------------------------

NAV = [
    ("Learn", "/learn/"),
    ("Make a Game", "/make-a-game/"),
    ("Cookbook", "/cookbook/"),
    ("Reference", "/reference/"),
    ("Concepts", "/concepts/"),
]
THEME_BOOT = "(function(){var t;try{t=localStorage.getItem('decay-theme')}catch(e){}if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';document.documentElement.dataset.theme=t})()"


def page(
    title: str,
    body: str,
    route: str,
    sha: str,
    description: str = "Decay documentation",
) -> str:
    canonical = f"{SITE}{route}"
    nav = "".join(
        f'<a href="{href}"{" aria-current=page" if route.startswith(href) else ""}>{label}</a>'
        for label, href in NAV
    )
    return f"""<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Decay</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{canonical}"><meta name="theme-color" content="#0e0e0c"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;0,6..72,600;1,6..72,500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap"><link rel="stylesheet" href="/assets/site.css"><script>{THEME_BOOT}</script></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar"><div class="wrap topbar-inner"><a class="brand" href="/" aria-label="Decay home">{MARK}<span class="brand-name">Decay</span><span class="brand-sub">Knowledgebase</span></a><nav class="nav" aria-label="Primary">{nav}</nav><div class="tools"><button class="search-trigger" type="button" data-search aria-label="Search documentation">{SEARCH_ICON}<span>Search</span><kbd>/</kbd></button><button class="icon-btn" type="button" id="themeToggle" aria-label="Switch theme" title="Switch theme"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.8a6.2 6.2 0 0 1 0 12.4z" fill="currentColor"/></svg></button><button class="icon-btn menu-btn" type="button" id="menuToggle" aria-label="Menu" aria-expanded="false" aria-controls="mobileNav"><svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2.5 4.5h11M2.5 8h11M2.5 11.5h11"/></svg></button></div></div><nav class="mobile-nav wrap" id="mobileNav" aria-label="Primary mobile" hidden>{nav}</nav></header>
<main id="main">{body}</main>
<footer class="footer"><div class="wrap footer-inner"><a class="brand" href="/" aria-label="Decay home">{MARK}<span class="brand-name">Decay</span></a><p>Built for Sindri Engine. Language and host implementation remain authoritative in <a href="{ENGINE_REPO}">vardirhq/sindri-engine</a>. Generated from Sindri <a href="{ENGINE_REPO}/commit/{esc(sha)}" title="{esc(sha)}"><code>{esc(sha[:12])}</code></a>.</p><a href="https://github.com/vardirhq/decay-knowledge">GitHub</a></div></footer>
<dialog class="search" id="searchDialog" aria-label="Search"><div class="search-box"><div class="search-input">{SEARCH_ICON}<label class="sr-only" for="searchInput">Search Decay documentation</label><input id="searchInput" type="search" autocomplete="off" spellcheck="false" placeholder="Search Decay…" role="combobox" aria-controls="searchResults" aria-expanded="true"><button type="button" class="search-close" data-close>Esc</button></div><div class="search-results" id="searchResults" role="listbox"></div><div class="search-foot"><span>↑↓ move</span><span>↵ open</span><span class="grow"></span><span class="hint">Aliases included: try “dt” or “global variable”</span></div></div></dialog>
<script src="/assets/site.js" defer></script></body></html>"""


def write(out: Path, route: str, data: str) -> None:
    target = out / route.strip("/") / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data)


def doc_layout(side_title: str, side: str, article: str, toc: str = "") -> str:
    """Sidebar, article and optional "On this page" column."""
    aside = f'<aside class="sidenav" aria-label="{esc(side_title)}"><span class="side-title">{esc(side_title)}</span>{side}</aside>'
    right = f'<nav class="toc" aria-label="On this page">{toc}</nav>' if toc else ""
    return f'<div class="wrap doc-layout{" has-toc" if toc else ""}">{aside}<article class="doc">{article}</article>{right}</div>'


def side_link(label: str, href: str, current: bool, mono: bool = False) -> str:
    cls = "side-link" + (" mono" if mono else "")
    return f'<a class="{cls}" href="{href}"{" aria-current=page" if current else ""}>{label}</a>'


def crumb(*parts: tuple[str, str | None]) -> str:
    items = [f'<a href="{h}">{esc(t)}</a>' if h else f"<span>{esc(t)}</span>" for t, h in parts]
    return '<nav class="crumb" aria-label="Breadcrumb">' + '<span class="sep">/</span>'.join(items) + "</nav>"


def toc_html(headings: list[tuple[str, str]], sha: str, note: str) -> str:
    if not headings:
        return ""
    links = "".join(f'<a href="#{i}">{esc(t)}</a>' for i, t in headings)
    return f'<span class="side-title">On this page</span>{links}<div class="toc-note">{note}<br><span>sindri-engine@{esc(sha[:7])}</span></div>'


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
    owners = [(t["name"], t["members"]) for t in api["types"]] + [("this", api["this"])]
    commit_link = f'<a href="{ENGINE_REPO}/commit/{esc(sha)}" title="{esc(sha)}"><code>{esc(sha[:12])}</code></a>'

    def describe(item: dict) -> str:
        """The upstream description, when the engine provides one."""
        text = item.get("description")
        return f'<p class="lead">{inline(text)}</p>' if text else ""

    def provenance() -> str:
        """Where a generated page came from: file, schema, engine and commit."""
        return (
            '<dl class="provenance">'
            "<div><dt>Source</dt><dd>docs/generated/decay-api.json</dd></div>"
            f'<div><dt>Schema</dt><dd>v{esc(api["schema_version"])}</dd></div>'
            f'<div><dt>Engine version</dt><dd>{esc(api["engine_version"])}</dd></div>'
            f"<div><dt>Source commit</dt><dd>{commit_link}</dd></div></dl>"
        )

    def api_side(current: str | None) -> str:
        links = [
            side_link("Overview", "/reference/api/", current == ""),
            side_link("Globals", "/reference/api/#globals", current == "globals"),
        ]
        links += [
            side_link(esc(name), f"/reference/api/{slug(name)}/", current == name, mono=True)
            for name, _ in owners
        ]
        return "".join(links)

    def badges(*items: tuple[str, bool]) -> str:
        return '<div class="badges">' + "".join(
            f'<span class="badge{" accent" if accent else ""}">{esc(t)}</span>' for t, accent in items
        ) + "</div>"

    def related_types(item: dict) -> str:
        related = []
        for typ in item.get("parameters", []) + [item.get("returns"), item.get("type")]:
            if typ in types and typ not in related:
                related.append(typ)
        if not related:
            return ""
        links = "".join(f'<a class="chip" href="/reference/api/{slug(t)}/">{esc(t)}</a>' for t in related)
        return f'<h2 class="label">Related types</h2><p class="chips">{links}</p>'

    def symbol_body(item: dict, owner: str | None, crumbs: tuple) -> str:
        sig = signature(item, owner)
        name = (
            f'{esc(owner)}.<wbr><span class="accent">{esc(item["name"])}</span>'
            if owner
            else f'<span class="accent">{esc(item["name"])}</span>'
        )
        note = ""
        if item["kind"] == "function" and item.get("parameters") and not item.get("parameter_names"):
            note = '<p class="note">Parameters are positional. Parameter names are not in this export yet; they appear here once Sindri\'s host declarations provide them.</p>'
        owner_row = (
            f'<p class="owner-line">Member of <a href="/reference/api/{slug(owner)}/"><code>{esc(owner)}</code></a></p>'
            if owner
            else ""
        )
        return (
            crumb(*crumbs)
            + badges((item["kind"], True), ("generated", False))
            + f'<h1 class="symbol-title">{name}</h1>{describe(item)}'
            + f'<h2 class="label">Signature</h2><div class="codeblock signature"><pre><code>{highlight(sig)}</code></pre></div>{note}'
            + owner_row
            + related_types(item)
            + provenance()
        )

    for item in api["globals"]:
        route = f"/reference/api/globals/{slug(item['name'])}/"
        sig = signature(item)
        body = doc_layout(
            "Sindri API",
            api_side("globals"),
            symbol_body(item, None, (("Reference", "/reference/"), ("Sindri API", "/reference/api/"), ("Globals", "/reference/api/#globals"))),
        )
        write(out, route, page(item["name"], body, route, sha, item.get("description") or "Decay documentation"))
        routes.append(route)
        add(item["name"], f"Global {item['kind']}", " ".join(filter(None, [sig, item.get("description")])), route)

    generated_aliases = {
        "Input": "controller gamepad input",
        "Gamepad": "controller input",
        "World": "spawn object spawning",
        "Time": "delta time dt update",
    }
    cards = []
    for owner, members in owners:
        owner_route = f"/reference/api/{slug(owner)}/"
        links = []
        for item in members:
            route = owner_route + slug(item["name"]) + "/"
            sig = signature(item, owner)
            body = doc_layout(
                "Sindri API",
                api_side(owner),
                symbol_body(item, owner, (("Reference", "/reference/"), ("Sindri API", "/reference/api/"), (owner, owner_route))),
            )
            write(out, route, page(f"{owner}.{item['name']}", body, route, sha, item.get("description") or "Decay documentation"))
            routes.append(route)
            summary = f'<span class="summary">{inline(item["description"])}</span>' if item.get("description") else ""
            links.append(
                f'<li><a href="{route}"><code>{highlight(sig)}</code></a>{summary}</li>'
            )
            add(f"{owner}.{item['name']}", item["kind"], " ".join(filter(None, [sig, item.get("description")])), route)
        kind = "this members" if owner == "this" else "Host type"
        owner_text = (
            "What a script can reach on the object it is attached to, beyond its own fields."
            if owner == "this"
            else types.get(owner, {}).get("description")
        )
        article = (
            crumb(("Reference", "/reference/"), ("Sindri API", "/reference/api/"), (owner, None))
            + badges((kind, True), ("generated", False))
            + f'<h1 class="symbol-title">{esc(owner)}</h1>{describe({"description": owner_text})}'
            + f'<h2 class="label">{len(members)} members · engine {esc(api["engine_version"])}</h2>'
            + f'<ul class="symbol-list">{"".join(links)}</ul>'
            + provenance()
        )
        write(out, owner_route, page(owner, doc_layout("Sindri API", api_side(owner), article), owner_route, sha, owner_text or "Decay documentation"))
        routes.append(owner_route)
        add(owner, kind, " ".join(m["name"] for m in members), owner_route, generated_aliases.get(owner, ""))
        blurb = f'<span class="summary">{inline(owner_text)}</span>' if owner_text else ""
        cards.append(
            f'<li><a href="{owner_route}"><code>{esc(owner)}</code></a><span class="count">{len(members)} members</span>{blurb}</li>'
        )

    api_route = "/reference/api/"
    globals_links = "".join(
        f'<li><a href="/reference/api/globals/{slug(x["name"])}/"><code>{highlight(signature(x))}</code></a>'
        + (f'<span class="summary">{inline(x["description"])}</span>' if x.get("description") else "")
        + "</li>"
        for x in api["globals"]
    )
    article = (
        crumb(("Reference", "/reference/"), ("Sindri API", None))
        + badges(("generated reference", True))
        + f'<h1>Sindri Decay API</h1><p class="lead">Executable truth from engine <strong>{esc(api["engine_version"])}</strong> at {commit_link}. This index is generated; do not edit signatures here.</p>'
        + f'<h2 class="label" id="types">Host types and namespaces</h2><ul class="symbol-list">{"".join(cards)}</ul>'
        + f'<h2 class="label" id="globals">Globals</h2><ul class="symbol-list">{globals_links}</ul>'
        + provenance()
    )
    write(out, api_route, page("Sindri API", doc_layout("Sindri API", api_side(""), article), api_route, sha))
    routes.append(api_route)
    add("Sindri API", "Reference", "host namespaces types globals functions", api_route)

    language_source = engine / "decay/LANGUAGE.md"
    if not language_source.is_file():
        raise SystemExit(f"missing authoritative language reference: {language_source}")
    language_markdown = language_source.read_text()
    language_route = "/reference/language/"
    language_html, language_h2 = render_markdown(language_markdown)
    lang_side = side_link("Overview", "/reference/", False) + "".join(
        side_link(esc(t), f"#{i}", False) for i, t in language_h2 if t != "Contents"
    )
    article = (
        crumb(("Reference", "/reference/"), ("Language", None))
        + badges(("generated from decay/LANGUAGE.md", True))
        + language_html
        + f'<dl class="provenance"><div><dt>Source</dt><dd><a href="{ENGINE_REPO}/blob/{esc(sha)}/decay/LANGUAGE.md">decay/LANGUAGE.md</a></dd></div><div><dt>Plain text</dt><dd><a href="/reference/language/source.md">source.md</a></dd></div><div><dt>Source commit</dt><dd>{commit_link}</dd></div></dl>'
    )
    write(out, language_route, page("Decay language reference", doc_layout("Language reference", lang_side, article), language_route, sha))
    routes.append(language_route)
    add(
        "Decay language reference",
        "Language reference",
        re.sub(r"\W+", " ", language_markdown),
        language_route,
        "syntax keywords types operators vectors lists text events state collections timers",
    )
    (out / "reference/language/source.md").write_text(language_markdown)
    lang_ids = set(re.findall(r'id="([^"]+)"', language_html))

    # Authored content -----------------------------------------------------
    authored = {}
    for path in sorted((ROOT / "content").glob("*/*.md")):
        if path.name == "README.md":
            continue
        meta, md = frontmatter(path)
        section = path.parent.name
        route = f"/{section}/" if path.stem == "index" else f"/{section}/{path.stem}/"
        authored.setdefault(section, []).append((path, meta, md, route))

    section_pages = {
        s: [(m["title"], r, m["description"]) for p, m, _, r in items if p.stem != "index"]
        for s, items in authored.items()
    }

    def section_side(section: str, current: str) -> str:
        pages = section_pages.get(section, [])
        numbered = section == "learn"
        links = "".join(
            side_link(f"{f'{n}. ' if numbered else ''}{esc(t)}", r, r == current)
            for n, (t, r, _) in enumerate(pages, 1)
        )
        if numbered:
            links += "".join(
                f'<span class="side-link soon">{n}. {esc(t)}</span>'
                for n, (t, _) in enumerate(PLANNED_LESSONS, len(pages) + 1)
            )
        others = "".join(
            side_link(esc(name), f"/{s}/", False)
            for s, name in SECTION_NAMES.items()
            if s != section
        )
        return links + f'<span class="side-title sub">Elsewhere</span>{others}'

    for section, items in authored.items():
        name = SECTION_NAMES.get(section, section.title())
        pages = section_pages.get(section, [])
        for path, meta, md, route in items:
            rendered, headings = render_markdown(md)
            if not rendered.lstrip().startswith("<h1"):
                rendered = f"<h1>{esc(meta['title'])}</h1>" + rendered
            idx = next((i for i, (_, r, _) in enumerate(pages) if r == route), None)
            pager = ""
            if idx is not None:
                prev = pages[idx - 1] if idx > 0 else (name, f"/{section}/", "")
                back = f'<a class="pager-card" href="{prev[1]}"><span>← {"Previous" if idx > 0 else "Back"}</span><strong>{esc(prev[0])}</strong></a>'
                if idx + 1 < len(pages):
                    nxt = pages[idx + 1]
                    fwd = f'<a class="pager-card next" href="{nxt[1]}"><span>Next</span><strong>{esc(nxt[0])} →</strong></a>'
                elif section == "learn" and PLANNED_LESSONS:
                    fwd = f'<div class="pager-card next soon"><span>Next lesson · soon</span><strong>{esc(PLANNED_LESSONS[0][0])} →</strong></div>'
                else:
                    fwd = '<a class="pager-card next" href="/"><span>Done here</span><strong>Knowledgebase home →</strong></a>'
                pager = f'<nav class="pager" aria-label="Pagination">{back}{fwd}</nav>'
            article = (
                crumb((name, f"/{section}/"), (meta["title"], None))
                + rendered
                + pager
            )
            toc = toc_html(headings, sha, "Examples checked against")
            body = doc_layout(name, section_side(section, route), article, toc)
            write(out, route, page(meta["title"], body, route, sha, meta["description"]))
            routes.append(route)
            add(meta["title"], section.title(), re.sub(r"\W+", " ", md), route, meta.get("aliases", ""))

    for section, items in section_pages.items():
        route = f"/{section}/"
        if not items or any(r == route for *_, r in authored[section]):
            continue
        name = SECTION_NAMES.get(section, section.title())
        rows = "".join(
            f'<a class="row" href="{r}"><span class="row-no">{f"{n:02d}" if section == "learn" else "→"}</span><span><strong>{esc(t)}</strong><span>{esc(d)}</span></span><span class="tag accent">Read →</span></a>'
            for n, (t, r, d) in enumerate(items, 1)
        )
        if section == "learn":
            rows += "".join(
                f'<div class="row"><span class="row-no muted">{n:02d}</span><span><strong>{esc(t)}</strong><span>{esc(d)}</span></span><span class="tag">Soon</span></div>'
                for n, (t, d) in enumerate(PLANNED_LESSONS, len(items) + 1)
            )
        article = f'{crumb((name, None))}<h1>{esc(name)}</h1><div class="rows">{rows}</div>'
        write(out, route, page(name, doc_layout(name, section_side(section, route), article), route, sha))
        routes.append(route)

    # Reference landing ----------------------------------------------------
    def ref_rows(items):
        return "".join(
            f'<a class="ref-row" href="{h}"><code>{esc(n)}</code><span>{inline(d)}</span></a>' for n, d, h in items
        )

    def lang_anchor(anchor: str) -> str:
        return f"/reference/language/#{anchor}" if anchor in lang_ids else "/reference/language/"

    ref_lang = [
        ("script", "Gameplay script declaration", lang_anchor("containers")),
        ("state", "Typed shared project state", lang_anchor("state")),
        ("event", "Project-wide typed events", lang_anchor("events")),
        ("Vec2", "Two-dimensional vector value", lang_anchor("vectors")),
    ]
    ref_api = [
        (n, types[n].get("description") or "Sindri host namespace", f"/reference/api/{slug(n)}/")
        for n in ("Input", "World", "Physics", "Audio")
        if n in types
    ]

    def ref_columns(lang_items, api_items):
        return (
            '<div class="ref-cols">'
            f'<div><div class="ref-head"><h3><a href="/reference/language/">Language</a></h3><span>decay/LANGUAGE.md</span></div>{ref_rows(lang_items)}</div>'
            f'<div><div class="ref-head"><h3><a href="/reference/api/">Sindri API</a></h3><span>decay-api.json</span></div>{ref_rows(api_items)}</div>'
            "</div>"
        )

    all_types = [
        (n, types[n].get("description") or "", f"/reference/api/{slug(n)}/") for n in types
    ]
    reference_body = (
        '<section class="section first"><div class="wrap">'
        '<div class="section-head"><div><div class="eyebrow">Reference</div><h1 class="h2">Exact answers, quickly.</h1></div>'
        "<p>Language truth comes from Decay. Sindri host API truth comes from Sindri. This site presents it instead of inventing a third version.</p></div>"
        + ref_columns(
            [("LANGUAGE.md", "The complete Decay language reference", "/reference/language/")] + ref_lang,
            [("Overview", f"All {len(types)} host types and {len(api['globals'])} globals", "/reference/api/")]
            + all_types,
        )
        + "</div></section>"
    )
    write(out, "/reference/", page("Reference", reference_body, "/reference/", sha, "Decay language and Sindri API reference."))
    routes.append("/reference/")

    # Home -----------------------------------------------------------------
    hero_code = """script Player {
    @export
    var speed: f32 = 220.0;

    fn update(dt: f32) {
        let direction = Input.axis("move_left", "move_right");
        this.transform.position.x += direction * speed * dt;
    }
}"""
    hero_lines = "".join(f'<span class="line">{line}</span>' for line in highlight(hero_code).split("\n"))
    learn_pages = section_pages.get("learn", [])
    lesson_rows = "".join(
        f'<a class="row" href="{r}"><span class="row-no">{n:02d}</span><span><strong>{esc(t)}</strong><span>{esc(d)}</span></span><span class="tag accent">Read →</span></a>'
        for n, (t, r, d) in enumerate(learn_pages, 1)
    ) + "".join(
        f'<div class="row"><span class="row-no muted">{n:02d}</span><span><strong>{esc(t)}</strong><span>{esc(d)}</span></span><span class="tag">Soon</span></div>'
        for n, (t, d) in enumerate(PLANNED_LESSONS[: max(0, 6 - len(learn_pages))], len(learn_pages) + 1)
    )
    recipes = [
        (tag, t, d, r) for (t, r, d), tag in zip(section_pages.get("cookbook", []), ["Movement", "Recipe", "Recipe"])
    ]
    for tag, t, d in [
        ("Communication", "Talk to another script", "Use typed script references instead of property-name strings."),
        ("Architecture", "Keep game-wide score", "Choose shared state when data belongs to the game rather than one entity."),
    ]:
        if len(recipes) < 3:
            recipes.append((tag, t, d, None))
    recipe_cards = "".join(
        (f'<a class="recipe" href="{r}">' if r else '<div class="recipe soon">')
        + f'<span class="eyebrow">{esc(tag)}</span><h3>{esc(t)}</h3><p>{esc(d)}</p>'
        + ('<span class="more">Read →</span></a>' if r else '<span class="tag">Soon</span></div>')
        for tag, t, d, r in recipes
    )
    concept_href = next((r for _, r, _ in section_pages.get("concepts", [])), "/concepts/")
    progress = "".join('<i class="on"></i>' if i < 2 else "<i></i>" for i in range(15))
    home = f"""<section class="hero wrap" id="home">
<div><div class="eyebrow">Sindri's gameplay language</div><h1>Build game logic.<br><em>Keep Rust underneath.</em></h1><p class="lede">Decay is a Rust-inspired, statically typed language made for gameplay. Learn it by building, look up exact syntax when you need it, and get back to your game.</p><div class="actions"><a class="btn primary" href="/learn/first-script/">Write your first script <span aria-hidden="true">→</span></a><a class="btn" href="/reference/">Browse reference</a></div></div>
<figure class="code-window" aria-label="Decay example"><div class="code-head"><span class="file">player.decay</span><span class="grow"></span><button type="button" class="copy" data-copy="heroCode">Copy</button></div><pre id="heroCode"><code class="numbered">{hero_lines}</code></pre></figure>
</section>
<section class="section" id="learn"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Start here</div><h2>Learn by making things happen.</h2></div><p>Short lessons introduce language features when a game actually needs them. Revolutionary concept, apparently.</p></div><div class="rows two">{lesson_rows}</div></div></section>
<section class="section alt" id="game"><div class="wrap split"><div><div class="eyebrow">Guided project</div><h2>Make a complete game.</h2><p class="muted">One project from empty scene to exported build. No mysterious starter project quietly doing half the work.</p></div><a class="project-card" href="/make-a-game/"><div class="project-top"><span class="tag accent">Coming next</span><span class="mono muted">15 chapters</span></div><h3>Build a tiny arena game</h3><p>Movement, enemies, collisions, health, score, events, shared state, audio, Weave UI and export, introduced because the game needs them.</p><div class="progress" aria-hidden="true">{progress}</div><small>Knowledgebase foundation in progress</small></a></div></section>
<section class="section" id="cookbook"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Cookbook</div><h2>How do I…?</h2></div><p>Answers for when you already know enough Decay and simply need the thing on screen to behave.</p></div><div class="recipes">{recipe_cards}</div></div></section>
<section class="section" id="reference"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Reference</div><h2>Exact answers, quickly.</h2></div><p>Language truth comes from Decay. Sindri host API truth comes from Sindri. This site presents it instead of inventing a third version.</p></div>{ref_columns(ref_lang, ref_api)}</div></section>
<section class="section" id="concepts"><div class="wrap"><div class="eyebrow">Concepts</div><h2 class="spaced">Choose the right communication tool.</h2><div class="decision"><a href="{concept_href}"><span class="mono muted">1 → 1</span><strong>One particular script?</strong><span class="mono accent">Typed script reference / message</span></a><a href="{concept_href}"><span class="mono muted">1 → many</span><strong>Announce something happened?</strong><span class="mono accent">Event</span></a><a href="{concept_href}"><span class="mono muted">everyone ↔ game</span><strong>Game-wide data?</strong><span class="mono accent">Shared state</span></a></div></div></section>"""
    write(out, "/", page("Language and API documentation", home, "/", sha, "Learn Decay, Sindri Engine's Rust-inspired, statically typed gameplay language."))

    notfound = f'<section class="wrap notfound">{MARK_LARGE}<div><div class="eyebrow mono">404 · not found</div><h1>This page has decayed.</h1><p class="lede">It had a half-life, and it used it. The route may have moved when the reference was regenerated.</p><div class="actions"><button class="btn primary" type="button" data-search>Search the docs</button><a class="btn" href="/">Go home</a></div></div></section>'
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
