# ClockIn design assets

The current setter, parameter dialog, and V2 timer match the live Figma file
`LM69kzqt9dczj66SLtcRjg`, inspected November 15, 2026. Local images in
`Codex References/` provide additional visual references. Figma pixels map to
Qt logical pixels without manual device-pixel-ratio multiplication.

## Current artwork

| Asset | Figma source / use | Logical size |
| --- | --- | --- |
| `fa-clock.svg` | Setter timer tab, 155:23 | 24×24 |
| `fa-stopwatch.svg` | Inactive stopwatch tab | 21×25 |
| `fa-cog.svg` | Setter settings, 152:2651 | 23×24 |
| `play-btn.svg` | Timer card play control, 91:25 | 24×24 |
| `setter-edit.svg` | Toolbar pencil, 165:27 | 23×24 |
| `setter-add.svg` | Toolbar add, 165:30 | 24×24 |
| `save-btn.svg` | Parameter save button icon | 25×25 |
| `dialog-cancel-button.svg` | Parameter cancel button, 23:47 | 110×46 including shadow |
| `v2-play.svg` | Expanded timer play, 196:30 | 36×36 |
| `v2-pause.svg` | Play/pause toggle while running | 36×36 |
| `reset-btn.svg` | Stop and reset countdown | 36×36 |
| `remove-btn.svg` | Remove timer, including shadow | 32×32 |
| `cancel-btn.svg` | Floating timer close/reset icon | 15×15, centered in a 24×24 control |

Controls use local SVG artwork. The remaining PNG checkmark is used by settings and menus; the application icon uses ICO. Unused legacy icons have been removed.

## Typography and colors

- IBM Plex Sans: setter/card text and parameter dialog, using explicit `wght`
  and `wdth` axes. Qt's synthetic bold is disabled for this variable font.
- IBM Plex Sans Condensed Bold: V2 countdown (40px) and objective (14px).
- Font sources: Google Fonts' `ofl/ibmplexsans` and `ofl/ibmplexsanscondensed`
  directories. Each bundled font has its adjacent SIL Open Font License file.
- Other bundled fonts are retained for existing application surfaces.
- Background `#282A36`, foreground `#EDEDDE`, neutral `#6272A4`, accent `#BD93F9`,
  objective `#D6C2D6`, error `#FF5555`.
- V2 compact/hovered size: 270×80; expanded: 300×120; corner radius: 8px.
  Minimized opacity is 70% for the whole native window when transparency is enabled.

Resources are resolved relative to the application directory through
`utils.paths.resource_path`; `packaging/resources.json` inventories the shipped
files. No runtime Figma URLs are used.

Stopwatch Page (`179:36`): `stopwatch-play.svg` (`191:17`) and
`stopwatch-pause.svg` (`191:19`) are 86×86 exports. The active stopwatch tab
(`179:43`) and inactive timer tab (`179:42`) are separate local exports.
Elapsed time uses IBM Plex Sans SemiBold, 96px, weight axis 600.

Stopwatch Widget (`213:68`, inspected November 20, 2026): idle/hover are
200×60; expanded/dragging is 220×100. The 40px IBM Plex Sans Condensed Bold
elapsed display uses hours:minutes:seconds. Idle opacity is 70%; hover and
expanded are opaque. The existing 36×36 `v2-play.svg` and `reset-btn.svg`
render identically to exports `213:74` and `213:75`; `stopwatch-close.svg` is
exported from `213:87`. Controls start at (69,52) and (115,52); the close
icon is at (178,6) in idle and (196,8) when expanded, and hidden in hover.
The stray close layer above the expanded frame is outside the window bounds.
