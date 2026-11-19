"""Montaje local del 3.1 «Mmm, qué rica» (1080x1920, 30 fps, 16,8 s). 0 creditos."""
import json, math, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 16.8
FD = "/home/user/oficina-anuncios/assets/fuentes/"
PB = FD + "Poppins-Bold.ttf"; PX = FD + "Poppins-ExtraBold.ttf"
COV = "/home/user/oficina-anuncios/assets/producto/portadas/"
CORAL = (255, 107, 87); BLUE = (63, 167, 245); YEL = (255, 214, 64); NAVY = (35, 28, 74); WHITE = (255, 255, 255); CREAM = (252, 246, 232)
DARK = (28, 18, 48)
_f = {}
def font(p, s):
    k = (p, s)
    if k not in _f: _f[k] = ImageFont.truetype(p, s)
    return _f[k]

def clip_frames(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 1280, 720, 3)
    return a
CL = {}
def getclip(n):
    if n not in CL: CL[n] = clip_frames(f"clips/c{n}.mp4")
    return CL[n]

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def lerp(a, b, x): return a + (b - a) * x
def prog(t, a, b): return min(max((t - a) / (b - a), 0.0), 1.0)

# ---------- escenas de video: (t0, t1, clip, offset (clip_t = t - offset), z0, z1, dy)
SC = [
    (0.0, 1.2, 1, 0.0, 1.00, 1.06), (1.2, 2.85, 1, 0.0, 1.10, 1.18), (2.85, 3.85, 1, 0.0, 1.00, 1.05), (3.85, 5.0, 1, 0.0, 1.08, 1.12),
    (5.0, 6.4, 2, 5.0, 1.00, 1.04), (6.4, 7.1, 2, 5.0, 1.04, 1.12),
    (8.3, 10.0, 2, 5.0, 1.00, 1.06),
    (10.0, 12.1, 3, 10.0, 1.00, 1.05),
    (13.9, 15.0, 3, 11.8, 1.00, 1.05), (15.0, 16.8, 3, 11.8, 1.18, 1.20),
]
def scene_at(t):
    for s in SC:
        if s[0] <= t < s[1]: return s
    return None

def zoom_box(t, s):
    z = lerp(s[4], s[5], ease(prog(t, s[0], s[1])))
    w, h = 720 / z, 1280 / z
    cx, cy = 360, 640 + (0 if z < 1.15 else -10)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), z

def base_frame(t):
    s = scene_at(t)
    if s is None: return None
    cl = getclip(s[2]); ct = t - s[3]
    idx = min(max(int(round(ct * FPS)), 0), len(cl) - 1)
    box, z = zoom_box(t, s)
    im = Image.fromarray(cl[idx]).resize((W, H), Image.LANCZOS, box=box)
    return im, box, s

# ---------- utilidades de dibujo
def new_layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def text_c(lay, txt, cy, size, fill=WHITE, stroke=9, fp=PB, cx=W // 2, shadow=False, alpha=255):
    d = ImageDraw.Draw(lay); f = font(fp, size)
    b = d.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    x = cx - (b[0] + b[2]) / 2; y = cy - (b[1] + b[3]) / 2
    if shadow: d.text((x + 6, y + 10), txt, font=f, fill=(0, 0, 0, 110), stroke_width=stroke, stroke_fill=(0, 0, 0, 110))
    d.text((x, y), txt, font=f, fill=fill + (alpha,), stroke_width=stroke, stroke_fill=DARK + (alpha,))
    return (x, y, b)
def sub_words(lay, parts, cy=1150, size=104):
    """parts: [(texto, color)] en una linea centrada."""
    d = ImageDraw.Draw(lay); f = font(PB, size)
    ws = []
    for tx, col in parts:
        b = d.textbbox((0, 0), tx, font=f, stroke_width=9); ws.append(b[2] - b[0])
    sp = int(size * 0.28); tot = sum(ws) + sp * (len(parts) - 1); x = W / 2 - tot / 2
    for (tx, col), w in zip(parts, ws):
        b = d.textbbox((0, 0), tx, font=f, stroke_width=9)
        d.text((x - b[0], cy - (b[1] + b[3]) / 2), tx, font=f, fill=col + (255,), stroke_width=9, stroke_fill=DARK + (255,)); x += w + sp
def rrect(lay, box, r, fill, outline=None, ow=0):
    ImageDraw.Draw(lay).rounded_rectangle(box, r, fill=fill, outline=outline, width=ow)
def scaled(img, k): return img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
def paste_c(lay, img, cx, cy, rot=0, alpha=1.0):
    if rot: img = img.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1: a = img.getchannel("A").point(lambda v: int(v * alpha)); img = img.copy(); img.putalpha(a)
    x0 = int(cx - img.width / 2); y0 = int(cy - img.height / 2)
    if x0 >= W or y0 >= H or x0 + img.width <= 0 or y0 + img.height <= 0: return
    cl = img.crop((max(0, -x0), max(0, -y0), min(img.width, W - x0), min(img.height, H - y0)))
    if cl.width > 0 and cl.height > 0: lay.alpha_composite(cl, (max(0, x0), max(0, y0)))
def letter_card(letter, col, size=360):
    im = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((26, 36, size + 26, size + 36), 56, fill=(0, 0, 0, 90))
    d.rounded_rectangle((20, 20, size + 20, size + 20), 56, fill=col + (255,), outline=(255, 255, 255, 255), width=10)
    f = font(PX, int(size * 0.78)); b = d.textbbox((0, 0), letter, font=f)
    d.text((20 + size / 2 - (b[0] + b[2]) / 2, 20 + size / 2 - (b[1] + b[3]) / 2 - 6), letter, font=f, fill=WHITE)
    return im
CARD_M = letter_card("M", CORAL); CARD_A = letter_card("A", BLUE)
def pop_scale(x):  # entrada 0..1 con sobreimpulso corto (solo insertos, no el CTA)
    x = min(max(x, 0), 1)
    return 1.0 + 0.18 * math.sin(math.pi * min(x * 1.3, 1)) * (1 - x) * 2 if x < 1 else 1.0

# ---------- portadas recortadas al titulo (sin textos propios)
CROP = {0: (114, 304), 1: (112, 256), 2: (116, 306), 3: (112, 304), 4: (114, 350)}
def cover_strip(i, w):
    im = Image.open(COV + f"p{i}.png").convert("RGB").crop((0, CROP[i][0], 640, CROP[i][1]))
    k = w / 640; im = im.resize((w, int(im.height * k)), Image.LANCZOS)
    out = Image.new("RGBA", (im.width + 24, im.height + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    d.rounded_rectangle((16, 20, im.width + 16, im.height + 20), 22, fill=(0, 0, 0, 90))
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 20, fill=255)
    out.paste(im, (8, 8), m)
    d.rounded_rectangle((8, 8, im.width + 8, im.height + 8), 20, outline=(255, 255, 255, 255), width=6)
    return out

# ---------- tracking de la tarjeta (esquinas en px del clip 720x1280): t_clip -> TL,TR,BR,BL
KF = [(0.5, [(145, 662), (362, 660), (370, 824), (152, 806)]), (0.8, [(143, 668), (360, 666), (372, 830), (150, 812)]),
      (1.1, [(152, 652), (370, 650), (382, 816), (158, 800)]), (1.4, [(188, 557), (405, 555), (405, 720), (190, 715)]),
      (1.7, [(205, 540), (425, 533), (420, 697), (220, 700)]), (2.1, [(205, 535), (428, 525), (425, 688), (215, 690)])]
def card_quad(ct):
    ct = min(max(ct, KF[0][0]), KF[-1][0])
    for (t0, q0), (t1, q1) in zip(KF, KF[1:]):
        if t0 <= ct <= t1:
            x = (ct - t0) / (t1 - t0); return [(lerp(a[0], b[0], x), lerp(a[1], b[1], x)) for a, b in zip(q0, q1)]
def persp_coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float))
M_TEX = Image.new("RGBA", (440, 300), (0, 0, 0, 0))
_d = ImageDraw.Draw(M_TEX); _b = _d.textbbox((0, 0), "M", font=font(PX, 270))
_d.text((220 - (_b[0] + _b[2]) / 2, 150 - (_b[1] + _b[3]) / 2 - 4), "M", font=font(PX, 270), fill=CORAL + (255,), stroke_width=0)
def tracked_M(lay, t, box):
    ct = t - 5.0; q = card_quad(ct); k = W / (box[2] - box[0])
    dst = [((x - box[0]) * k, (y - box[1]) * k) for x, y in q]
    co = persp_coeffs(dst, [(0, 0), (440, 0), (440, 300), (0, 300)])
    tr = M_TEX.transform((W, H), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)
    a = prog(t, 5.5, 5.7)
    if a < 1: tr.putalpha(tr.getchannel("A").point(lambda v: int(v * a)))
    lay.alpha_composite(tr)
    return (sum(p[0] for p in dst) / 4, sum(p[1] for p in dst) / 4)

def rings(lay, c, t, t0, t1, col=CORAL, n=3, maxr=330):
    d = ImageDraw.Draw(lay)
    for i in range(n):
        x = ((t - t0) / (t1 - t0) - i * 0.28) % 1.0 if t >= t0 else None
        if x is None: continue
        r = 40 + maxr * x; a = int(200 * (1 - x))
        d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col + (a,), width=12)

CONF = np.random.default_rng(7).random((60, 5))
def confetti(lay, t, t0, cx, cy):
    if t < t0 or t > t0 + 0.9: return
    x = (t - t0) / 0.9; d = ImageDraw.Draw(lay); cols = [CORAL, BLUE, YEL, (84, 201, 120), (160, 110, 230)]
    for i, (a, b, c_, e, f_) in enumerate(CONF):
        ang = a * 2 * math.pi; sp = 250 + 600 * b; r = sp * ease(x) ** 0.7
        px = cx + math.cos(ang) * r; py = cy + math.sin(ang) * r + 500 * x * x * (0.4 + c_)
        s = 12 + 14 * e
        d.rectangle((px - s / 2, py - s / 2, px + s / 2, py + s / 2), fill=cols[i % 5] + (int(255 * (1 - x ** 2)),))

def arrow(lay, cx, cy, size, alpha=255):
    d = ImageDraw.Draw(lay); s = size
    pts = [(cx - s * .22, cy - s * .5), (cx + s * .22, cy - s * .5), (cx + s * .22, cy + s * .02), (cx + s * .5, cy + s * .02), (cx, cy + s * .55), (cx - s * .5, cy + s * .02), (cx - s * .22, cy + s * .02)]
    d.polygon(pts, fill=WHITE + (alpha,), outline=DARK + (alpha,))
    d.line(pts + [pts[0]], fill=DARK + (alpha,), width=9, joint="curve")

# ---------- subtitulos (tiempos reales de la voz, ver informe)
SUBS = [
    (0.0, 0.36, [("MMM", YEL)]), (0.36, 1.2, [("¡QUÉ RICA!", WHITE)]), (1.2, 1.72, [("ACABO DE", WHITE)]), (1.72, 2.2, [("DECIR UNA", WHITE)]),
    (2.2, 2.7, [("LETRA", YEL)]), (2.7, 3.4, [("ESE", WHITE), ("MMM", YEL)]), (3.4, 3.7, [("ABRE", WHITE)]),
    (5.0, 5.5, [("PRIMERO", WHITE)]), (5.5, 6.4, [("EL SONIDO", YEL)]), (6.4, 7.1, [("MMM", YEL)]), (7.1, 7.6, [("A", YEL)]),
    (8.3, 8.7, [("MISIÓN", WHITE)]), (8.7, 9.1, [("LECTURA", WHITE)]), (9.1, 9.5, [("ES EL", WHITE)]), (9.5, 10.0, [("MÉTODO", WHITE)]),
    (10.0, 10.65, [("PARA ENSEÑAR", WHITE)]), (10.65, 11.15, [("A LEER", WHITE)]), (11.15, 12.1, [("EN CASA", YEL)]),
    (12.1, 12.8, [("DEL SONIDO", WHITE)]), (12.8, 13.2, [("A LAS", WHITE)]), (13.2, 13.9, [("SÍLABAS", YEL)]),
    (13.9, 14.35, [("ÉCHALE", WHITE)]), (14.35, 14.9, [("UN VISTAZO", WHITE)]), (14.9, 15.55, [("EN MÁS", WHITE)]),
]
def subtitle_at(t):
    for a, b, p in SUBS:
        if a <= t < b: return p

# ---------- composicion
def render(t):
    bf = base_frame(t); lay = new_layer()
    S_MAMA = 3.7 <= t < 5.0
    if bf:
        img, box, s = bf
        if S_MAMA: img = img.filter(ImageFilter.GaussianBlur(7))
        img = img.convert("RGBA")
    else:
        img = None; box = None
    # --- insertos a pantalla completa
    if 7.1 <= t < 7.6:  # tarjeta A
        img = Image.new("RGBA", (W, H), (30, 60, 120, 255)); g = ImageDraw.Draw(img)
        for y in range(0, H, 8): g.rectangle((0, y, W, y + 8), fill=(int(lerp(40, 22, y / H)), int(lerp(90, 50, y / H)), int(lerp(170, 120, y / H)), 255))
        x = prog(t, 7.1, 7.22); k = lerp(0.3, 1.0, ease(x)) * (1 + 0.04 * math.sin(math.pi * x))
        rings(lay, (W // 2, 820), t, 7.1, 7.45, BLUE, n=2, maxr=380)
        paste_c(lay, scaled(letter_card("A", BLUE, 520), k), W // 2, 820)
    if 7.6 <= t < 8.3:  # fusion MA
        img = Image.new("RGBA", (W, H), (255, 244, 220, 255)); g = ImageDraw.Draw(img)
        for y in range(0, H, 8): g.rectangle((0, y, W, y + 8), fill=(int(lerp(255, 255, y / H)), int(lerp(240, 205, y / H)), int(lerp(215, 160, y / H)), 255))
        x = ease(prog(t, 7.6, 7.78)); zz = lerp(1.0, 1.10, prog(t, 7.78, 8.3))
        mx = lerp(-200, 380, x); ax = lerp(1280, 700, x)
        if t < 7.78:
            paste_c(lay, scaled(CARD_M, 0.95), mx, 820); paste_c(lay, scaled(CARD_A, 0.95), ax, 820)
        else:
            f = font(PX, int(430 * zz)); d = ImageDraw.Draw(lay); tx = "MA"
            b = d.textbbox((0, 0), tx, font=f, stroke_width=14); cx0 = W / 2 - (b[0] + b[2]) / 2; cy0 = 820 - (b[1] + b[3]) / 2
            d.text((cx0 + 8, cy0 + 12), tx, font=f, fill=(0, 0, 0, 90), stroke_width=14, stroke_fill=(0, 0, 0, 90))
            mw = d.textbbox((0, 0), "M", font=f, stroke_width=14)[2]
            d.text((cx0, cy0), "M", font=f, fill=CORAL + (255,), stroke_width=14, stroke_fill=DARK + (255,))
            d.text((cx0 + d.textlength("M", font=f), cy0), "A", font=f, fill=BLUE + (255,), stroke_width=14, stroke_fill=DARK + (255,))
        confetti(lay, t, 7.65, W // 2, 820)
        if t >= 7.78: text_c(lay, "¡MA!", 1150, 200, YEL, 12, PX)
    if 12.1 <= t < 13.9:  # ruta
        img = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(lay)
        a = ease(prog(t, 12.1, 12.35))
        text_c(lay, "Del sonido", 560, 118, NAVY, 0, PX, alpha=int(255 * a)); text_c(lay, "a las sílabas", 700, 118, NAVY, 0, PX, alpha=int(255 * a))
        y = 850; x1, x2 = 300, 780
        d.rounded_rectangle((x1 - 8, y - 8, x2 + 8, y + 8), 8, fill=(220, 210, 190, 255))
        pl = ease(prog(t, 12.4, 13.2)); d.rounded_rectangle((x1 - 8, y - 8, lerp(x1, x2, pl) + 8, y + 8), 8, fill=CORAL + (255,))
        for xx, lab, t0, col in ((x1, "Sonido", 12.3, CORAL), (x2, "Sílabas", 13.2, BLUE)):
            on = t >= t0; k = 1.0 + (0.25 * math.sin(math.pi * prog(t, t0, t0 + 0.3)) if on else 0)
            r = int(52 * k); d.ellipse((xx - r, y - r, xx + r, y + r), fill=(col if on else (225, 218, 200)) + (255,), outline=NAVY + (255,), width=8)
            text_c(lay, lab, y + 115, 66, NAVY, 0, PB, cx=xx)
    if img is None: img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    # --- insertos sobre el video
    if bf and 5.5 <= t < 7.1:
        cc = tracked_M(lay, t, box)
        if t >= 6.4: rings(lay, cc, t, 6.4, 7.1, CORAL, n=3, maxr=300)
    if 2.25 <= t < 3.2:
        k = pop_scale(prog(t, 2.25, 2.6)); xo = lerp(500, 0, ease(prog(t, 2.25, 2.5))); xo2 = lerp(0, 520, ease(prog(t, 3.0, 3.2)))
        paste_c(lay, scaled(CARD_M, 0.62 * k), 800 + xo + xo2, 640)
    if S_MAMA:
        d = ImageDraw.Draw(lay)
        def big(word, cy, t0):
            x = ease(prog(t, t0, t0 + 0.22)); fz = 190; f = font(PX, fz)
            b = d.textbbox((0, 0), word, font=f, stroke_width=12); wd = b[2] - b[0]; x0 = W / 2 - wd / 2; y0 = cy - (b[1] + b[3]) / 2 + lerp(40, 0, x)
            al = int(255 * x)
            d.text((x0 + 8, y0 + 12), word, font=f, fill=(0, 0, 0, int(110 * x)), stroke_width=12, stroke_fill=(0, 0, 0, int(110 * x)))
            d.text((x0, y0), word, font=f, fill=WHITE + (al,), stroke_width=12, stroke_fill=DARK + (al,))
            m = d.textbbox((0, 0), word[0], font=f, stroke_width=12)
            d.text((x0 - m[0] + b[0], y0), word[0], font=f, fill=CORAL + (al,), stroke_width=12, stroke_fill=DARK + (al,))
        big("MAMÁ", 800, 3.7)
        if t >= 4.4:
            text_c(lay, "y", 930, 80, YEL, 8, PB); big("MESA", 1080, 4.4)
    if 8.4 <= t < 10.0:
        k = pop_scale(prog(t, 8.4, 8.7)) * 1.0; c = scaled(cover_strip(0, 470), k)
        paste_c(lay, c, 800, 345, rot=-3)
    if 11.1 <= t < 12.1:
        for j, i in enumerate((1, 2, 3, 4)):
            t0 = 11.1 + 0.25 * j
            if t < t0: continue
            x = ease(prog(t, t0, t0 + 0.2)); c = cover_strip(i, 280)
            cx = 160 + j * 253; cy = 1345 + (j % 2) * 14
            paste_c(lay, c, cx, cy + lerp(90, 0, x), rot=lerp(0, (-9, -3, 3, 9)[j], 1), alpha=x)
    # --- subtitulos / CTA
    if not (S_MAMA or 7.6 <= t < 8.3 or 7.1 <= t < 7.6 and False):
        p = subtitle_at(t)
        if p:
            if (7.1 <= t < 7.6): sub_words(lay, p, 1330)
            elif 5.0 <= t < 7.1: sub_words(lay, p, 1400)
            else: sub_words(lay, p)
    if t >= 14.9:
        a = int(255 * prog(t, 14.9, 15.1)); arrow(lay, W // 2, 1310, 110, a)
    if t >= 15.55:
        text_c(lay, "Más información", 1440, 84, WHITE, 8, PB, alpha=int(255 * prog(t, 15.55, 15.75)))
    out = Image.alpha_composite(img, lay).convert("RGB")
    # fundido inicial/final del video no se aplica (corte directo)
    return out

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "frames":
        for t in map(float, sys.argv[2:]):
            render(t).save(f"fr/f_{t:05.2f}.png")
    else:
        out = sys.argv[2]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-an", out], stdin=subprocess.PIPE)
        N = int(round(DUR * FPS))
        for i in range(N):
            p.stdin.write(render(i / FPS).tobytes())
        p.stdin.close(); p.wait()
