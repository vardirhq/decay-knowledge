# Reference

Reference is exact, scan-friendly, and separated into two surfaces.

## Language reference

Answers questions about Decay itself:

- lexical structure and comments;
- declarations (`script`, functions, variables, events, state);
- types and constructors;
- expressions and operators;
- control flow;
- vectors and built-in language values;
- collections;
- attributes such as `@export`;
- lifecycle semantics;
- project-wide typing rules.

The current authority is `vardirhq/sindri-engine/decay/LANGUAGE.md`. This site should not silently add syntax that merely looks Rust-like.

## Sindri API reference

Answers questions about what Sindri exposes to Decay. The machine-readable authority is `vardirhq/sindri-engine/docs/generated/decay-api.json`, generated from the host surface shared by analyzer/runtime.

Current global namespaces include `Animation`, `Audio`, `Camera`, `Effects`, `Game`, `Gamepad`, `Gesture`, `Grid`, `Input`, `Physics`, `Pointer`, `Profiles`, `Random`, `Save`, `Scene`, `Stick`, `Time`, `Touch`, `Ui`, `Viewport`, and `World`, plus host values/functions. The generated source, not this sentence, decides the current complete list.

Generated API pages should show:

- symbol/type name;
- kind (value/function/type/member);
- exact parameter and return types;
- human explanation from the host contract where available;
- checked examples;
- related cookbook/concept pages;
- upstream engine revision used to generate the page.
