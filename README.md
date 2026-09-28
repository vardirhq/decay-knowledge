# Decay Knowledgebase

The public learning and reference site for **Decay**, Sindri Engine's Rust-inspired, statically typed gameplay language.

This repository owns the **knowledge experience**: tutorials, cookbook recipes, concepts, diagnostics explanations, search, and the website itself.

It does **not** own the Decay language implementation or Sindri host API. Those remain authoritative in [`vardirhq/sindri2`](https://github.com/vardirhq/sindri2):

- `decay/LANGUAGE.md` — implemented Decay language behaviour
- `docs/scripting.md` — Sindri host contract
- `docs/generated/decay-api.md` / `decay-api.json` — generated host API reference
- `docs/decay-direction.md` — language/product direction

The long-term rule is simple: **teach here, define there**. Reference data should be generated or synchronized from authoritative Sindri/Decay definitions rather than manually duplicated until it drifts.

## Knowledgebase structure

The intended public information architecture is:

```text
Start Here
├── What is Decay?
├── Your first script
└── Decay in 10 minutes

Learn Decay
├── Scripts
├── Variables and types
├── Functions
├── Control flow
├── Vectors
├── Entities and scripts
├── Script communication
├── Events
├── Shared state
├── Collections
└── Putting it together

Make a Game
└── A complete guided Sindri project

Cookbook
├── Movement
├── Input
├── Physics
├── Animation
├── Audio
├── Spawning
├── UI
├── State
└── Common gameplay patterns

Language Reference
Sindri API Reference
Concepts
Diagnostics
Tools
Decay Internals
```

The site should serve three jobs without muddling them together:

1. **Teach** — progressive material explaining why concepts exist and when to use them.
2. **Help accomplish tasks** — short recipes answering practical "How do I...?" questions.
3. **State exact truth** — language/API reference generated from or checked against the implementation.

## Source-of-truth boundary

`vardirhq/sindri2` remains authoritative for:

- grammar and semantics;
- types and built-ins;
- diagnostic behaviour;
- Sindri host namespaces, members, and signatures;
- runtime/editor integration.

`decay-knowledge` owns:

- teaching prose;
- tutorials and exercises;
- cookbook recipes;
- concept explanations;
- diagnostic explanations;
- search metadata and synonyms;
- site design and navigation;
- generated presentation of upstream reference data.

The same signature should never be maintained independently in the compiler, LSP, generated API docs, and this website if it can instead flow from one canonical description.

## Quality rules

A mature Decay knowledgebase should enforce these rules:

- Valid Decay examples are compiled in CI where practical.
- Deliberately-invalid examples are marked and checked as failures where practical.
- Tutorial checkpoint projects are validated against the Sindri version they teach.
- Generated API/reference material comes from Sindri/Decay's authoritative data.
- Search supports conceptual synonyms such as `global variable` → shared `state` and `controller` → gamepad/input docs.
- Teaching, cookbook, concepts, and reference link to each other instead of duplicating explanations.
- Pages clearly state whether they teach **Decay the language** or **Sindri's Decay host API**.

## Planned site

The initial design direction is a clean documentation application with:

- a focused landing page;
- persistent top navigation for Learn / Make a Game / Cookbook / Reference / Concepts;
- section sidebars for long-form material;
- excellent full-site search;
- copyable, syntax-highlighted Decay examples;
- related-content panels;
- dedicated compiler-diagnostic pages;
- responsive desktop/mobile layouts;
- future hooks for editor/LSP deep links and machine-readable knowledge access.

## Development status

This repository is being bootstrapped. The first milestone is to establish the site shell, content model, upstream Sindri/Decay synchronization strategy, and a small high-quality vertical slice covering:

- landing page;
- first-script tutorial;
- one language reference page;
- one Sindri API reference page;
- one cookbook recipe;
- one concept page;
- one diagnostic page;
- unified search across those content types.

That slice should prove the information architecture before hundreds of pages are enthusiastically generated and left for future archaeologists.
