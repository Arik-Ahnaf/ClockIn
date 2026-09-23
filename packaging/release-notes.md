ClockIn desktop timer for Windows and Arch Linux, built with Python and PySide6.

### Downloads

- **Windows x64:** download the `windows-x86_64.zip`, extract the entire folder, and launch `ClockIn.exe`.
- **Linux x86_64:** download the `linux-x86_64.tar.gz`, extract it, and launch `ClockIn/ClockIn`. This build targets current Arch Linux and requires an X11/XWayland desktop and the documented system libraries.
- **Arch Linux package:** install the `.pkg.tar.zst` with `sudo pacman -U <filename>`.
- `SHA256SUMS.txt` provides checksums for all three downloads.

Keep the complete application folder together. Python is bundled; no Python installation is required.

### Included

- Independent floating timers with synchronized controls and monotonic countdowns.
- Preserved asset, font, stylesheet, and default-configuration folders.
- User-writable timer storage outside protected installation directories.
- Reproducible PyInstaller onedir configuration and native Windows/Arch build workflows.

Both platform builds run automated timer/widget tests and relocated-bundle smoke checks before publication. Linux native desktop interactions were also checked locally. Windows visual/taskbar behavior and display scaling still require manual testing.
