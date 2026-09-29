# Upstream Sindri/Decay knowledge

The knowledgebase deliberately does not own Decay's executable truth.

## Authoritative upstream inputs

From `vardirhq/sindri-engine`:

- `decay/LANGUAGE.md` — implemented language syntax and semantics.
- `docs/scripting.md` — meaning and contracts of Sindri host calls.
- `docs/generated/decay-api.json` — machine-readable host surface.
- `docs/generated/decay-api.md` — human-readable generated host surface.
- `docs/decay-direction.md` — product/language direction, not a substitute for implemented behaviour.

`decay-api.json` is generated from the same host description used by the analyzer/runtime and should be the primary input for generated Sindri API pages.

## Implemented synchronization

The site builds the latest `sindri-engine/main` during CI, unless a manual run
or a dispatch names an exact revision; every build records the resolved commit, so reference generation and example validation
always use the same checkout.

```text
sindri-engine
  decay/LANGUAGE.md
  docs/scripting.md
  docs/generated/decay-api.json
          |
          v
knowledge import / validation
          |
     +----+----+
     |         |
 reference   search
     |         |
     +----+----+
          |
        site
```

`scripts/build.py` creates the reference and search artifacts directly in the
uncommitted Pages output. Do not silently mix reference data from one engine
revision with examples validated against another.

## Future structured language export

The host API already has structured JSON. The language itself does not yet expose an equivalent complete documentation schema. When one is added upstream, prefer it over parsing Markdown. Until then, `decay/LANGUAGE.md` remains authoritative for language reference prose and grammar claims.

A useful generated `docs/generated/decay-language.json` would include the
following, derived from parser/compiler/analyzer definitions rather than a
parallel hand-maintained list:

- a schema version and Decay language version;
- keywords, contextual keywords, declaration forms, and attributes;
- primitive and built-in value types, constructors, and members;
- operators with arity, precedence, and associativity;
- lifecycle functions and their exact signatures;
- list, text, vector, timer, collection, event, state, and script-communication
  operations;
- stable diagnostic IDs, phase/category, message templates, and documentation
  URLs where available.

Each entry should have a stable machine name, display name, kind, exact
signature or token spelling where applicable, and optional structured
description. References between entries should use stable names. Ordering must
be deterministic and the generator should have the same check/write contract
as `sindri-capabilities`.

This repository can then generate language symbol routes and diagnostics from
that file while continuing to render `LANGUAGE.md` as authored reference prose.
It should reject unknown schema versions rather than silently publishing an
incomplete interpretation. Diagnostic IDs must originate in the compiler/LSP,
not in this site.
