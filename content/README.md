# Decay Knowledgebase content model

This repository owns the public teaching experience for Decay. `vardirhq/sindri-engine` remains authoritative for language semantics and the Sindri host API.

## Content layers

- **Learn** teaches progressively and explains why a feature exists.
- **Cookbook** answers practical "How do I...?" questions quickly.
- **Concepts** explain mental models and design choices.
- **Reference** states exact language and host-API truth.
- **Diagnostics** explain compiler/LSP errors and likely fixes.
- **Make a Game** teaches Sindri + Decay through one complete project.

## Source-of-truth rules

1. Do not hand-maintain host signatures that already exist in `sindri-engine/docs/generated/decay-api.json`.
2. Language examples must be checked against current Decay before publication.
3. Host examples must use the current Sindri host surface, not remembered syntax.
4. Teaching may simplify an explanation, but it may not contradict the reference.
5. Search metadata should include the words developers actually use, not only Decay terminology.

## Page metadata

Authored content should eventually carry at least:

```yaml
kind: learn | cookbook | concept | diagnostic | tutorial
slug: stable-url-slug
title: Human-readable title
summary: One-sentence search result description
level: beginner | intermediate | advanced
topics: [events, state]
aliases: [global variable, broadcast]
```

Generated reference pages get their symbol/signature metadata from the upstream export instead.

## Validation target

The knowledgebase is trustworthy only when examples and generated reference data are validated against the `sindri-engine` revision each CI build resolves (latest `main` unless one is named). A future language/API change that invalidates published material should break knowledgebase validation rather than silently ship stale documentation.
