# Diagnostics knowledgebase

Decay diagnostics should eventually be searchable documentation, not merely compiler prose that disappears after the developer fixes the line.

## Desired diagnostic page

Each stable diagnostic should have:

- stable code, e.g. `DECAY-E####`;
- short title;
- representative compiler/LSP message;
- why it happens;
- minimal invalid example;
- corrected example;
- common causes;
- related language/API reference;
- version information when behaviour changed.

## Integration goal

Where tooling supports documentation links, `decay-lsp`/VS Code/Sindri should be able to link a diagnostic directly to its page on `https://decay.vardir.no/`.

Do not invent stable codes in this repository. Diagnostic identity belongs to Decay upstream. Until upstream exposes stable diagnostic IDs, this section should document common errors by concept without pretending they are permanent compiler contracts.
