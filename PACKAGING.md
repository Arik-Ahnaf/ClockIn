# Building ClockIn

Build on the target OS: Windows x64 for Windows, Arch Linux x86_64 for Arch.
PyInstaller is not a cross-compiler. A Windows executable cannot be produced or
natively verified by the Linux build. Use the committed **Build distributions**
GitHub Actions workflow for separate native builds and downloadable artifacts;
it runs manually or on a `v*` tag. Tag builds publish a GitHub release with
Windows and Linux archives, an Arch package, and SHA-256 checksums only after
both platform builds and their verification steps pass. Manual runs only build
artifacts.

## Dependencies

Install `uv`; `.python-version` selects Python 3.14.7. The runtime dependency is PySide6; PyInstaller is
in the separate `build` dependency group. `uv.lock` pins runtime and build
packages, including transitive dependencies and wheel hashes. The scripts use
`--locked` and build with that environment's interpreter. No Pillow, alternate
Qt binding, or other packaging framework is needed.

```sh
uv sync --locked --group build
uv run --no-sync python build.py
```

After activating the same environment, `python build.py` works too. For a bare
onedir build without archives/Arch recipe generation:

```sh
pyinstaller --noconfirm --clean ClockIn.spec
```

`build.py` works from any current directory. It checks the required files in
`packaging/resources.json` before cleaning its own temporary output, runs the
committed spec, verifies inclusion, and writes the folder and archive to `dist/`.
Add new required assets to that manifest. All files under `assets/`, `styles/`,
and `defaults/` are collected automatically. Files outside these folders, such
as your personal root `timers.json`, are not distributed.

## Windows

From PowerShell:

```powershell
./packaging/windows/build.ps1
```

This builds and verifies the relocated distribution. Deliver the generated
`dist/ClockIn-0.1.1-windows-x86_64.zip`, or the entire `dist/ClockIn/` folder.
Extract the ZIP before launching `ClockIn.exe`. Python is included; the recipient
needs no Python installation. `console=False` selects the Windows GUI subsystem,
and the spec embeds `assets/logo.ico` into the executable. Qt also uses this icon
at runtime. The icon was converted from the existing `assets/Logo.png`.

## Arch Linux

Install the build tools (`base-devel`, Python, `uv`) and the desktop dependencies
listed in `packaging/arch/PKGBUILD.in`. Use X11 or XWayland for native dragging.
Build as a regular user:

```sh
./packaging/arch/build.sh
```

This builds the same onedir application, verifies it, then runs `makepkg`.
`build.py` generates `dist/arch/PKGBUILD` from the committed template and fills in
the version, archive name, and SHA-256 of the actual build. The result is
`dist/arch/clockin-0.1.1-1-x86_64.pkg.tar.zst`. Install it with:

```sh
sudo pacman -U dist/arch/clockin-0.1.1-1-x86_64.pkg.tar.zst
```

Installation places the complete distribution in `/opt/clockin`, adds a
`/usr/bin/clockin` symlink, and installs a desktop entry and icon. No Python
package is needed at runtime. Alternatively distribute the generated `.tar.gz`
and launch the extracted `ClockIn/ClockIn` directly. Preserve symlinks when
copying Linux distributions (for example `cp -a`). The archive preserves them.
Arch builds target current Arch; they are not promised to run on older Linux
systems with older glibc. The rolling OS baseline can change even with locked
Python packages; this is a repeatable build process, not a byte-identical build.

## Runtime layout and persistence

```text
ClockIn/
├── ClockIn.exe                  # ClockIn on Linux
├── assets/
│   ├── logo.ico
│   ├── Logo.png
│   ├── fonts/
│   └── ...
├── styles/
│   ├── main.qss
│   └── menu.qss
├── defaults/
│   └── timers.json
├── PySide6/                     # Qt binaries/plugins collected by hooks
└── ...                         # Python and platform runtime libraries
```

The spec uses `COLLECT`, `exclude_binaries=True`, and
`contents_directory="."` to preserve this onedir layout. Never distribute only
the executable. No resources are embedded into Python constants or Qt resource
modules. Existing procedural painting remains in the widget code; external QSS
files preserve the existing appearance.

`utils/paths.py` is the only resource-location boundary. Source runs resolve from
the module location; frozen runs resolve from the executable location, including
when launched through `/usr/bin/clockin`. Neither uses the shell's working
directory. UI modules and timer logic contain no PyInstaller detection.

There is no `settings.json` in the existing product. Its persisted configuration
is `timers.json`. The shipped `defaults/timers.json` remains a normal, read-only
input; user edits never overwrite it. Storage locations are:

| Run | Writable timer database |
| --- | --- |
| Windows, source or bundle | `%LOCALAPPDATA%/ClockIn/timers.json` |
| Linux bundle | `$XDG_DATA_HOME/ClockIn/timers.json`, normally `~/.local/share/ClockIn/timers.json` |
| Linux source | `timers.json` beside `app.py`, preserving development behavior |

On first use of the user-data location, a legacy `timers.json` beside the
application is validated and imported without modifying the original. Existing
user data always wins. Otherwise the empty shipped defaults initialize the user
database. Writes remain atomic. Protected installation directories never need
to be writable.

## Verification

```sh
QT_QPA_PLATFORM=offscreen uv run --no-sync python -m unittest discover -s tests -v
uv run --no-sync python app.py --smoke-test /tmp/clockin-source.json
uv run --no-sync python scripts/verify_distribution.py
uv run --no-sync python scripts/verify_distribution.py --native
```

For Windows source smoke checks, use a writable Windows report path, for example
`$env:TEMP/clockin-source.json`. The verifier defaults to offscreen Qt; `--native`
uses a desktop session. The smoke mode saves only temporary test timers and
reports resource/font/icon loading, exact setter size, shared countdowns,
pause/resume/finish, and persistence.

The distribution verifier copies the bundle into a temporary directory and
runs it from an unrelated working directory with Python/Qt search overrides
removed. On Linux with Bubblewrap installed it also hides the entire source tree
and mounts the copied distribution read-only. It reports whether this isolation
was performed. On Windows it checks the PE GUI subsystem to catch console builds.
Evidence is written to `build/verification/bundle-smoke.json`.

Before releasing on Windows, also launch `ClockIn.exe` on a clean Windows
machine and check Explorer/taskbar icons, absence of a console, floating-window
stacking over another application, dragging, and DPI scaling. CI/offscreen checks
do not establish those desktop behaviors. Linux native input/stacking checks
remain available through `scripts/validate_desktop.py`.

PyInstaller's built-in PySide6 hooks collect the imported Qt modules and plugins;
there are no manually copied Qt DLLs, collect-all calls, exclusions, or hidden
imports. If a future dependency needs a hook, document the concrete reason in the
spec. See [PyInstaller spec files](https://pyinstaller.org/en/stable/spec-files.html)
and [onedir layout options](https://pyinstaller.org/en/stable/usage.html).

## Verification in this workspace (2026-09-23)

- 48 unit/widget tests passed on Arch Linux.
- Source launch from `/tmp` passed 31 smoke checks on the native desktop.
- Relocated onedir launch passed 32 smoke checks with its source tree hidden and
  installation read-only; native launch produced no stderr output.
- Normal packaged startup initialized the actual XDG user database while the
  installation remained read-only. Missing-resource build preflight also failed
  clearly as intended.
- The existing native desktop suite passed 53 checks on retry, including dragging,
  pause/resume, independent timers, and stacking above an unrelated active app.
  The first attempt was interrupted by a pointer-position mismatch. XWayland
  framebuffer capture remains unavailable and was explicitly skipped.
- `makepkg` produced the Arch package and its archive contents were inspected.
- Windows build/GUI verification requires the Windows workflow or a Windows
  machine; neither has been executed from this Linux workspace.
