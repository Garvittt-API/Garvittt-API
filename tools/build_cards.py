#!/usr/bin/env python3
"""
Build the window cards used by README.md  ->  assets/cards/*.svg

Look: paper-coloured macOS window, dark code pane, a dithered pixel band,
and a caption strip with a lime "USE ->" button. Everything is plain SVG —
no external services, no build step in the README.

    python3 tools/build_cards.py

Three cards, nothing else:
    hero     1100 px  -> the banner
    system    760 px  -> the neofetch profile card
    arsenal  1100 px  -> the stack
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


def ascii_portrait(x, y, cols, rows, ch=7.6, lh=8.2, size=8.0, scheme="mint"):
    """dithered duotone bust — big hood, dark visor, headphone cups, shoulders"""
    out = []

    def shade(nx, ny):
        """head + neck + trapezoid torso, lit from the upper left"""
        # head (slightly egg shaped)
        hx, hy, hrx, hry = .50, .24, .255, .195
        head = 1 - math.hypot((nx - hx) / hrx, (ny - hy) / hry)
        # jaw, narrows toward the chin
        jaw = 1 - math.hypot((nx - .50) / (.175 - .06 * max(0, ny - .30)),
                             (ny - .385) / .095)
        # neck
        neck = 1 - math.hypot((nx - .50) / .095, (ny - .495) / .065)
        # torso: trapezoid, half width grows with y
        v = 0.0
        if .520 < ny < 1.02:
            half = .105 + (ny - .520) * .96
            edge = abs(nx - .5) / half
            if edge < 1:
                v = .80 - .30 * edge ** 2
                # collar notch
                if ny < .60 and abs(nx - .5) < .085:
                    v = .32
        v = max(head, jaw * .97, neck * .70, v)
        # visor band across the eyes
        if .245 < ny < .325 and abs(nx - .5) < .215:
            v = .99
        # headphone cups
        for cx in (.168, .832):
            d = math.hypot((nx - cx) / .050, (ny - .300) / .088)
            if d < 1:
                v = max(v, .58 * (1 - d) + .16)
        # rim light from the upper left
        v += .24 * max(0, .50 - nx) * (head > 0)
        # fade the torso out toward the caption
        if ny > .84:
            v *= max(.15, 1 - (ny - .84) * 3.6)
        return v

    for r in range(rows):
        for c in range(cols):
            nx, ny = (c + .5) / cols, (r + .5) / rows
            v = max(0.0, min(1.0, shade(nx, ny) * 1.14 + bayer(c, r) * .24))
            if v < .10:
                continue
            g = LEVELS[min(len(LEVELS) - 1, int(v * len(LEVELS)))]
            if g == " ":
                continue
            if scheme == "cyan":
                color = "#1C8FB8" if ny < .30 else (CYAN if ny < .62 else "#2563A8")
                if v > .86:
                    color = "#BFEFFF"
            else:
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
                "".join(body), "one profile, three screens: hero · system · arsenal")


# ── 02 · system.tsx — the neofetch card ─────────────────────────────────────
def build_system():
    W = 760
    p, cell, rows = 18, 8, 14
    band_h = rows * cell
    top = HEAD_H + p + band_h + 18
    PORTRAIT_W = 210

    body = [band_nebula(p, HEAD_H + p, (W - 2 * p) // cell, rows, cell, seed=21)]
    PCOLS, PROWS, PCH, PLH = 24, 56, 8.0, 8.6
    body.append(ascii_portrait(14, top - 6, PCOLS, PROWS, ch=PCH, lh=PLH, size=8.2,
                               scheme="cyan"))
    body.append(text(16, top - 6 + PROWS * PLH + 20, "gv-01 · human, allegedly", 10, DIM))

    # ── neofetch rows ───────────────────────────────────────────────────────
    ROWS = [
        ("section", "OS"),
        ("kv", "Uptime:", "1 year, 9 months"),
        ("kv", "Host:", "PLANET EARTH · INDIA"),
        ("kv", "Kernel:", "6.x-arch1"),
        ("kv", "IDE:", "Neovim · VS Code"),
        ("gap",),

        ("section", "Languages"),
        ("kv", "Programming:", "Python, TypeScript, JavaScript, Go, Rust"),
        ("kv", "Human:", "English, Hindi"),
        ("gap",),

        ("section", "Tools"),
        ("kv", "Backend:", "FastAPI, Node.js, discord.py"),
        ("kv", "Frontend:", "Next.js, React, Tailwind"),
        ("kv", "Data:", "Postgres, MongoDB, FAISS"),
        ("kv", "Ops:", "Docker, Linux, Git, Cloudflare"),
        ("gap",),

        ("section", "About"),
        ("kv", "Role:", "Cybersecurity student · Discord API dev"),
        ("kv", "Focus:", "appsec, bots, AI tooling"),
        ("gap",),

        ("section", "Bio"),
        ("kv", "Bio 1:", "I break systems to learn how they survive,"),
        ("kv", "Bio 2:", "then build bots that hold up in production."),
        ("gap",),

        ("section", "Contact"),
        ("kv", "GitHub:", "github.com/Garvittt-API"),
        ("kv", "Discord:", "@garvittt"),
        ("kv", "Mail:", "garvitchoudhary2315@gmail.com"),
        ("gap",),

        ("section", "GitHub Stats"),
        ("kv", "Repos:", "30 public · 262 stars"),
        ("kv", "Commits:", "435"),
        ("kv", "Opened:", "jan 2025"),
    ]

    col_x0, col_x1 = PORTRAIT_W + 34, W - 20
    s_, step_, gap_ = 12.6, 19.0, 8.0
    BOTTOM_Y = top + sum(step_ if r[0] != "gap" else gap_ for r in ROWS) - 2
    _yb = top
    body.append(f'<line x1="{PORTRAIT_W + 18}" y1="{top - 14}" x2="{PORTRAIT_W + 18}" '
                f'y2="{BOTTOM_Y}" stroke="{FAINT}" stroke-opacity=".45"/>')

    s, step, gap_h = 12.6, 19.0, 8.0
    y = top + 2
    for row in ROWS:
        kind = row[0]
        if kind == "section":
            label = row[1]
            body.append(text(col_x0, y, label, s, CYAN, 700, ls="0.2"))
            body.append(leader(col_x0 + len(label) * cw(s) + 8, col_x1, y - 4))
            y += step
        elif kind == "kv":
            label, value = row[1], row[2]
            body.append(text(col_x0, y, label, s, CYAN))
            body.append(leader(col_x0 + len(label) * cw(s) + 6,
                               col_x1 - len(value) * cw(s) - 10, y - 4))
            body.append(text(col_x1, y, value, s, WHITE, 500, anchor="end"))
            y += step
        else:
            y += gap_h

    body_h = y - HEAD_H + 4
    return card(W, body_h, "System.tsx", "NEOTECH",
                "The spec sheet — who this is, on one screen.",
                "".join(body), "portrait · system · languages · tools · bio · stats")


# ── 03 · arsenal.tsx (wide) ─────────────────────────────────────────────────
def build_arsenal():
    W, BH = 1100, 300
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
    y0 = p + band_h + 30
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
            y += 20
    # second column: certifies / reading, under the first block
    x0 = 24 + 548
    x1 = x0 + 148
    y = y0 + 4 * 21 + 8
    body.append(f'<line x1="{x0}" y1="{y-14}" x2="{W-24}" y2="{y-14}" stroke="{FAINT}" stroke-opacity=".55"/>')
    body.append(text(x0, y, "reading", 13, CYAN))
    body.append(leader(x0 + 7 * cw(13) + 8, x1, y - 4))
    body.append(text(x1 + 18, y, "the web application hacker's handbook", 13, TEXT))
    y += 20
    body.append(text(x0, y, "grinding", 13, CYAN))
    body.append(leader(x0 + 8 * cw(13) + 8, x1, y - 4))
    body.append(text(x1 + 18, y, "portswigger academy · picoctf", 13, TEXT))

    lx0, lx1 = 24, 172
    ly = y0 + 4 * 21 + 8
    body.append(f'<line x1="{lx0}" y1="{ly-14}" x2="520" y2="{ly-14}" stroke="{FAINT}" stroke-opacity=".55"/>')
    body.append(text(lx0, ly, "shipping", 13, CYAN))
    body.append(leader(lx0 + 8 * cw(13) + 8, lx1, ly - 4))
    body.append(text(lx1 + 18, ly, "discord bots · dev tooling", 13, TEXT))
    ly += 20
    body.append(text(lx0, ly, "writing", 13, CYAN))
    body.append(leader(lx0 + 7 * cw(13) + 8, lx1, ly - 4))
    body.append(text(lx1 + 18, ly, "writeups · readmes · docs", 13, TEXT))

    body.append(f'<line x1="572" y1="{y0-12}" x2="572" y2="{ly-40}" stroke="{FAINT}" stroke-opacity=".5"/>')

    # bottom strip: what I'm doing / learning / reading
    by = BH - 30
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "hero.svg": build_hero(),
        "system.svg": build_system(),
        "arsenal.svg": build_arsenal(),
    }
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        h = re.search(r'<svg[^>]*height="([\d.]+)"', svg).group(1)
        print(f"assets/cards/{name:12s} {len(svg)/1024:6.1f} kB  h={h}")


if __name__ == "__main__":
    main()
