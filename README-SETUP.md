# 🛠️ README-SETUP

Notes for future-you. The profile page is `README.md`; every window card is a
generated SVG in `assets/cards/`, and the rest is a public badge service.

## Regenerate the cards

```bash
python3 tools/build_cards.py      # writes assets/cards/*.svg
```

No dependencies, no build step in the README itself. The script is plain
Python — palette, copy and pixel art all live in that one file.

| Card | File | Size | Used as |
| :-- | :-- | :-- | :-- |
| `readme.md` | `hero.svg` | 1100 × 578 | full-width hero, links to the portfolio |
| `System.tsx` | `system.svg` | 560 × 693 | top-left of the 2×2 grid |
| `Bash.tsx` | `bash.svg` | 560 × 693 | top-right of the 2×2 grid |
| `YAML.tsx` | `yaml.svg` | 560 × 693 | bottom-left of the 2×2 grid |
| `packageJSON.tsx` | `packagejson.svg` | 560 × 693 | bottom-right of the 2×2 grid |
| `builds.sh` | `builds.svg` | 1100 × 560 | Featured Builds, above the project table |
| `arsenal.tsx` | `arsenal.svg` | 1100 × 434 | Arsenal section |

The four tall cards are shown at 50% width inside a `<table>`, which is what
makes them line up as a 2×2 grid on both desktop and mobile.

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
- **ASCII portrait** — a handful of signed-distance shapes (head, jaw,
  shoulders, visor band, headphone cups) sampled per character cell with a
  4×4 Bayer matrix for ordered dithering.
- **Robot** — a hand-typed character map (`FACE`) plus a blinking status LED.
- **Chrome** — one `card()` function draws every window: title bar, traffic
  lights, caption strip and the shadowed `USE →` button.

## Widgets

| Section | Service |
| :-- | :-- |
| Profile views | [hits.sh](https://hits.sh) |
| Stats / top languages | [github-readme-stats](https://github.com/anuraghazra/github-readme-stats) |
| Streak | [streak-stats](https://github.com/DenverCoder1/github-readme-streak-stats) |
| Dev quote | [quotes-github-readme](https://github.com/PiyushSuthar/github-readme-quotes) |
| Contribution snake | [`Platane/snk`](https://github.com/Platane/snk) via [`.github/workflows/snake.yml`](./.github/workflows/snake.yml) |
| Footer wave | [capsule-render](https://github.com/kyechan99/capsule-render) |

## The snake

It renders once the workflow has published to the `output` branch:

> **Actions → 🐍 Contribution Snake → Run workflow**

It then refreshes itself every 12 hours. If the image is missing, that workflow
has not run yet.

## Older assets (kept, unused)

`assets/banner-*.svg`, `assets/bot-*.svg`, `assets/marquee-*.svg` and
`assets/terminal.svg` are the previous hand-written hero art. The README no
longer references them — the window-card style in `assets/cards/` replaced
them — but they are left in the repo in case you want to bring any back.
`assets/divider-*.svg` is still used between sections.
