# ClockIn design assets

The current setter, parameter dialog, and V2 timer match the live Figma file
`LM69kzqt9dczj66SLtcRjg`, inspected November 15, 2026. Local images in
`Codex References/` provide additional visual references. Figma pixels map to
Qt logical pixels without manual device-pixel-ratio multiplication.

## Current artwork

| Asset | Figma source / use | Logical size |
| --- | --- | --- |
| `fa-clock.svg` | Setter timer tab, 155:23 | 24×24 |
| `fa-stopwatch.svg` | Deferred stopwatch tab | 21×25 |
| `fa-cog.svg` | Setter settings, 152:2651 | 23×24 |
| `play-btn.svg` | Timer card play control, 91:25 | 24×24 |
| `setter-edit.svg` | Toolbar pencil, 165:27 | 23×24 |
| `setter-add.svg` | Toolbar add, 165:30 | 24×24 |
| `dialog-save-button.svg` | Parameter save button, 23:45 | 110×46 including shadow |
| `dialog-cancel-button.svg` | Parameter cancel button, 23:47 | 110×46 including shadow |
| `v2-play.svg` | Expanded timer play, 196:30 | 36×36 |
| `v2-pause.svg` | Expanded timer pause, 196:29 | 36×36 |
| `v2-close-first.svg`, `v2-close-second.svg` | Cancel diagonals, 197:12–13 | 15×15 each, overlaid in a 24×24 control |

The new setter/dialog/V2 exports are unmodified Figma SVGs. The supplied 86px
`fa-play-circle.svg` and `fa-pause-circle.svg` are retained for future stopwatch
work; V2 uses the exact 36px exports instead. Supplied raster icons and older
artwork remain available, but the revamped UI does not depend on removed icons.
The edit-card remove button uses native shapes: a 20px red circle and 8×3px minus,
as specified by Figma node 78:16.

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
