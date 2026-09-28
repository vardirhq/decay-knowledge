---
title: Your first Decay script
description: Add frame-by-frame behaviour to a Sindri entity.
aliases: first script, update loop, delta time, dt
---

# Your first Decay script

A script groups state and behaviour. Sindri calls `start` once and `update`
once per frame. The `dt` argument is elapsed time in seconds, so multiplying by
it makes movement independent of frame rate.

```decay compile
script FirstScript {
    var elapsed: f32 = 0.0;

    fn start() {
        elapsed = 0.0;
    }

    fn update(dt: f32) {
        elapsed += dt;
    }
}
```

Examples in this site declare their expectation explicitly. The build checks
this example with the current engine rather than assuming old teaching still
compiles. Continue with the [generated API reference](/reference/api/).

