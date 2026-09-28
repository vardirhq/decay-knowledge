---
title: Decay diagnostics
description: Explanations and fixes for stable Decay compiler diagnostics.
aliases: compiler error, lsp error, error code
---

# Decay diagnostics

Diagnostic reference pages will appear here once the compiler and LSP expose
stable diagnostic IDs. IDs will come from Sindri; this site will not create a
second, web-only identity scheme.

Until then, use the exact message and source span reported by `decay-lsp` and
consult the [language reference](/reference/language/).

The documentation build also checks deliberately invalid examples. This sample
must continue to fail because `missing` was never declared:

```decay fail
script UndeclaredName {
    fn update(dt: f32) {
        missing = dt;
    }
}
```
