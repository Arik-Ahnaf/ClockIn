# ClockIn

ClockIn is a desktop timer app with floating timers that stay above your other
windows. Keep track of multiple countdowns while you work, study, or take a break.

<img width="240" height="240" alt="Logo" src="https://github.com/user-attachments/assets/55d63bc4-19d2-432c-afae-b24fea936121" />

## Features

- Create multiple timers with custom hours, minutes, and seconds.
- Keep each countdown visible in its own movable, always-on-top window.
- Pause, resume, and reset timers independently.
- Hear the system alarm sound when a timer finishes on Windows or Arch Linux.
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

## Usage

Refer to the [wiki](https://github.com/Arik-Ahnaf/ClockIn/wiki) for detailed instructions on how to use the app.

## Help and feedback

Report bugs or request features on the
[issue tracker](https://github.com/Arik-Ahnaf/ClockIn/issues). For installation
problems, include your operating system, ClockIn version, and any error message.

## Building Windows

On Linux, use GitHub **Actions → Build Windows → Run workflow**, then download
the `ClockIn-windows` artifact from the successful run. The workflow builds and
executes the app on `windows-latest`; do not use Wine or Linux PyInstaller to
build Windows executables. Changes to the Windows workflow also trigger a build.

On Windows, run `./packaging/windows/build.ps1` with `uv` installed. Both methods
use the same `ClockIn.spec` and produce `dist/ClockIn-<version>-windows-x86_64.zip`.
Extract the ZIP and keep the complete `ClockIn` folder, including its assets,
styles, defaults, and runtime libraries, together.
