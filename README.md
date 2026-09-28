# Decay Knowledgebase

The static documentation published at **https://decay.vardir.no**. The design
rule is **TEACH HERE, DEFINE THERE**: this repository owns authored learning,
concept, cookbook, and diagnostic explanations; [`vardirhq/sindri-engine`](https://github.com/vardirhq/sindri-engine)
owns executable language and host-API truth.

## Architecture

`scripts/build.py` reads Sindri's generated `docs/generated/decay-api.json`,
discovers every global, function, type, namespace-like host value, member, and
`this` member, and emits static routes under `_site/reference/api/`. The
authoritative `decay/LANGUAGE.md` is rendered at `/reference/language/` without
trying to infer a second symbol model from its prose. The build also
builds `search-index.json`, `sitemap.xml`, canonical metadata, a 404 page, and
`build-metadata.json`. The page shell, home, reference landing and 404 are
rendered by the build too (there is no hand-written root `index.html`); styling
lives in `assets/site.css`, with dark and light themes. Every page and metadata artifact records the exact
engine Git SHA. `_site` is intentionally uncommitted: the two source revisions
reproduce it.

The JSON is generated in Sindri from the host surface shared by analyzer and
runtime (`cargo run -p sindri-capabilities -- --write`). This repository does
not parse `docs/scripting.md` or guess descriptions from prose. Parameter names
and structured descriptions are not in schema version 1; those should be added
to the canonical Sindri host declarations/generator before this site displays
them. `decay/LANGUAGE.md` likewise remains the current human-readable language
authority. Compiler structures do contain tokens/types, but Sindri does not yet
export a stable language metadata schema, so this site deliberately does not
regex-scrape that document. The desired upstream schema is described in
`docs/upstream.md` so it can later replace prose-only language indexing.

Decay diagnostics do not yet have consistently preserved stable codes across
parser, semantic analyzer, `decay-lsp`, and JSON preflight. The gap is tracked
in Sindri's `docs/decay-lsp-modernization.md`; this site will not invent web-only
IDs.

## Local build

Read both repositories' `AGENTS.md`/`CLAUDE.md` first, then:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/validate_examples.py --engine-dir ../sindri-engine
python scripts/build.py --engine-dir ../sindri-engine
python scripts/check_site.py _site
python -m http.server --directory _site 8000
```

Use the SHA in `SINDRI_ENGINE_REVISION` to reproduce the default CI build. A
dispatch may intentionally build another exact revision; its SHA is captured
in the output rather than changing the pin.

## Authored content

Put Markdown at `content/<section>/<slug>.md` with this simple front matter:

```yaml
---
title: Human title
description: Search and page description.
aliases: controller, gamepad, input
---
```

Aliases feed client-side search. Mark every Decay fence explicitly:

````markdown
```decay compile
script Example { fn update(dt: f32) {} }
```

```decay fail
this is deliberately invalid
```
````

The validator runs each fence through the current engine's typed
`decay-lsp --check`. A `diagnostic=CODE` fence annotation is supported once an
upstream stable code is available. Never copy generated signatures into
teaching prose; link to the generated symbol route.

## GitHub automation and one-time setup

The Pages workflow runs for knowledgebase pushes/PRs, manual dispatches,
cross-repository `repository_dispatch`, and a nightly recovery schedule. It
checks out the requested engine revision, verifies Sindri's generated API is
current, validates examples, builds, checks links/search/provenance, then
deploys only after validation succeeds. GitHub Pages must be configured to use
**GitHub Actions**; DNS and the existing `CNAME` must continue pointing
`decay.vardir.no` at Pages.

For immediate engine-driven updates, add a Sindri workflow that sends event
`sindri-engine-updated` after relevant changes reach `main`, with payload
`{"sha":"${GITHUB_SHA}"}`. Cross-repository dispatch requires a fine-grained
PAT or GitHub App token with Actions/content access to `decay-knowledge`, stored
in Sindri as `DECAY_KNOWLEDGE_TOKEN`. GitHub's default `GITHUB_TOKEN` cannot
dispatch to another repository. The nightly run is the no-token safety net and
builds current `sindri-engine/main`; ordinary builds use the reproducible pin.
Update `SINDRI_ENGINE_REVISION` when adopting a new default revision. A dispatch
SHA makes updates immediate while retaining exact provenance.

## Generated versus authored

- **Generated:** host API pages and symbol indexes, search records for symbols,
  sitemap, build/source metadata.
- **Authored:** learning paths, tutorials, cookbook guidance, concepts, and
  future expanded diagnostic explanations.

Future work includes a canonical structured language export, stable upstream
diagnostic IDs, richer upstream descriptions, and tutorial project validation.
