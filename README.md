# ClockIn

ClockIn is a desktop timer app with floating timers that stay above your other
windows. Keep track of multiple countdowns while you work, study, or take a break.

## Features

- Create multiple timers with custom hours, minutes, and seconds.
- Keep each countdown visible in its own movable, always-on-top window.
- Pause, resume, and reset timers independently.
- Manage all your timers from one main window.
- Save your timer durations automatically for your next session.
- Use the app offline, with no account required. Your timers stay on your device.

## Installing

Download ClockIn from the official
[Releases page](https://github.com/Arik-Ahnaf/ClockIn/releases). Open a release's
**Assets** list and choose the download for your operating system. Use the packaged
app rather than GitHub's **Source code** archives; you do not need to install
Python or build ClockIn yourself.

### Windows

1. Download the `ClockIn-<version>-windows-x86_64.zip` asset for 64-bit Windows.
2. Right-click the ZIP and select **Extract All**.
3. Open the extracted `ClockIn` folder and double-click **ClockIn.exe**.

This is a portable app, so there is no installer. Keep the entire extracted folder
together; the executable needs the files beside it. You can create a shortcut to
`ClockIn.exe` for easier access.

### Arch Linux

Download the `clockin-<version>-<release>-x86_64.pkg.tar.zst` asset. In a terminal
opened in your download folder, install it with the following command, replacing
`<filename>` with the downloaded package's name:

```sh
sudo pacman -U ./<filename>.pkg.tar.zst
```

Then open **ClockIn** from your application launcher, or run:

```sh
clockin
```

Use an X11 session or install `xorg-xwayland` when using Wayland so floating timers
can be positioned and dragged correctly.

#### Portable Linux archive

If you prefer the portable download, extract the
`ClockIn-<version>-linux-x86_64.tar.gz` asset and run the `ClockIn` executable inside
the extracted folder:

```sh
./ClockIn/ClockIn
```

Keep the entire folder together. The portable archive still needs your system's
desktop libraries; the Arch package installs its required dependencies through
pacman. Linux builds target current Arch Linux and are not guaranteed to work on
other distributions or older systems.

## Using ClockIn

1. Click the **Add timer** button at the bottom of the main window, or press
   **Ctrl+N**.
2. Set the hours, minutes, and seconds. The duration must be at least one second.
3. Click the timer card's **play** button to start it and show its floating window.
4. Drag the floating timer's text or background to move it. Click its surface to
   show or hide the pause and delete controls.

Click a timer card's time to change its duration; this resets that timer. To
remove timers, use the bottom **Edit timers** button to reveal removal controls.
You can also right-click a timer card or floating timer for more actions. The
**Settings** menu lets you pause or reset all timers, or hide their floating windows.

Closing a floating window only hides it; its countdown continues. Click its
card's play button to show it again. Closing the main ClockIn window exits the
app and stops all countdowns.

### Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| **Ctrl+N** in the main window | Create a timer |
| **Space** in a floating timer | Pause or resume |
| **Delete** in a floating timer | Remove that timer |
| **Escape** in a floating timer | Collapse its controls, or hide it if already compact |

## Saved timers and updates

Timer additions, duration changes, and deletions are saved automatically. On your
next launch, saved timers start idle at their configured durations. Running
countdowns and floating-window positions are not restored.

Your timer data is stored separately from the installed app:

| Operating system | Timer data |
| --- | --- |
| Windows | `%LOCALAPPDATA%\ClockIn\timers.json` |
| Linux | `~/.local/share/ClockIn/timers.json`, or `$XDG_DATA_HOME/ClockIn/timers.json` if configured |

To back up your timers, close ClockIn and copy this file to a safe location.

To update a portable installation, close ClockIn, download the new release, and
extract it into a new folder. Launch the new copy; your saved timers remain in
the same data location. On Arch Linux, install the newer package with
`sudo pacman -U` as above.

## Help and feedback

Report bugs or request features on the
[issue tracker](https://github.com/Arik-Ahnaf/ClockIn/issues). For installation
problems, include your operating system, ClockIn version, and any error message.

For developer build and verification instructions, see [PACKAGING.md](PACKAGING.md).
