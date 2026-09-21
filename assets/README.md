# ClockIn design assets

The PNG icons in this directory were extracted from the user-supplied, unmodified
Figma exports in `Codex References/`. They are original design artwork, not
Unicode characters or replacement icon-library drawings. The live Figma tool
was unavailable because its usage quota had been reached, so the exports are
our visual evidence. The exports do not contain Figma typography/effect metadata.

Coordinates below are `(x, y, width, height)` in the source export's logical
pixels. No device-pixel-ratio scaling was applied.

## Icon provenance

| Output | Source export | Source crop | Content |
| --- | --- | --- | --- |
| `play-card.png` | `Setter Page.png` | `(199, 54, 24, 24)` | Grey circle and white play triangle |
| `play.png` | `Setter Page.png` | `(205, 60, 12, 12)` | White play triangle only |
| `pause-button.png` | `States.png` | `(65, 452, 50, 50)` | Dark circle and pause icon |
| `trash-button.png` | `States.png` | `(155, 452, 50, 50)` | Dark circle and trash icon |
| `pause.png` | `States.png` | `(78, 464, 26, 25)` | Pause icon only |
| `trash.png` | `States.png` | `(168, 464, 25, 25)` | Trash icon only |
| `set.png` | `Setter Window.png` | `(164, 219, 15, 16)` | Floppy-disk Set icon |
| `remove.png` | `Timer.png` | `(10, 80, 20, 20)` | Red remove circle and white minus |
| `add.png` | `Button.png` | `(55, 30, 30, 30)` | Add glyph, backing color removed |
| `edit.png` | `Button.png` | `(55, 100, 30, 30)` | Pencil glyph, backing color removed |

Uniform background pixels were made transparent. Antialiased outer pixels were
unblended against the sampled background and known foreground color. The remove
icon overlaps a card edge in the original export; red-channel excess recovers
the red disc's alpha at its outside edge. These are raster crops, so they have
the source export's resolution and are not claimed to be the original vectors.
The full-circle assets preserve the icon positions within their circle.

## Measured geometry and colors

The updated setter bottom buttons occupy `(140,440,100,50)` for edit and
`(260,440,100,50)` for add. Their fills are `#1A1A1A` and `#009DDC`, radius 8,
with centered 30px `#FFFFF3` artwork. Hover uses Qt's `QColor.lighter(110)`.
Per the later user instructions, card shadows are hover-only, removal icons
require edit mode, and buttons have no shadows. The parameter setter is now a
separate, non-modal native top-level window; the content remains `500×300`.

- Setter page: `500×500`, background `#2A2D34`.
- Card rectangles: `(37,40,200,50)`, `(247,40,200,50)`,
  `(37,100,200,50)`. Radius `4`, border `1`, border `#FFFFF3`,
  body `#2A2D34`, text white. Card play bounds relative to its card:
  `(162,14,24,24)`, circle `#464646`.
- Cards have a black drop shadow; raster pixels indicate approximately 25%
  opacity, downward offset and soft edges. Exact Figma blur/offset metadata
  cannot be recovered unambiguously from the image.
- Parameter window: `500×300`, background `#2A2D34`, outer radius about `8`.
- Parameter fields: `(136,143,69,41)`, `(215,143,69,41)`,
  `(294,143,69,41)`, radius `8`, fill `#1A1A1A`.
- Parameter Set button: `(140,209,100,36)`, fill `#13506C`, radius `8`.
- Parameter Cancel button: `(260,209,100,36)`, fill `#1A1A1A`, radius `8`.
  Both have a small dark shadow. Parameter text is `#FFFFF3`.
- Floating default/Idle surface in `States.png`: `(35,62,200,60)`.
  Background `#1A1A1A`, text `#868686`.
- Floating Hover surface: `(35,224,200,58)`. This export genuinely contains
  58 opaque rows, versus 60 in Idle; this is a measured export difference.
  Background `#1A1A1A`, text `#F2F2F2`.
- Floating Clicked/expanded surface: `(0,384,270,130)`, background `#1A1A1A`,
  text `#F2F2F2`. Its circular controls are at relative `(65,68,50,50)` and
  `(155,68,50,50)`, fill `#2A2D34`, glyph fill `#FFFFF3`.
- The floating surfaces have square opaque corners, no border, and no visible
  shadow in this export. Surrounding transparent pixels belong to the export
  canvas. The `Idle`, `Hover`, and `Clicked` labels above the surfaces document
  states; they are not part of the timer window.
- Source floating text sample `5:10:05`: default fully colored glyph bounds
  `(71,79)` through exclusive `(199,107)`; expanded fully colored bounds
  `(59,405)` through exclusive `(213,439)`. Antialiased bounds are slightly wider.

## Fonts and fidelity limits

Exact original font family, weight, size, letter spacing, line height, and
OpenType features cannot be recovered from PNG metadata. The stated 24px bold
setter timer size is supplied by the user. Font comparisons used Qt raster
renders and measured the exported glyphs. No font below is claimed to be a
confirmed original Figma font.

Bundled portable candidates:

- `fonts/AdwaitaSans-Regular.ttf`: unmodified installed Adwaita Sans variable
  font, font metadata version `4.001;git-9221beed3`, based on Inter. It supports
  normal and bold weights. At 24px bold, card sample `00:05:00` has approximately
  the exported 112px ink width and 18px ink height. It gave the best tested card
  pixel-mask overlap (about 81%).
- `fonts/NotoSans-Regular.ttf` and `fonts/NotoSans-Bold.ttf`: unmodified installed
  Noto Sans 2.015. At 39px bold, floating sample `5:10:05` gave the closest tested
  overlap (about 80%), though the original's digit `1` has a different foot.
  These are fallbacks for consistent typography across installations.

Comparison also considered installed Roboto/FreeSans and official Google Fonts
versions of Open Sans, Lato, Ubuntu, Source Sans 3, Roboto Condensed, and Inter.
Open Sans is bundled for the parameter dialog: its 24px bold heading matches
the source's 214px ink width. Its OFL notice accompanies `fonts/OpenSans.ttf`.
Other comparison downloads are not included. The actual implementation uses
Adwaita Sans 24px bold for cards, Noto Sans 40/48px bold for floating timers,
Open Sans for the parameter dialog, and Roboto with bundled fallbacks for menus.
For the small floating sample,
Roboto at 39px bold scored about 73%, Lato 39px about 73%, and Open Sans 39px about
68%; none resolved the original font identity. At 24px bold, installed Roboto's
card sample is only about 94px wide, materially narrower than the source.

The bundled files came from `/usr/share/fonts/Adwaita/` and
`/usr/share/fonts/noto/`. Their SIL Open Font License 1.1 notices are bundled in
`fonts/AdwaitaSans-LICENSE.txt` and `fonts/NotoSans-LICENSE.txt`. The Adwaita notice
came from the installed `adwaita-fonts` package. Noto's license was retrieved from
its official upstream because the system package's generic license did not
match these individual font files' embedded OFL metadata:

- <https://gitlab.gnome.org/GNOME/adwaita-fonts>
- <https://github.com/notofonts/latin-greek-cyrillic>
- <https://raw.githubusercontent.com/notofonts/latin-greek-cyrillic/main/OFL.txt>
- Comparison fonts: <https://github.com/google/fonts>
