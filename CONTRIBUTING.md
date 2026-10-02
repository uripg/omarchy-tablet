# Contributing

Hardware reports are useful: include the laptop model, Omarchy/Hyprland/Quickshell versions, and `scripts/doctor` output. Remove personal device names before posting. Say whether detection, landscape/portrait touch alignment, pen alignment, and brightness work.

## Local installation

From a clone:

```bash
./scripts/setup
mkdir -p ~/.config/omarchy/plugins
ln -s "$PWD" ~/.config/omarchy/plugins/io.github.uripg.tablet
omarchy-shell shell rescanPlugins
omarchy plugin enable io.github.uripg.tablet
```

Do not overwrite an existing installation. Disable other tablet controllers before testing. Restart the shell with `omarchy restart shell` after QML edits if its component cache keeps the old code.

## Checks

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile backend/*.py
bash -n scripts/setup scripts/start-service scripts/tablet
./scripts/setup
```

Manual tests need a real Wayland session and convertible hardware:

1. Fold/unfold and verify keyboard/dock visibility; also test manual mode without switch access.
2. Type short taps, hold a letter for accents, cancel a held key by moving away, and use suggestions in English and Spanish. Change application focus and check suggestions clear.
3. Test brightness/volume and Brave playback controls with an existing session.
4. Rotate both ways; check all screen corners, keyboard keys, and pen alignment. Disable and verify the original orientation returns.
5. Enter Zen with each filter combination. Restore with the floating button. Repeat with the bar already hidden and with an existing screen shader.
6. Disable the plugin while in portrait and Zen. Check the shader, bar, orientation, keyboard process, and controller all restore or stop correctly.

Keep native plugin lifecycle handling in Service.qml, UI in ui/, and hardware/controller behavior in backend/. Do not add install hooks that run privileged commands. The switch permission helper remains an explicit, reviewable step.

The vendored keyboard records its upstream commit and modifications in vendor/wvkbd/UPSTREAM.txt. Keep upstream license files when changing or updating it.
