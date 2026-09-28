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

## Sync design

The site should consume a pinned upstream revision during CI:

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

The first implementation may copy the generated JSON into a build artifact, but it must record the upstream commit SHA. Do not silently mix reference data from one engine revision with examples validated against another.

## Future structured language export

The host API already has structured JSON. The language itself does not yet expose an equivalent complete documentation schema. When one is added upstream, prefer it over parsing Markdown. Until then, `decay/LANGUAGE.md` remains authoritative for language reference prose and grammar claims.

A useful language export would eventually include:

- keywords and declarations;
- primitive and built-in value types;
- operators and precedence;
- constructors and built-in members;
- lifecycle functions;
- attributes such as `@export`;
- diagnostic codes and documentation links where available;
- language/schema version.
