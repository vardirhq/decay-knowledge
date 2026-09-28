# Decay concepts

Concept pages explain how to think about Decay. They are not syntax reference pages.

## Communication model

Choose based on ownership and audience:

| Need | Prefer |
| --- | --- |
| Configure a value per script/entity | `@export` field |
| Talk to one known script | typed script reference/message |
| Announce that something happened | typed event |
| Store data owned by the game/project | shared state |

The important distinction is coupling. A direct message knows its recipient. An event describes an occurrence and lets listeners decide whether they care. Shared state represents durable project-wide data rather than a notification.

## Other concept pages to build

- Script lifecycle and frame ordering
- Entity versus script identity
- The project-wide type environment
- Host API versus Decay language
- Mutation and value semantics
- Timers and frame time
- Operation budgets and runtime safety
- Prefabs, entities and script instances
- Input actions versus physical devices
- Decay's Rust inspiration: what it borrows and deliberately does not borrow
