---
title: Make a camera follow the player
description: Follow a gameplay target with a dead zone, smoothing, confinement, and optional camera shake.
aliases: camera follow, follow player, smooth camera, dead zone, camera smoothing, camera bounds, camera shake
---

# Make a camera follow the player

A following camera should usually be **authored as camera behavior**, not rebuilt every frame in Decay.

Sindri keeps projection and gameplay behavior separate. The camera entity owns a `sindri.camera` component for projection and may also own `sindri.camera.behavior` for follow, confinement, and shake. The engine advances that behavior after gameplay scripts, so the camera follows the position your player reached during the current frame.

That means your player script can stay concerned with the player:

```decay compile
script Player {
    @export let speed: f32 = 5.0;

    fn update(dt: f32) {
        this.transform.position.x += Input.axis("ArrowLeft", "ArrowRight") * speed * dt;
        this.transform.position.y += Input.axis("ArrowDown", "ArrowUp") * speed * dt;
    }
}
```

The camera follows because of its authored behavior, not because this script knows a camera exists.

## Add follow behavior to the camera

Give the camera entity both its normal camera component and a behavior component. This is a shortened scene-format example showing the relevant fields:

```json
{
  "id": "camera",
  "name": "Gameplay Camera",
  "transform_3d": {
    "position": [0, 0, 10],
    "rotation": [0, 0, 0, 1],
    "scale": [1, 1, 1]
  },
  "components": {
    "sindri.camera": {
      "projection": "orthographic",
      "vertical_size": 8,
      "near": 0.1,
      "far": 100,
      "fit": "height"
    },
    "sindri.camera.behavior": {
      "follow": {
        "target": "player",
        "offset": [0, 0, 0],
        "dead_zone": [2.5, 1.5],
        "smoothing": 5,
        "max_speed": 8
      }
    }
  }
}
```

`target` is the stable entity ID to follow. In this example the player entity therefore has the ID `player`.

The four follow settings solve different problems:

| Setting | What it changes |
| --- | --- |
| `offset` | Keeps the camera displaced from the target. Useful when the player should not sit exactly at screen center. |
| `dead_zone` | Lets the target move inside a rectangular area before the camera starts following. |
| `smoothing` | Makes the camera converge on its desired position instead of snapping there immediately. |
| `max_speed` | Caps how quickly the camera may catch up. |

Start simple. Use a zero offset, a modest dead zone, and tune smoothing while playing. A giant dead zone plus a low maximum speed can make a perfectly functional camera feel as though it has become emotionally detached from the player.

## Keep the camera inside the level

A following camera can expose empty space beyond the edge of a bounded level. Add `confine` beside `follow`:

```json
"sindri.camera.behavior": {
  "follow": {
    "target": "player",
    "offset": [0, 0, 0],
    "dead_zone": [2.5, 1.5],
    "smoothing": 5,
    "max_speed": 8
  },
  "confine": {
    "min": [-8, -4],
    "max": [8, 4]
  }
}
```

The bounds are world-space XY camera-position limits. Follow is evaluated first and confinement then clamps the resulting camera position.

## Add impact shake from gameplay

Camera follow itself is engine-owned behavior, but gameplay can decide **when** an impact should shake the camera. Configure shake on the camera:

```json
"shake": {
  "trauma": 0,
  "strength": 0.3,
  "decay": 1.6,
  "frequency": 30,
  "phase": 0
}
```

Then add trauma from Decay when something meaningful happens:

```decay compile
script Player {
    fn update(dt: f32) {
        if Input.just_pressed("Space") {
            Camera.add_trauma(1.0);
        }
    }
}
```

`Camera.add_trauma` changes the camera behavior's transient trauma. The behavior owns the actual shake motion and decay, so gameplay code does not need to generate offsets or noise itself.

## Behavior order matters

Sindri evaluates camera behavior in this order:

1. **Follow** finds the desired camera position.
2. **Confinement** clamps that position to the authored world bounds.
3. **Shake** adds transient impact motion.

Because shake comes last, a strong impact may briefly move the rendered camera across a confinement edge. It does not change the camera's underlying followed position.

## Common mistakes

### Moving the camera manually in every player script

Don't make ordinary player movement responsible for copying the player's position into the camera. You lose the authored dead zone, smoothing, confinement, and engine-owned behavior ordering, while coupling gameplay to presentation for no useful prize.

### Following an entity name instead of its ID

The behavior target is a stable scene entity ID. If the player is named `Hero` but its ID is `player`, the target is `player`.

### Expecting `Camera.add_trauma` to create follow behavior

It doesn't. The camera must already have authored camera behavior, including shake configuration. The Decay call is the gameplay trigger.

### Updating follow before player movement

You do not need to order this yourself. Gameplay hosts advance camera behavior after scripts, so the camera sees the target position produced by that frame's gameplay update.

## When to use something else

This recipe is for the standard case: one authored world camera following a gameplay entity. Sindri currently renders exactly one authored world camera per game frame. Split-screen, camera stacks, render targets, and camera-priority systems are different features rather than hidden modes of this follow component.

For the complete working implementation, see Sindri's `examples/camera` feature example. It uses the same `sindri.camera.behavior` component and the same engine update path described here.
