# Omarchy Tablet

A touch interface for convertible laptops running Omarchy: fold the screen back, type, control music, rotate to portrait, or settle into reading with a single restore button.

**Early release.** Tested on a Lenovo Yoga with Omarchy's native Quickshell plugin system and Hyprland 0.56.2 (Lua configuration). Other laptops need testing. This does not support older Waybar-based Omarchy releases or legacy Hyprland configuration APIs.

## What it does

- Detects Linux tablet-mode switches, with a manual toggle when hardware detection is unavailable.
- Provides a large on-screen keyboard, long-press accents, English/Spanish word suggestions, and reusable AI prompt snippets.
- Adds touch controls for brightness, volume, workspaces, closing the focused window, and keyboard visibility.
- Shows track information and playback controls from an existing Brave MPRIS session, including YouTube Music.
- Rotates the display, touchscreen, and pen together, with landscape and both portrait orientations.
- Collapses the tablet UI and Omarchy bar into one restore button in Zen mode. Optional grayscale and warm filters make reading more comfortable.

Suggestions use bundled word lists and only track typing through this keyboard. Prompt buttons insert text; they do not call an AI service or submit a prompt. Music requires the browser to expose an MPRIS player. Zen does not hide toolbars inside other applications. Grayscale is a color filter, not physical e-ink.

## Install

Once this repository is published, replace `<repository-url>` with its Git URL:

```bash
omarchy plugin add <repository-url> --yes
cd ~/.config/omarchy/plugins/io.github.uripg.tablet
omarchy pkg add base-devel wayland libxkbcommon cairo pango python wtype brightnessctl wireplumber
./scripts/setup
./scripts/doctor
omarchy plugin enable io.github.uripg.tablet
```

The plugin manager installs plugins disabled and does not run build hooks. The explicit setup step builds the bundled keyboard locally. Quickshell, Omarchy, Hyprland, and a working systemd user session must already be installed.

If `doctor` reports a tablet-switch permission problem, run `./scripts/setup-input` in a terminal. It shows a device-specific udev rule and asks before installing it with sudo. Manual mode works without that rule. No extra permission is needed to read browser media metadata.

Add **Tablet Mode** to your Omarchy bar using its widget settings for a persistent manual toggle. Left-click toggles tablet mode; right-click returns to automatic detection. You can also run:

```bash
./scripts/tablet on
./scripts/tablet auto
```

Do not run this alongside another tablet controller or on-screen keyboard service. If migrating from a personal `tablet-mode.service`, stop and disable that service first.

## Controls

The dock opens Quick controls, rotates the display, closes the focused window, and toggles the keyboard. The writing strip offers word suggestions and prompt snippets. Hold supported letter keys for accents.

Quick controls includes **Zen**, **Grayscale**, and **Warm light**. Enter Zen to hide the controls; tap the remaining button to restore them. Reading filters apply only while Zen is active. Exiting Zen restores the previous screen shader and bar visibility. Turning tablet mode off restores the display orientation captured when the plugin started.

Rotation is manual, not accelerometer-driven. Check touch alignment after the first rotation on a new device.

## Configuration

Optional settings: `~/.config/omarchy-tablet/settings.json` (respects `XDG_CONFIG_HOME`). Disable and re-enable the plugin after changes.

```json
{
  "monitor": "auto",
  "switch_name": "auto",
  "backlight": "auto",
  "touch_devices": "auto",
  "pen_devices": "auto",
  "keyboard_height": 400,
  "keyboard_font_size": 24,
  "media_player": "brave"
}
```

Automatic display selection prefers an internal eDP/LVDS/DSI panel. Touch and pen discovery only selects a device when there is exactly one of its kind; with multiple devices, set explicit arrays of names from `hyprctl devices -j`. Use `[]` to leave a device category alone. `monitor` and `backlight` accept explicit names; `switch_name` accepts the input device's full name. Run `scripts/doctor` to see the selection.

Keyboard height accepts 240–600; font size accepts 14–32. Set `media_player` to `"any"` to include other MPRIS players, or a substring of their D-Bus name. Multiple browser players may require pausing other tabs.

Display filters affect every monitor because Hyprland's screen shader is global. They temporarily replace an existing screen shader. Rotation maps selected touch/pen devices to the tablet display; custom per-device mappings are not preserved. Avoid rotating explicitly selected external drawing tablets unless you want that mapping.

## Update and remove

```bash
omarchy plugin disable io.github.uripg.tablet
omarchy plugin update io.github.uripg.tablet
cd ~/.config/omarchy/plugins/io.github.uripg.tablet
./scripts/setup
omarchy plugin enable io.github.uripg.tablet
```

Rebuild after updates. During source development, restart the Omarchy shell if it retains cached QML components.

To remove, disable first, then run `omarchy plugin remove io.github.uripg.tablet`. The built keyboard in `~/.local/share/omarchy-tablet` and preferences in `~/.config/omarchy-tablet` can be deleted afterward. If installed and no longer needed, remove `/etc/udev/rules.d/70-omarchy-tablet.rules` with sudo and reload udev rules.

## Troubleshooting

Run `scripts/doctor` and `journalctl --user -u omarchy-tablet-plugin.service -b`. The controller runs in a transient user service so disabling the plugin can restore the screen before stopping it. No login service is installed.

A missing switch still allows manual mode. Firmware must expose `SW_TABLET_MODE` for automatic detection. Brightness needs a usable kernel backlight device. Playback buttons depend on the player's advertised capabilities.

If the shell crashes while in Zen, re-enabling the plugin recovers the saved shader/bar state. To stop the controller directly, use `systemctl --user stop omarchy-tablet-plugin.service`. Display rotation is restored on normal shutdown; a forced kill can require manually resetting orientation.

## Development and licensing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local installation and checks. Code is GPL-3.0-only; bundled word data has separate attribution and share-alike terms in [NOTICE.md](NOTICE.md). The keyboard is a modified, pinned copy of [wvkbd](https://github.com/jjsullivan5196/wvkbd), built without fetching source during installation.
