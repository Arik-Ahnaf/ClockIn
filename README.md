# ClockIn

A Python / PySide6 desktop timer with a fixed-size setter and independently
draggable floating timers. Countdown state is shared between both views; all
visual changes are immediate, with no animations.

## Run

Requires Python 3.14+ and a desktop session.

```sh
uv sync --locked
uv run python main.py
```

Alternatively, create a Python virtual environment, install `PySide6>=6.11.2`,
and run `python main.py` from this directory.

On Linux, ClockIn selects Qt's `xcb` backend when an X11/XWayland display is
available. This supports the required arbitrary global-position dragging; native
Wayland restricts client positioning. An explicitly supplied `QT_QPA_PLATFORM`
is respected. Install your distribution's XWayland and Qt xcb runtime libraries
if needed. Windows and macOS use Qt's native default backend.

## Use

- The setter loads its timers from `timers.json` every time the app starts.
  First launch creates an empty database; add your own timers with the add button.
- The bottom **add** button, **Settings → New timer**, or **Ctrl+N**, opens a
  separate, non-modal parameter setter window with native window controls. Hours are
  0–99; minutes and seconds are 0–59. A duration must be at least one second.
- Click a card's time to configure it. Reconfiguration returns that timer to idle.
- Click its play icon to start/resume it and show its floating window. Reopening
  an already running timer preserves its countdown and reuses the same window.
- Toggle the bottom **edit** button to show or hide card removal controls.
  Hovering a card adds its shadow, but does not expose removal controls.
  Right-click a card for edit/reset/remove.
- Buttons brighten by 10% while hovered, without shadows. The menu uses 20px text.
- Drag any floating timer text/background. Pressing immediately uses the expanded
  dragging appearance; moving uses the original global pointer-to-window offset.
- Click the floating surface to toggle the expanded pause/delete controls. This
  follows the approved interpretation of the reference's **Clicked** state.
  Buttons consume their own input and never initiate a drag.
- **Space** pauses/resumes a focused floating timer; **Delete** removes it;
  **Escape** collapses its controls or hides the compact window. Its context menu
  also provides pause/resume, reset, hide, and delete.
- Hiding/closing a floating window leaves its countdown running. Deleting a timer
  stops only that timer. Closing the setter closes the application.

Timer additions, duration changes, and deletions are saved immediately to
`timers.json` beside `main.py`, independent of the working directory used to launch
the app. Timer IDs and display order survive restarts. Saved timers reopen idle
at their configured duration; in-progress countdowns and floating positions are
not restored. The database is local and ignored by Git.

The file has this structure (durations are whole seconds):

```json
{
  "version": 1,
  "timers": [
    {"timer_id": "my-timer", "duration_seconds": 300}
  ]
}
```

The initial file contains an empty `timers` list. Each ID must be unique and
non-empty; durations range from 1 to 359999 seconds. You can edit the file while
ClockIn is closed, then relaunch to load your changes. Invalid or unreadable
databases show an error and are left intact. Saves replace the file atomically;
if saving fails, the requested add/edit/delete is not applied. Countdown refreshes
do not write to disk. No network, account, or storage service is used.

## Design and assets

Source: [ClockIn in Figma](https://www.figma.com/design/LM69kzqt9dczj66SLtcRjg/ClockIn?node-id=101-2).
The Figma MCP request returned a plan quota error, so implementation uses the
provided `Codex References/` exports. Geometry and colors were measured from
those files; icon artwork is extracted directly from them, not replaced with
Unicode symbols. Asset provenance and font limitations are documented in
[`assets/README.md`](assets/README.md).

| Surface | Logical pixels |
| --- | --- |
| Setter client area | 500 × 500 |
| Timer cards | 200 × 50, radius 4 |
| Parameter dialog | 500 × 300 |
| Compact floating timer | 200 × 60 |
| Hover painted surface | 200 × 58 |
| Expanded / dragging floating timer | 270 × 130 |

The hover export is two pixels shorter than idle. Its painted surface follows
the export while retaining the compact 200 × 60 native hit area, with transparent
bottom rows, to avoid repeated enter/leave events at the bottom edge. Floating
surfaces in the supplied exports have square corners; the configuration dialog
has rounded transparent corners. Qt handles display scaling; measurements are
never manually multiplied by a device pixel ratio.

The bottom section follows the updated Setter Page and Button exports: edit at
`(140,440)` and add at `(260,440)`, each `100×50` with 30px artwork. Additional
timers scroll above this fixed section, preserving card dimensions and spacing.

## Structure

```text
ClockIn/
├── main.py
├── models/
├── controllers/
├── windows/
├── widgets/
├── utils/
├── assets/
├── tests/
└── scripts/
```

- `models/timer_model.py`: explicit idle/running/paused/finished lifecycle and a
  monotonic deadline. Published snapshots keep the two displays synchronized.
- `controllers/timer_controller.py`: a 50 ms `QTimer` refreshes the model only
  while running. Refresh frequency never determines elapsed time.
- `utils/timer_store.py`: validates timer definitions and reads/writes the local
  JSON database using atomic replacement.
- `windows/setter_window.py`: owns models/controllers, cards, and floating windows
  in dictionaries keyed by timer identity.
- `windows/floating_timer_window.py`: native utility flags, explicit visual state
  priority (`DRAGGING > HOVER > DEFAULT`), mouse capture, and global-offset drag.
- `windows/timer_dialog.py`, `widgets/`, `utils/`, `assets/`: configuration,
  reusable controls, centralized design values, and artwork/fonts.

## Verify

```sh
QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v
```

Tests cover delayed refreshes, exact finish deadlines, pause/resume, independent
timers, shared views, lifecycle cleanup, fixed dimensions, and input state
regressions. Offscreen Qt may log unsupported window-manager operations; use the
native check for actual stacking and pointer behavior.

On an X11/XWayland desktop with `libX11`, `libXtst`, and `xprop`:

```sh
QT_QPA_PLATFORM=xcb uv run python scripts/validate_desktop.py
```

This check temporarily creates test windows, moves the pointer, exercises real
mouse input, and verifies native stacking against a separate application
process. It restores the pointer and closes its test windows when complete.
Other operating systems still require their own native window-manager checks.

Validated on KDE Wayland through XWayland at 125% display scaling: 37 automated
tests and 53 native desktop checks passed. Native stacking confirms the floating
timer remains above an active normal window in another process. Root-framebuffer
capture is unavailable through this XWayland session, so that screenshot check
is explicitly skipped; per-widget screenshots and native stacking are available.
