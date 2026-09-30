# Animation Game Package

Use `runtime_glb/` first for game integration. `fbx/` is a fallback export, and
`blend_source/` keeps the Blender source files for later edits.

## Runtime GLB

- `runtime_glb/kiwi_wing_flap.glb`
  - Action: kiwi wing flap
  - Use: kiwi simple wing flapping loop

- `runtime_glb/jiligulu_idle_show.glb`
  - Action: jiligulu idle show
  - Use: jiligulu idle/display loop

- `runtime_glb/woodpecker_peck_idle.glb`
  - Action: Woodpecker_PeckIdle
  - Use: woodpecker small pecking idle loop
  - Timing: 30fps source, 1-90 frames, 3.0 seconds

- `runtime_glb/otter_swim.glb`
  - Action: Otter_Swim
  - Use: main otter shallow-creek swimming loop
  - Timing: 30fps source, 1-72 frames, 2.4 seconds

## Notes

- Original source files were not overwritten.
- `.blend1` automatic Blender backups are intentionally excluded.
- GLB is the recommended runtime format for the game.
