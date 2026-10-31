# 🛠️ README-SETUP

Notes for future-you. The profile page is `README.md`, which is three
generated SVGs and a badge row — nothing else.

## Regenerate the cards

```bash
python3 tools/build_cards.py      # writes assets/cards/*.svg
```

No dependencies, no build step in the README itself. The script is plain
Python — palette, copy and pixel art all live in that one file.

| Card | File | Size | Used as |
| :-- | :-- | :-- | :-- |
| `readme.md` | `hero.svg` | 1100 × 578 | full-width hero, links to the portfolio |
| `System.tsx` | `system.svg` | 760 × 833 | full-width spec sheet, links to the portfolio |
| `arsenal.tsx` | `arsenal.svg` | 1100 × 418 | Arsenal section, links to the repo list |

Every card is shown at `width="100%"`, so the README is one column of cards on
any screen. That is the whole layout — no table, no grid.

## The palette (change it in one place)

| Token | Hex | Used for |
| :-- | :-- | :-- |
| panel | `F8F6F0` | window chrome + title bar |
| caption | `F0ECE1` | caption strip under each card |
| hairline | `DBD5C6` | 1px borders |
| ink | `12151A` | window titles, captions |
| lime | `E6FA4B` | the `USE →` button |
| pane | `080C12` | code pane background |
| mint | `00E5A0` | primary accent, keys, highlights |
| cyan | `22D3EE` | secondary accent, values |
| paper | `ECF8F4` | bright text / pixel robot shell |
| signal | `FF4D8D` | the single hot accent (comet, eyes, LED) |

Badges in the body of the README still follow the older rule: every
`img.shields.io` badge passes `labelColor=05080D` and one of the two accents.

## How the art is made

- **Pixel bands** — a tiny `Canvas` grid of cells written out as `<rect>`s.
  `nebula()` draws dithered metaballs over a starfield; `band_night()` draws the
  crimson moon; `band_sigils()` draws the mirrored identicon strip.
- **ASCII portrait** — the System card draws a bust out of signed-distance
  shapes (head, jaw, neck, trapezoid torso, visor band, headphone cups),
  sampled per character cell with a 4×4 Bayer matrix for ordered dithering.
- **Neofetch rows** — label on the left, value right-aligned, and a dot leader
  filling the gap; a dot that would land on the value is dropped instead of
  overlapping it.
- **Chrome** — one `card()` function draws every window: title bar, traffic
  lights, caption strip and the shadowed `USE →` button.

## Widgets

| Section | Service |
| :-- | :-- |
| Profile views | [hits.sh](https://hits.sh) |

That is the only external widget left. `.github/workflows/snake.yml` still
runs, but nothing displays its output — delete the workflow if you want the
`output` branch to stop updating.

## Older assets (kept, unused)

`assets/banner-*.svg`, `assets/bot-*.svg`, `assets/marquee-*.svg` and
`assets/terminal.svg` are the previous hand-written hero art, left in the repo
in case you want to bring any back. `assets/divider-*.svg` is still used
between sections.
