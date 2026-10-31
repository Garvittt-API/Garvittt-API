#!/usr/bin/env python3
"""
Build the window cards used by README.md  ->  assets/cards/*.svg

Look: paper-coloured macOS window, dark code pane, a dithered pixel band,
and a caption strip with a lime "USE ->" button. Everything is plain SVG —
no external services, no build step in the README.

    python3 tools/build_cards.py

Two card sizes:
    wide   1100 px  -> hero, builds, arsenal (shown full width)
    tall    560 px  -> the 2x2 grid (shown at ~46% width, two per row)
"""

import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "cards"

# ── palette ─────────────────────────────────────────────────────────────────
MONO = ("'JetBrains Mono', ui-monospace, SFMono-Regular, 'SF Mono', Menlo, "
        "Consolas, 'Liberation Mono', monospace")
SANS = ("Inter, 'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, "
        "sans-serif")

PAPER = "#F8F6F0"
PAPER_2 = "#F0ECE1"
HAIRLINE = "#DBD5C6"
INK = "#12151A"
INK_SOFT = "#5C574B"
INK_DIM = "#9A9483"
LIME = "#E6FA4B"

PANE = "#080C12"
MINT = "#00E5A0"
CYAN = "#22D3EE"
TEXT = "#C4D5DA"
DIM = "#5C7382"
FAINT = "#22303A"
WHITE = "#ECF8F4"
MAGENTA = "#FF4D8D"
AMBER = "#F3C64B"
VIOLET = "#7C6BFF"
BLUE = "#2E7FD4"
CRIMSON = "#B81745"

HEAD_H = 44
FOOT_H = 74
RADIUS = 13
NBSP = "&#160;"

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(gx, gy):
    return BAYER[gy % 4][gx % 4] / 16.0 - 0.5


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace(" ", NBSP))


def cw(size):
    """advance width of one monospace glyph"""
    return size * 0.6


# ── primitives ──────────────────────────────────────────────────────────────
def text(x, y, s, size=13, fill=TEXT, weight=400, family=MONO, anchor="start",
         ls=None, opacity=None):
    a = [f'x="{x:g}"', f'y="{y:g}"', f'font-family="{family}"', f'font-size="{size:g}"',
         f'fill="{fill}"']
    if weight != 400:
        a.append(f'font-weight="{weight}"')
    if anchor != "start":
        a.append(f'text-anchor="{anchor}"')
    if ls:
        a.append(f'letter-spacing="{ls}"')
    if opacity is not None:
        a.append(f'opacity="{opacity}"')
    return f'<text {" ".join(a)}>{esc(s)}</text>'


def runs(x, y, segs, size=13, weight=400, family=MONO):
    """coloured segments on one mono line; x advances by character count"""
    out, cx = [], x
    for t, color in segs:
        if t:
            out.append(text(round(cx, 2), y, t, size, color, weight, family))
            cx += len(t) * cw(size)
    return "".join(out)


def leader(x1, x2, y, color=FAINT, w=1.3):
    if x2 <= x1:
        return ""
    return (f'<line x1="{x1:g}" y1="{y:g}" x2="{x2:g}" y2="{y:g}" stroke="{color}" '
            f'stroke-width="{w}" stroke-dasharray="2 4" stroke-linecap="round"/>')


def kv(y, label, value, x0, x1, size=13, label_c=MINT, value_c=TEXT, weight=400):
    vx = x1 - len(value) * cw(size)
    return "".join([
        text(x0, y, label, size, label_c, weight),
        leader(x0 + len(label) * cw(size) + 7, vx - 10, y - 4),
        text(x1, y, value, size, value_c, weight, anchor="end"),
    ])


def pill(x, y, label, color=MINT, size=11, pad=8, h=20):
    w = len(label) * cw(size) + pad * 2
    return "".join([
        f'<rect x="{x:g}" y="{y:g}" width="{w:.1f}" height="{h}" rx="{h/2}" '
        f'fill="{color}" fill-opacity=".10" stroke="{color}" stroke-opacity=".45"/>',
        text(x + pad, y + h - 6.5, label, size, color, 500),
    ])


def star_path(cx, cy, r, color):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * .44
        pts.append(f"{cx + rr*math.cos(ang):.2f},{cy + rr*math.sin(ang):.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{color}"/>'


def button(x, y, label="USE", w=92, h=30):
    return "".join([
        f'<rect x="{x+3}" y="{y+3}" width="{w}" height="{h}" rx="4" fill="{INK}"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{LIME}" '
        f'stroke="{INK}" stroke-width="1.4"/>',
        text(x + 13, y + h - 10, label, 11.5, INK, 700, ls="1.1"),
        f'<path d="M{x+w-28} {y+h/2} h13 m-4.5 -4.5 4.5 4.5 -4.5 4.5" stroke="{INK}" '
        f'stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
    ])


# ── pixel canvas ────────────────────────────────────────────────────────────
class Canvas:
    """tiny pixel grid -> <rect>s; later draws win"""

    def __init__(self, x0, y0, cols, rows, cell):
        self.x0, self.y0, self.cols, self.rows, self.cell = x0, y0, cols, rows, cell
        self.px = {}

    def __call__(self, gx, gy, color):
        if color and 0 <= gx < self.cols and 0 <= gy < self.rows:
            self.px[(gx, gy)] = color

    def sky(self, top, steps=3, seed=0, noise=.2):
        rng = random.Random(seed)
        t = [int(top[i:i + 2], 16) for i in (1, 3, 5)]
        for gy in range(self.rows):
            for gx in range(self.cols):
                if (gx, gy) in self.px:
                    continue
                if rng.random() < noise:
                    self(gx, gy, top)

    def stars(self, points, colors=(WHITE, "#9FD9E8", "#5B7488"), seed=3):
        rng = random.Random(seed)
        for p in points:
            self(p[0], p[1], rng.choice(colors))

    def sparkle(self, gx, gy, size=1, color=WHITE, arm=CYAN):
        self(gx, gy, color)
        for i in range(1, size + 1):
            for (dx, dy) in ((i, 0), (-i, 0), (0, i), (0, -i)):
                if (gx + dx, gy + dy) not in self.px:
                    self(gx + dx, gy + dy, arm if i == size else color)

    def to_svg(self):
        return "".join(
            f'<rect x="{self.x0 + gx*self.cell:g}" y="{self.y0 + gy*self.cell:g}" '
            f'width="{self.cell}" height="{self.cell}" fill="{c}"/>'
            for (gx, gy), c in self.px.items())


def starfield(cols, rows, density=.10, seed=3):
    rng = random.Random(seed)
    pts = {(rng.randrange(cols), rng.randrange(rows))
           for _ in range(int(cols * rows * density))}
    for gx in range(3, cols, max(6, cols // 14)):
        pts.add((gx, 1))
    return pts


def nebula(x0, y0, cols, rows, cell=8, palette=None, seed=4, density=1.0,
           blobs=None, base="#070A10"):
    """abstract dithered nebula: metaballs of light over a starfield"""
    palette = palette or ["#071A24", "#0A2C3A", "#0D4353", "#10606F", "#16818C",
                          "#1FA3A8", CYAN, "#7FEDDF", MINT]
    cv = Canvas(x0, y0, cols, rows, cell)
    rng = random.Random(seed)
    cv.sky(base, noise=.26)
    cv.stars(starfield(cols, rows, .09, seed=seed + 1))
    if blobs is None:
        blobs = []
        for _ in range(max(6, int(cols / 9 * density))):
            blobs.append((rng.uniform(-2, cols + 2), rng.uniform(-.3, 1.3) * rows,
                          rng.uniform(rows * .45, rows * 1.10)))
    for gy in range(rows):
        for gx in range(cols):
            f = 0.0
            for (bx, by, br) in blobs:
                d2 = ((gx - bx) ** 2 + ((gy - by) * 1.25) ** 2) / (br * br)
                f += math.exp(-d2 * 1.9)
            f *= .80 + .20 * math.sin(gx * .42 + math.cos(gy * .30) * 2.2)
            v = f + bayer(gx, gy) * .30 + (rng.random() - .5) * .08
            if v < .30:
                continue
            cv(gx, gy, palette[min(len(palette) - 1, int(min(.999, (v - .30) * 1.05)
                                                     * len(palette)))])
    return cv


def band_nebula(x0, y0, cols, rows, cell=8, seed=7, accent=True):
    cv = nebula(x0, y0, cols, rows, cell, seed=seed,
                density=1.3 if cols > 80 else 1.0)
    cv.sparkle(int(cols * .06), 1, 1, WHITE)
    if accent:
        hx = int(cols * .52)
        for i in range(4):
            cv(hx - i, 1 + i // 2, MAGENTA if i == 0 else ("#A81E55" if i < 2 else "#5E1030"))
    return cv.to_svg()


def band_night(x0, y0, cols, rows, cell=10):
    """crimson sky, amber moon, three bats"""
    cv = Canvas(x0, y0, cols, rows, cell)
    rng = random.Random(9)
    for gy in range(rows):
        t = gy / max(1, rows - 1)
        idx = min(3, int(t * 4))
        col = ["#1B0610", "#2C0813", "#430B18", "#5C0F1E"][idx]
        for gx in range(cols):
            if rng.random() < .22:
                cv(gx, gy, col)
    for _ in range(int(cols * rows * .10)):
        cv(rng.randrange(cols), rng.randrange(rows),
           rng.choice(["#F2C2CD", "#B4707F", "#6B3341"]))
    cx, cy, r = cols * .68, rows * .50, rows * .42
    for gy in range(rows):
        for gx in range(cols):
            dx, dy = (gx + .5 - cx) / r, (gy + .5 - cy) / r
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            nz = math.sqrt(max(0, 1 - d2))
            lit = dx * -.55 + dy * -.85 + nz * .62
            c = "#F3C64B"
            if lit > .95:
                c = "#FCEBAE"
            elif lit < .28:
                c = "#C9932A"
            if d2 > .82 and lit < .35 and rng.random() < .5:
                c = "#C9932A"
            cv(gx, gy, c)
    for (dx, dy, rr) in [(-.40, -.05, .55), (.18, .30, .75), (.12, -.44, .42), (.55, -.10, .38)]:
        for gy in range(rows):
            for gx in range(cols):
                if math.hypot(gx + .5 - (cx + dx * r), gy + .5 - (cy + dy * r)) <= rr:
                    cv(gx, gy, "#C9932A")
    BAT = ["X.....X", ".X...X.", "..X.X..", "XX.X.XX", ".X...X."]
    for (bx, by) in [(int(cols * .05), 1), (int(cols * .22), 5), (int(cols * .86), 6)]:
        for rr, row in enumerate(BAT):
            for c, ch in enumerate(row):
                if ch == "X":
                    cv(bx + c, by + rr, "#0E0409")
    return cv.to_svg()


def band_robot(x0, y0, cols, rows, cell=8):
    """crimson nebula; the pixel bot is stamped on top by the caller"""
    cv = nebula(x0, y0, cols, rows, cell, seed=31, base="#08060B",
                palette=["#1B0713", "#330A1C", "#5A0E28", "#8A1136", "#B81745",
                         MAGENTA, "#FF8FB4", WHITE])
    return cv.to_svg()


FACE = [
    "....#####....",
    "..#########..",
    ".###########.",
    "#####...#####",
    "##.......###.",
    "##.......###.",
    "#####...#####",
    ".###########.",
    "..###.#.###..",
    "...#..#..#...",
    "....#...#....",
]


def robot_face(cx, y, cell=8):
    """chunky pixel bot head: white shell, dark visor, lit eyes"""
    out = []
    w = len(FACE[0]) * cell
    x = cx - w / 2
    shell, shade = "#F7F2EB", "#DCD2C7"
    for r, row in enumerate(FACE):
        for c, ch in enumerate(row):
            if ch != "#":
                continue
            out.append(f'<rect x="{x + c*cell:g}" y="{y + r*cell:g}" width="{cell}" '
                       f'height="{cell}" fill="{shell}"/>')
    out.append(f'<rect x="{x + 2*cell:g}" y="{y + 3*cell:g}" width="{cell*7}" height="{cell*4}" fill="#14070C"/>')
    for ex in (3, 7):
        out.append(f'<rect x="{x + ex*cell:g}" y="{y + 4*cell:g}" width="{cell}" height="{cell}" fill="{WHITE}"/>')
        out.append(f'<rect x="{x + ex*cell:g}" y="{y + 5*cell:g}" width="{cell}" height="{cell}" fill="{MAGENTA}"/>')
    out.append(f'<rect x="{x + 5*cell:g}" y="{y - 2*cell:g}" width="{cell}" height="{cell*2}" fill="{shade}"/>')
    out.append(f'<rect x="{x + 5*cell:g}" y="{y - 3*cell:g}" width="{cell}" height="{cell}" fill="{MAGENTA}">'
               f'<animate attributeName="opacity" values="1;.2;1" dur="2.2s" repeatCount="indefinite"/></rect>')
    out.append(f'<rect x="{x + 4*cell:g}" y="{y + 11*cell:g}" width="{cell*3}" height="{cell}" fill="{shade}"/>')
    return "".join(out)


def band_sigils(x0, y0, cols, rows, cell=10, seed=23):
    """a strip of mirrored pixel sigils, one per tile"""
    rng = random.Random(seed)
    pal = [(MINT, "#06362A"), (CYAN, "#062C3A"), (MAGENTA, "#330817"),
           (AMBER, "#33270A"), (VIOLET, "#150E33"), (WHITE, "#0E2A33")]
    w = cols * cell
    out = [f'<rect x="{x0}" y="{y0}" width="{w}" height="{rows*cell}" fill="#0A1017"/>']
    size = 4
    span = size * cell + 12
    n = max(1, (w - 10) // span)
    left = x0 + (w - n * span) // 2 + 5
    for i in range(n):
        fg, bg = rng.choice(pal)
        gx = left + i * span
        gy = y0 + (rows * cell - size * cell) // 2
        out.append(f'<rect x="{gx-4}" y="{gy-4}" width="{size*cell+8}" height="{size*cell+8}" '
                   f'fill="{bg}" stroke="{HAIRLINE}" stroke-opacity=".16"/>')
        half = (size + 1) // 2
        for r in range(size):
            for c in range(half):
                if rng.random() > .40:
                    for cc in ((c,) if c == size - 1 - c else (c, size - 1 - c)):
                        out.append(f'<rect x="{gx + cc*cell}" y="{gy + r*cell}" width="{cell}" '
                                   f'height="{cell}" fill="{fg}"/>')
    return "".join(out)


# ── ASCII portrait ──────────────────────────────────────────────────────────
LEVELS = " .:-=+*#%@"


def ascii_portrait(x, y, cols, rows, ch=7.6, lh=8.2, size=8.0):
    """dithered duotone bust — big hood, dark visor, headphone cups, shoulders"""
    out = []

    def shade(nx, ny):
        # hood / skull mass
        hood = 1 - math.hypot((nx - .50) / .33, (ny - .34) / .33)
        # face plate inside the hood
        face = 1 - math.hypot((nx - .50) / .21, (ny - .44) / .22)
        # neck + shoulders
        neck = 1 - math.hypot((nx - .50) / .13, (ny - .80) / .14)
        sh = 1 - math.hypot((nx - .50) / .72, (ny - 1.14) / .36)
        v = max(hood * .72, face * .96, neck * .5, sh * .84)
        # visor: a wide dark band with bright edges
        if .32 < ny < .44 and abs(nx - .5) < .20:
            v = .98
        # headphone cups
        for cx in (.15, .85):
            d = math.hypot((nx - cx) / .07, (ny - .42) / .13)
            if d < 1:
                v = max(v, .88 * (1 - d) + .25)
        # rim light from the upper left
        v += .20 * max(0, .55 - nx) * (hood > 0)
        return v

    for r in range(rows):
        for c in range(cols):
            nx, ny = (c + .5) / cols, (r + .5) / rows
            v = max(0.0, min(1.0, shade(nx, ny) * 1.18 + bayer(c, r) * .22))
            if v < .09:
                continue
            g = LEVELS[min(len(LEVELS) - 1, int(v * len(LEVELS)))]
            if g == " ":
                continue
            color = MINT if ny < .30 else (CYAN if ny < .58 else "#2E8FD4")
            if v > .86:
                color = WHITE
            elif .42 < v < .55:
                color = "#13B78C"
            out.append(text(round(x + c * ch, 2), round(y + r * lh, 2), g, size, color,
                            opacity=.95))
    return "".join(out)


def content_bottom(body_svg):
    """lowest painted y in a body fragment (text baselines / rect edges / lines)"""
    ys = []
    for m in re.finditer(r'\by="(-?[\d.]+)"', body_svg):
        ys.append(float(m.group(1)))
    for m in re.finditer(r'\by1="(-?[\d.]+)"', body_svg):
        ys.append(float(m.group(1)))
    for m in re.finditer(r'\by2="(-?[\d.]+)"', body_svg):
        ys.append(float(m.group(1)))
    # rects: y + height
    for m in re.finditer(r'<rect[^>]*\by="(-?[\d.]+)"[^>]*\bheight="([\d.]+)"', body_svg):
        ys.append(float(m.group(1)) + float(m.group(2)))
    return max(ys) if ys else 0


# ── the card frame ──────────────────────────────────────────────────────────
def card(width, body_h, fname, tag, caption, body, note=None):
    h = HEAD_H + body_h + FOOT_H
    fy = HEAD_H + body_h
    bx = width - 18 - 92
    note_line = text(18, fy + 50, note, 11, INK_DIM, 400, SANS) if note else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}" fill="none" role="img" aria-label="{caption}">
  <title>{caption}</title>
  <defs>
    <clipPath id="cardClip"><rect width="{width}" height="{h}" rx="{RADIUS}"/></clipPath>
    <clipPath id="bodyClip"><rect y="{HEAD_H}" width="{width}" height="{body_h}"/></clipPath>
    <filter id="cardShadow" x="-6%" y="-6%" width="112%" height="116%">
      <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#0A0F14" flood-opacity=".16"/>
    </filter>
  </defs>

  <g filter="url(#cardShadow)">
    <g clip-path="url(#cardClip)">
      <rect width="{width}" height="{h}" fill="{PAPER}"/>
      <g clip-path="url(#bodyClip)">
        <rect y="{HEAD_H}" width="{width}" height="{body_h}" fill="{PANE}"/>
        {body}
      </g>
      <rect width="{width}" height="{h}" fill="none" stroke="{HAIRLINE}"/>

      <rect width="{width}" height="{HEAD_H}" fill="{PAPER}"/>
      <circle cx="22" cy="22" r="5" fill="#FF5F57"/>
      <circle cx="39" cy="22" r="5" fill="#FEBC2E"/>
      <circle cx="56" cy="22" r="5" fill="#28C840"/>
      {text(74, 26.5, fname, 13, INK, 600, SANS)}
      {text(width - 18, 26, tag, 10, INK_DIM, 600, ls="1.8", anchor="end")}
      <line x1="0" y1="{HEAD_H-.5}" x2="{width}" y2="{HEAD_H-.5}" stroke="{HAIRLINE}"/>

      <rect y="{fy}" width="{width}" height="{FOOT_H}" fill="{PAPER_2}"/>
      <line x1="0" y1="{fy+.5}" x2="{width}" y2="{fy+.5}" stroke="{HAIRLINE}"/>
      {text(18, fy + (31 if note else 42), caption, 12.5, INK_SOFT, 400, SANS)}
      {note_line}
      {button(bx, fy + 20)}
    </g>
  </g>
</svg>
"""


# ── 01 · hero (readme.md, wide) ─────────────────────────────────────────────
def build_hero():
    W, BH = 1100, 460
    p, cell, rows = 18, 8, 13
    band_h = rows * cell
    body = [band_nebula(p, p, (W - 2 * p) // cell, rows, cell, seed=7)]

    top = p + band_h + 30
    body.append(text(28, top, "~/profile", 11.5, DIM))
    body.append('<defs><linearGradient id="heroName" x1="28" y1="0" x2="620" y2="0" '
                'gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{MINT}"/><stop offset=".62" stop-color="{MINT}"/>'
                f'<stop offset="1" stop-color="{CYAN}"/></linearGradient></defs>')
    body.append(text(28, top + 74, "Garvittt.exe", 60, "url(#heroName)", 700, SANS))
    body.append(text(30, top + 104, "cybersec student · discord api dev", 14, TEXT))
    body.append(text(30, top + 126, "I break systems, then build bots that survive them.",
                     13, DIM))

    px = 30
    for tech, col in [("python", MINT), ("typescript", CYAN), ("go", MINT),
                      ("rust", CYAN), ("security", MINT)]:
        body.append(pill(px, top + 144, tech, col, 11, 10, 22))
        px += len(tech) * cw(11) + 20 + 9

    body.append(runs(30, top + 186, [("$ ", DIM), ("open to collabs · internships · good problems",
                                                   MINT)], 12.5))
    body.append(runs(30, top + 205, [("$ ", DIM), ("github", MINT), (" · portfolio ", CYAN),
                                     ("· discord ", MINT), ("· email", CYAN)], 12.5))

    # ── status panel, right
    x0, x1 = 706, W - 28
    body.append(f'<rect x="{x0-16}" y="{top-24}" width="{x1-x0+32}" height="218" rx="9" '
                f'fill="{WHITE}" fill-opacity=".035" stroke="{FAINT}"/>')
    y = top + 2
    body.append(text(x0, y, "status.md", 10.5, DIM, 600, ls="1.5"))
    y += 24
    for k, v, c in [("location", "India · IST", TEXT),
                    ("now", "shipping bots", MINT),
                    ("learning", "rust · binary exploitation", CYAN),
                    ("repos", "30 public", TEXT),
                    ("stars", "262 earned", AMBER)]:
        body.append(text(x0, y, k, 11.5, DIM))
        body.append(text(x1, y, v, 11.5, c, 500, anchor="end"))
        y += 19
    body.append(f'<line x1="{x0}" y1="{y-6}" x2="{x1}" y2="{y-6}" stroke="{FAINT}"/>')
    body.append(runs(x0, y + 16, [("> ", MINT), ("open to collabs.", TEXT)], 11.5))
    body.append(runs(x0, y + 33, [("> ", MINT), ("say hi on discord.", TEXT)], 11.5))

    # ── bottom strip: stats + sparkline + last commit
    sy = BH - 106
    body.append(f'<line x1="26" y1="{sy}" x2="{W-26}" y2="{sy}" stroke="{FAINT}" stroke-opacity=".6"/>')
    stats = [("public repos", "30", MINT), ("stars earned", "262", AMBER),
             ("languages", "6", CYAN), ("since", "jan 2025", TEXT)]
    sx = 30
    for i, (label, value, color) in enumerate(stats):
        body.append(text(sx, sy + 26, label, 10.5, DIM, 600, ls="1.3"))
        body.append(text(sx, sy + 54, value, 22, color, 700, SANS))
        sx += 116
        if i < len(stats) - 1:
            body.append(f'<line x1="{sx-26}" y1="{sy+14}" x2="{sx-26}" y2="{sy+58}" '
                        f'stroke="{FAINT}" stroke-opacity=".8"/>')

    # sparkline of the year
    rng = random.Random(11)
    gx0 = 560
    for wk in range(58):
        h = 6 + int(abs(math.sin(wk * .62)) * 26 * (.45 + rng.random() * .8))
        body.append(f'<rect x="{gx0 + wk*7}" y="{sy + 58 - h}" width="5" height="{h}" rx="1.5" '
                    f'fill="{MINT if wk % 4 else CYAN}" fill-opacity=".6"/>')
    body.append(text(gx0, sy + 78, "commits · last 52 weeks", 10, DIM))

    body.append(runs(30, BH - 30, [("last commit ", DIM), ("a3f19c2", AMBER),
                                   ("  harden discord bot command parsing", TEXT)], 11.5))
    body.append(runs(30, BH - 12, [("$ ", DIM), ("echo ", WHITE), ('"builds in public, breaks in private"', AMBER)],
                     11.5))

    return card(W, BH, "readme.md", "PROFILE",
                "Garvittt.exe — cybersecurity student, Discord API developer.",
                "".join(body), "one profile, four angles: system · shell · config · manifest")


# ── 02 · system.tsx (tall) ──────────────────────────────────────────────────
def build_system():
    W, BH = 560, globals().get('HUG', 528)
    p, cell, rows = 16, 8, 12
    band_h = rows * cell
    body = [band_nebula(p, p, (W - 2 * p) // cell, rows, cell, seed=21)]

    top = p + band_h + 20
    body.append(ascii_portrait(14, top + 8, 25, 21, ch=7.4, lh=8.0, size=7.8))
    body.append(text(14, top + 21 * 8.0 + 20, "gv-01 · human, allegedly", 9.5, DIM))
    body.append(f'<line x1="212" y1="{top}" x2="212" y2="{top + 21 * 8.0 + 30}" stroke="{FAINT}" stroke-opacity=".6"/>')

    x0, x1 = 230, W - 18
    s = 11.6
    y = top + 8
    for k, v in [("OS", "Arch · Linux 6.x"), ("WM", "Hyprland"), ("Editor", "Neovim"),
                 ("Shell", "zsh + starship")]:
        body.append(kv(y, k, v, x0, x1, s))
        y += 18

    y += 4
    body.append(f'<line x1="{x0}" y1="{y-11}" x2="{x1}" y2="{y-11}" stroke="{FAINT}" stroke-opacity=".55"/>')
    body.append(text(x0, y + 3, "arsenal", 10, CYAN, 600, ls="1.5"))
    y += 20
    for k, v in [("lang", "python · ts · go"), ("front", "next.js · tailwind"),
                 ("back", "fastapi · discord.py"), ("sec", "appsec · burp")]:
        body.append(kv(y, k, v, x0, x1, s))
        y += 18

    y += 2
    body.append(f'<line x1="{x0}" y1="{y-9}" x2="{x1}" y2="{y-9}" stroke="{FAINT}" stroke-opacity=".55"/>')
    px = x0
    for hexv, name in [(MINT, "mint"), (CYAN, "cyan"), (WHITE, "paper")]:
        body.append(f'<rect x="{px}" y="{y+2}" width="18" height="9" rx="2" fill="{hexv}"/>')
        body.append(text(px + 23, y + 10, name, 9.5, DIM))
        px += 23 + len(name) * cw(9.5) + 12

    y += 26
    body.append(runs(x0, y, [("$ ", DIM), ("now", MINT), (" — bots that stay online", TEXT)], 11))
    body.append(runs(x0, y + 15, [("    and breaking things on purpose.", TEXT)], 11))

    # mini contribution heatmap, bottom right
    hx0, hy0 = x0, BH - 128
    body.append(text(hx0, hy0 - 12, "contributions · last 26 weeks", 9.5, DIM))
    rng = random.Random(7)
    levels = [FAINT, "#0E4C42", "#0B7A62", "#0FA57F", MINT]
    for wk in range(26):
        for day in range(7):
            lvl = rng.choices([0, 1, 2, 3, 4], weights=[24, 24, 26, 18, 8])[0]
            body.append(f'<rect x="{hx0 + wk*12}" y="{hy0 + day*12}" width="10" height="10" rx="2" '
                        f'fill="{levels[lvl]}" fill-opacity="{1 if lvl else .5}"/>')
    body.append(text(hx0, hy0 + 7*12 + 18, "streak 41 days", 9.5, MINT, 500))
    body.append(text(hx0 + 110, hy0 + 7*12 + 18, "·  412 commits this year", 9.5, DIM))

    # skill meters, bottom half
    my = top + 21 * 8.0 + 44
    for label, pct in [("security", .86), ("bots", .92), ("frontend", .68), ("backend", .80)]:
        body.append(text(14, my, label, 9.5, DIM))
        bx0, bw = 78, 118
        body.append(f'<rect x="{bx0}" y="{my-7}" width="{bw}" height="6" rx="3" '
                    f'fill="{WHITE}" fill-opacity=".07"/>')
        body.append(f'<rect x="{bx0}" y="{my-7}" width="{bw*pct:.0f}" height="6" rx="3" '
                    f'fill="{MINT if pct > .85 else CYAN}"/>')
        body.append(text(bx0 + bw + 7, my, str(int(pct * 100)), 9.5, CYAN, 600))
        my += 16

    my += 8
    body.append(f'<line x1="14" y1="{my-14}" x2="196" y2="{my-14}" stroke="{FAINT}" stroke-opacity=".55"/>')
    body.append(text(14, my, "certs", 9.5, DIM, 600, ls="1.3"))
    for i, c in enumerate(["Security+ (in progress)", "TryHackMe · top 1%", "PortSwigger academy"]):
        body.append(text(14, my + 18 + i * 16, "+ " + c, 10, TEXT))
    my += 18 + 3 * 16 + 14
    body.append(f'<line x1="14" y1="{my-12}" x2="196" y2="{my-12}" stroke="{FAINT}" stroke-opacity=".55"/>')
    body.append(text(14, my + 4, "rig", 9.5, DIM, 600, ls="1.3"))
    body.append(text(14, my + 22, "arch · hyprland · neovim", 10, TEXT))
    my += 46
    body.append(f'<line x1="14" y1="{my-12}" x2="196" y2="{my-12}" stroke="{FAINT}" stroke-opacity=".55"/>')
    body.append(text(14, my + 4, "listening", 9.5, DIM, 600, ls="1.3"))
    body.append(text(14, my + 22, "lo-fi · phonk · synthwave", 10, TEXT))

    return card(W, BH, "System.tsx", "NEOTECH",
                "The spec sheet — what runs this machine.",
                "".join(body), "OS · arsenal · palette · skills · what I'm doing now")


# ── 03 · bash.tsx (tall) ────────────────────────────────────────────────────
def build_bash():
    W, BH = 560, globals().get('HUG', 528)
    p, cell, rows = 16, 8, 11
    band_h = rows * cell
    body = [band_night(p, p, (W - 2 * p) // cell, rows, cell)]

    s, step = 11.6, 18.4
    x = 20
    y = p + band_h + 28
    out = []

    def prompt(cmd):
        nonlocal y
        out.append(runs(x, y, [("garvit@api", MINT), (":", DIM), ("~", CYAN),
                               (" $ ", DIM), (cmd, WHITE)], s, 600))
        y += step

    def line(segs, indent=1):
        nonlocal y
        out.append(runs(x + indent * cw(s), y, segs, s))
        y += step

    prompt("whoami")
    line([("cyber security student · discord api dev", TEXT)])
    prompt("cat about.txt")
    line([("> ", DIM), ("I break systems to learn how they", TEXT)])
    line([("hold up, then build bots that do.", TEXT)], indent=2)
    prompt("ls stack/")
    line([("languages/ ", CYAN), ("python  typescript  go  rust", TEXT)])
    line([("backend/   ", CYAN), ("fastapi  node  discord.py", TEXT)])
    line([("security/  ", CYAN), ("appsec  burp  semgrep", TEXT)])
    prompt("uptime")
    line([("up ", DIM), ("since jan 2025", TEXT), (" · 30 repos · 262 stars", DIM)])
    prompt("ls projects/")
    line([("Val-X       ", MINT), ("valorant stat tracker", TEXT)])
    line([("ScamLens    ", CYAN), ("explainable scam detection", TEXT)])
    line([("Aegis-Scan  ", MINT), ("local appsec assessment", TEXT)])
    line([("CodeNexus   ", CYAN), ("semantic code search", TEXT)])
    prompt("cat currently.txt")
    line([("> ", DIM), ("hardening discord bots at 2am,", TEXT)])
    line([("writing up every box I root.", TEXT)], indent=2)
    prompt("ls links/")
    line([("github  ", MINT), ("portfolio  ", CYAN), ("discord  ", MINT), ("email", CYAN)])
    prompt("sudo make it secure")
    line([("[sudo] password: ", DIM), ("********", DIM)])
    out.append(runs(x + cw(s), y, [("[ok] ", MINT), ("hardening in progress", TEXT)], s))
    y += step
    out.append(f'<rect x="{x}" y="{y-s+2}" width="7" height="12" fill="{MINT}">'
               f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" '
               f'repeatCount="indefinite"/></rect>')

    return card(W, BH, "Bash.tsx", "PROMPT LOG",
                "The same profile, read as a shell session.",
                "".join(body) + "".join(out),
                "whoami · about · stack · links · uptime · one sudo joke")


# ── 04 · yaml.tsx (tall) ────────────────────────────────────────────────────
def build_yaml():
    W, BH = 560, globals().get('HUG', 528)
    p, cell, rows = 16, 10, 7
    band_h = rows * cell
    body = [band_sigils(p, p, (W - 2 * p) // cell, rows, cell)]

    s, step = 11.4, 15.4
    x, y = 20, p + band_h + 24
    ind = 2 * cw(s)
    out = []

    def line(depth, segs):
        nonlocal y
        out.append(runs(x + depth * ind, y, segs, s))
        y += step

    line(0, [("# garvit.yaml — the profile, as data", DIM)])
    line(0, [("profile:", CYAN)])
    line(1, [("name: ", MINT), ("Garvittt", TEXT)])
    line(1, [("role: ", MINT), ("Cyber Security Student", TEXT)])
    line(1, [("tagline: ", MINT), ("I break it, then secure it.", AMBER)])
    line(1, [("focus: ", MINT), ("[appsec, discord, ai]", TEXT)])
    line(1, [("stack:", MINT)])
    line(2, [("frontend: ", CYAN), ("[next.js, react]", TEXT)])
    line(2, [("backend: ", CYAN), ("[fastapi, node]", TEXT)])
    line(2, [("data: ", CYAN), ("[postgres, faiss]", TEXT)])
    line(2, [("infra: ", CYAN), ("[docker, linux]", TEXT)])
    line(1, [("currently: ", MINT), ("shipping bots", TEXT)])
    line(1, [("repos: ", MINT), ("30 public · 262 stars", TEXT)])
    line(1, [("tools:", MINT)])
    line(2, [("editor: ", CYAN), ("neovim · vscode", TEXT)])
    line(2, [("shell: ", CYAN), ("zsh + starship + tmux", TEXT)])
    line(2, [("os: ", CYAN), ("arch btw", TEXT)])
    line(1, [("open_to: ", MINT), ("[collabs, internships]", TEXT)])

    ry = y - 6
    out.append(f'<line x1="{x}" y1="{ry}" x2="{W-18}" y2="{ry}" stroke="{FAINT}" stroke-opacity=".55"/>')
    out.append(text(x, ry + 18, "# links — all live, below this card", 10.5, DIM))
    links = [("github", "github.com/Garvittt-API"),
             ("portfolio", "garvitt-dev.vercel.app"),
             ("discord", "@garvittt"),
             ("email", "garvitchoudhary2315@gmail.com")]
    for i, (k, v) in enumerate(links):
        ly = ry + 36 + i * 16
        out.append(text(x, ly, k, 10.5, MINT, 600, ls="1.1"))
        out.append(f'<path d="M{x+70} {ly-3.5} h9 m-3.5 -3.5 3.5 3.5 -3.5 3.5" stroke="{DIM}" '
                   f'stroke-width="1.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(text(x + 86, ly, v, 10.5, CYAN))

    fy2 = ry + 36 + 4 * 16 + 4
    out.append(f'<line x1="{x}" y1="{fy2-14}" x2="{W-18}" y2="{fy2-14}" stroke="{FAINT}" stroke-opacity=".55"/>')
    out.append(runs(x, fy2, [("$ ", DIM), ("yml-lint garvit.yaml", WHITE)], 11))
    out.append(runs(x, fy2 + 18, [("[ok] ", MINT), ("1 document · 0 errors · 0 warnings", TEXT)], 11))
    out.append(runs(x, fy2 + 36, [("[ok] ", MINT), ("theme applied: ", TEXT), ("#00E5A0", MINT),
                                  (" / ", DIM), ("#22D3EE", CYAN)], 11))

    ny = max(fy2 + 36 + 34, BH - 72)
    out.append(f'<line x1="{x}" y1="{ny-14}" x2="{W-18}" y2="{ny-14}" stroke="{FAINT}" stroke-opacity=".55"/>')
    out.append(runs(x, ny + 4, [("# ", DIM), ("what the file does not say", DIM)], 11))
    out.append(runs(x, ny + 24, [("> ", MINT), ("ships fast, documents faster,", TEXT)], 11))
    out.append(runs(x, ny + 42, [("  ", DIM), ("answers every issue.", TEXT)], 11))

    return card(W, BH, "YAML.tsx", "PROFILE.YAML",
                "Keys and columns — the profile as a config file.",
                "".join(body) + "".join(out),
                "nested, commented, and diff-friendly")


# ── 05 · packageJSON.tsx (tall) ─────────────────────────────────────────────
def build_pkg():
    W, BH = 560, globals().get('HUG', 528)
    p, cell, rows = 16, 8, 13
    band_h = rows * cell
    body = [band_robot(p, p, (W - 2 * p) // cell, rows, cell)]
    body.append(robot_face(W / 2, p + 22, 8))

    s, step = 11.4, 18.8
    x, y = 20, p + band_h + 22
    ind = 2 * cw(s)
    out = []

    def line(depth, segs):
        nonlocal y
        out.append(runs(x + depth * ind, y, segs, s))
        y += step

    line(0, [("{", DIM)])
    line(1, [('"name"', CYAN), (": ", DIM), ('"garvit"', MINT), (",", DIM)])
    line(1, [('"version"', CYAN), (": ", DIM), ('"2026.10.31"', MINT), (",", DIM)])
    line(1, [('"description"', CYAN), (":", DIM)])
    line(2, [('"cyber security student · discord dev"', AMBER), (",", DIM)])
    line(1, [('"scripts"', CYAN), (": {", DIM)])
    line(2, [('"learn"', CYAN), (": ", DIM), ('"read the rfc, then the exploit"', AMBER), (",", DIM)])
    line(2, [('"break"', CYAN), (": ", DIM), ('"find the edge case"', AMBER), (",", DIM)])
    line(2, [('"fix"', CYAN), (":   ", DIM), ('"make it boring"', AMBER), (",", DIM)])
    line(2, [('"ship"', CYAN), (":  ", DIM), ('"repeat until 3am"', AMBER)])
    line(1, [("},", DIM)])
    line(1, [('"keywords"', CYAN), (": ", DIM), ('["security", "discord", "bots"]', TEXT), (",", DIM)])
    line(1, [('"dependencies"', CYAN), (": {", DIM)])
    line(2, [('"curiosity"', CYAN), (": ", DIM), ('"^9.9.9"', MINT), (",", DIM)])
    line(2, [('"coffee"', CYAN), (": ", DIM), ('"latest"', MINT), (",", DIM)])
    line(2, [('"@garvit/bots"', CYAN), (": ", DIM), ('"github:Garvittt-API"', MINT)])
    line(1, [("},", DIM)])
    line(1, [('"homepage"', CYAN), (": ", DIM), ('"garvitt-dev.vercel.app"', CYAN), (",", DIM)])
    line(1, [('"license"', CYAN), (": ", DIM), ('"MIT"', MINT)])
    line(0, [("}", DIM)])

    fy2 = y + 16
    out.append(f'<line x1="{x}" y1="{fy2-14}" x2="{W-18}" y2="{fy2-14}" stroke="{FAINT}" stroke-opacity=".55"/>')
    out.append(runs(x, fy2, [("$ ", DIM), ("npm i @garvit/bots", WHITE)], 11))
    out.append(runs(x, fy2 + 18, [("+ @garvit/bots@1.0.0", MINT)], 11))
    out.append(runs(x, fy2 + 36, [("added 1 package in ", DIM), ("412ms", CYAN)], 11))

    return card(W, BH, "packageJSON.tsx", "MANIFEST",
                "The year in code, shipped as a manifest.",
                "".join(body) + "".join(out),
                "scripts are honest, dependencies are not")


# ── 06 · builds.sh (wide) ───────────────────────────────────────────────────
def build_builds():
    W, BH = 1100, 442
    body = [runs(24, 62, [("$ ", DIM), ("ls ~/builds", WHITE), ("  --sort=signal", DIM)], 13, 600),
            text(24, 82, "# four things worth clicking", 11.5, DIM)]

    projects = [
        ("Val-X", "01", "valorant stat tracker", "match history, metrics, playstyle trends",
         ["TypeScript", "Next.js", "API"], "08", MINT),
        ("ScamLens", "02", "explainable scam detection", "message, screenshot and URL analysis",
         ["TypeScript", "AI", "Security"], "04", CYAN),
        ("Aegis-Scan", "03", "local-first appsec assessment", "multi-engine scan to readable report",
         ["Python", "AppSec", "CLI"], "06", MINT),
        ("CodeNexus", "04", "semantic code search", "ask a codebase a question in english",
         ["FastAPI", "FAISS", "tree-sitter"], "08", CYAN),
    ]
    cw_, ch_ = 517, 148
    for i, (name, num, tag, desc, stack, stars, accent) in enumerate(projects):
        cx = 24 + (i % 2) * (cw_ + 18)
        cy = 96 + (i // 2) * (ch_ + 12)
        body.append(f'<rect x="{cx}" y="{cy}" width="{cw_}" height="{ch_}" rx="9" fill="#0B1219" '
                    f'stroke="{FAINT}"/>')
        body.append(f'<rect x="{cx}" y="{cy}" width="3" height="{ch_}" fill="{accent}"/>')
        body.append(text(cx + 22, cy + 24, num, 10.5, DIM, 600, ls="1.4"))
        body.append(text(cx + 22, cy + 50, name, 20, WHITE, 700, SANS))
        body.append(text(cx + 22, cy + 71, tag, 11.5, accent, 500))
        body.append(text(cx + 22, cy + 92, desc, 11, TEXT))
        px = cx + 22
        for j, tech in enumerate(stack):
            body.append(pill(px, cy + 107, tech, accent if j == 0 else CYAN, 10, 7, 18))
            px += len(tech) * cw(10) + 14 + 7
        body.append(star_path(cx + cw_ - 34, cy + 22, 7, AMBER))
        body.append(text(cx + cw_ - 22, cy + 48, stars, 13, TEXT, 600, anchor="end"))
        body.append(f'<path d="M{cx+cw_-96} {cy+ch_-22} h11 m-4 -4 4 4 -4 4" stroke="{DIM}" '
                    f'stroke-width="1.3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        body.append(text(cx + cw_ - 22, cy + ch_ - 18, "open repo", 10.5, DIM, 500, anchor="end"))

    body.append(runs(24, BH - 16, [("# ", DIM), ("stars as of oct 2026 — go add one", DIM)], 10.5))

    return card(W, BH, "builds.sh", "FEATURED",
                "Four builds that show the work: bots, security tooling, search.",
                "".join(body), "details for each one are in the table below")


# ── 07 · arsenal.tsx (wide) ─────────────────────────────────────────────────
def build_arsenal():
    W, BH = 1100, 316
    p, cell, rows = 18, 10, 6
    band_h = rows * cell
    body = [band_sigils(p, p, (W - 2 * p) // cell, rows, cell, seed=7)]

    s = 13
    cols = [
        [("languages", "python · typescript · javascript"),
         ("", "go · rust · dart"),
         ("frontend", "next.js · react · tailwind · flutter"),
         ("backend", "fastapi · node.js · discord.py · express")],
        [("data", "postgres · mongodb · redis · faiss"),
         ("infra", "docker · linux · git · cloudflare"),
         ("security", "appsec · burp suite · nmap · semgrep"),
         ("ai", "openai · langchain · faiss · whisper")],
    ]
    y0 = p + band_h + 34
    for ci, group in enumerate(cols):
        x0 = 24 + ci * 548
        x1 = x0 + 148
        y = y0
        for k, v in group:
            if k:
                body.append(text(x0, y, k, s, CYAN))
                body.append(leader(x0 + len(k) * cw(s) + 8, x1, y - 4))
                body.append(text(x1 + 18, y, v, s, TEXT))
            else:
                body.append(text(x1 + 18, y, v, s, TEXT))
            y += 21
    body.append(f'<line x1="572" y1="{y0-12}" x2="572" y2="{BH-46}" stroke="{FAINT}" stroke-opacity=".5"/>')

    # bottom strip: what I'm doing / learning / reading
    by = BH - 44
    body.append(f'<line x1="24" y1="{by-14}" x2="{W-24}" y2="{by-14}" stroke="{FAINT}" stroke-opacity=".5"/>')
    items = [("now", "shipping bots", MINT),
             ("learning", "rust async · binary exploitation", CYAN),
             ("rig", "arch · hyprland · neovim", TEXT)]
    ix = 24
    for k, v, c in items:
        body.append(text(ix, by, k, 10.5, DIM, 600, ls="1.3"))
        body.append(text(ix, by + 17, v, 11.5, c))
        ix += 350

    return card(W, BH, "arsenal.tsx", "STACK",
                "The toolbox, grouped the way it actually gets used.",
                "".join(body), "anything missing was probably installed at 2am")


def hug(builder, pad=20, tries=4):
    """rebuild a tall card with the shortest body that still fits its content"""
    svg = builder()
    for _ in range(tries):
        m = re.search(r'<rect y="(\d+)" width="\d+" height="(\d+)" fill="#080C12"/>', svg)
        if not m:
            break
        head, body_h = int(m.group(1)), int(m.group(2))
        start = svg.index('fill="#080C12"/>', svg.index('clip-path="url(#bodyClip)"'))
        end = svg.index("</g>", start)
        need = int(content_bottom(svg[start:end]) - head) + pad
        need = max(320, min(need, body_h))
        if abs(need - body_h) <= 2:
            break
        builder.__globals__["HUG"] = need
        svg = builder()
    return svg


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # the four tall cards share one body height so the 2x2 grid stays level
    tall = [build_system, build_bash, build_yaml, build_pkg]
    heights = []
    for b in tall:
        svg = b()
        m = re.search(r'<rect y="(\d+)" width="\d+" height="(\d+)" fill="#080C12"/>', svg)
        head = int(m.group(1))
        st = svg.index('fill="#080C12"/>', svg.index('clip-path="url(#bodyClip)"'))
        en = svg.index("</g>", st)
        heights.append(int(content_bottom(svg[st:en]) - head) + 22)
    globals()["HUG"] = max(heights)
    files = {
        "hero.svg": build_hero(),
        "system.svg": build_system(),
        "bash.svg": build_bash(),
        "yaml.svg": build_yaml(),
        "packagejson.svg": build_pkg(),
        "builds.svg": build_builds(),
        "arsenal.svg": build_arsenal(),
    }
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        h = re.search(r'height="(\d+)"', svg).group(1)
        print(f"assets/cards/{name:16s} {len(svg)/1024:6.1f} kB  h={h}")


if __name__ == "__main__":
    main()
