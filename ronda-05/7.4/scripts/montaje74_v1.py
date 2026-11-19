"""Montaje local 7.4 infomercial 3D (1080x1920, 30 fps, 25,62 s). 0 creditos. Reutiliza helpers del 3.1."""
import os, sys, math, subprocess
os.chdir("/home/user/misionlectura-media/ronda-05/7.4")
sys.path.insert(0, "/home/user/misionlectura-media/ronda-05/3.1/scripts")
import numpy as np
from PIL import Image, ImageDraw
import montaje as M
from montaje import (W, H, FPS, CORAL, BLUE, YEL, NAVY, WHITE, CREAM, DARK, PB, PX, font, ease, lerp, prog, new_layer, text_c,
                     sub_words, scaled, paste_c, letter_card, rings, confetti, arrow, cover_strip, persp_coeffs, M_TEX, CARD_M, CARD_A, pop_scale)
DUR = 25.62
ST = {n: Image.open(f"imagenes/{n}.jpg").convert("RGB") for n in ("I1", "I3", "I5")}
def still(name, z, cx=0.5, cy=0.5):
    im = ST[name]; w, h = im.size
    bw = w / z; bh = min(h, w * 16 / 9) / z
    x0 = min(max(cx * w - bw / 2, 0), w - bw); y0 = min(max(cy * h - bh / 2, 0), h - bh)
    return im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + bw, y0 + bh)).convert("RGBA")
def clipf(n, ct, z, cx=0.5, cy=0.5):
    cl = M.getclip(n); idx = min(max(int(round(ct * FPS)), 0), len(cl) - 1)
    w, h = 720, 1280; bw, bh = w / z, h / z
    x0 = min(max(cx * w - bw / 2, 0), w - bw); y0 = min(max(cy * h - bh / 2, 0), h - bh)
    return Image.fromarray(cl[idx]).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + bw, y0 + bh)).convert("RGBA"), (x0, y0, x0 + bw, y0 + bh)
def zz(t, a, b, z0, z1, e=True):
    x = prog(t, a, b); return lerp(z0, z1, ease(x) if e else x)
def crema(): 
    img = Image.new("RGBA", (W, H), CREAM + (255,)); return img
# ---- tracking de la tarjeta en CLIP 4 (px del clip 720x1280): t_clip -> TL,TR,BR,BL
KF = [(0.0, [(236, 592), (482, 586), (484, 762), (238, 764)]), (0.4, [(236, 576), (484, 574), (486, 746), (238, 752)]),
      (0.7, [(236, 572), (484, 570), (486, 744), (238, 746)]), (1.0, [(234, 574), (484, 568), (488, 744), (236, 748)])]
def quad(ct):
    ct = min(max(ct, KF[0][0]), KF[-1][0])
    for (t0, q0), (t1, q1) in zip(KF, KF[1:]):
        if t0 <= ct <= t1:
            x = (ct - t0) / (t1 - t0); return [(lerp(a[0], b[0], x), lerp(a[1], b[1], x)) for a, b in zip(q0, q1)]
def tracked_M(lay, t, box):
    ct = t - 14.15; q = quad(ct); k = W / (box[2] - box[0])
    dst = [((x - box[0]) * k, (y - box[1]) * k) for x, y in q]
    co = persp_coeffs(dst, [(0, 0), (440, 0), (440, 300), (0, 300)])
    tr = M_TEX.transform((W, H), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)
    a = prog(t, 14.2, 14.35)
    if a < 1: tr.putalpha(tr.getchannel("A").point(lambda v: int(v * a)))
    lay.alpha_composite(tr)
    return (sum(p[0] for p in dst) / 4, sum(p[1] for p in dst) / 4)
# ---- subtitulos (tiempos reales de la voz maestra)
S1 = 1150; SB = 1432
SUBS = [
 (0.96, 1.80, [("ENSEÑAR A LEER", WHITE)], S1, 104), (1.80, 2.50, [("EN CASA", YEL)], S1, 104),
 (2.50, 3.10, [("¿POR DÓNDE", WHITE)], S1, 104), (3.10, 3.70, [("EMPEZAR?", WHITE)], S1, 104),
 (3.70, 4.50, [("LAS LETRAS", WHITE)], S1, 104), (4.50, 5.30, [("SE APRENDEN", YEL)], S1, 104),
 (5.30, 6.20, [("PERO JUNTARLAS", WHITE)], 1400, 100), (6.20, 6.78, [("EN SÍLABAS", WHITE)], 1400, 100),
 (6.78, 7.30, [("NO ES", WHITE)], S1, 104), (7.30, 8.10, [("TAN", WHITE), ("FÁCIL", YEL)], S1, 104),
 (8.10, 8.90, [("POR ESO EXISTE", WHITE)], SB, 90), (8.90, 9.96, [("MISIÓN LECTURA", YEL)], SB, 90),
 (9.96, 10.70, [("EL MÉTODO", WHITE)], SB, 90), (10.70, 11.40, [("PARA ENSEÑAR", WHITE)], SB, 90),
 (11.40, 11.85, [("A LEER", WHITE)], SB, 90), (11.85, 12.30, [("EN CASA", YEL)], SB, 90),
 (12.30, 13.40, [("DEL SONIDO", WHITE)], S1, 104), (13.40, 14.15, [("A LAS SÍLABAS", WHITE)], S1, 104),
 (14.15, 14.97, [("MMM", YEL)], 1340, 120), (14.97, 15.45, [("A", YEL)], S1, 120),
 (16.20, 16.90, [("PASO A PASO", WHITE)], 1350, 104), (16.90, 17.60, [("CON JUEGOS", WHITE)], 1350, 104), (17.60, 18.50, [("CORTOS", YEL)], 1350, 104),
 (18.50, 19.05, [("¡Y ESO NO", WHITE)], S1, 104), (19.05, 19.60, [("ES TODO!", YEL)], S1, 104),
 (19.60, 20.60, [("INCLUYE CUATRO", WHITE)], 1130, 96), (20.60, 21.30, [("BONUS", YEL)], 1130, 96), (21.30, 22.18, [("PARA PRACTICAR", WHITE)], 1130, 96),
 (22.18, 22.55, [("TOCA", WHITE)], S1, 104),
 (23.65, 24.20, [("Y MÍRALO", WHITE)], S1, 104), (24.20, 24.90, [("COMPLETO", YEL)], S1, 104),
]
def sub_at(t):
    for a, b, p, y, sz in SUBS:
        if a <= t < b: return p, y, sz
def render(t, with_bg=True):
    lay = new_layer(); img = None; box = None
    # ---- fondo por escena
    if t < 0.96: img, box = clipf(1, t, zz(t, 0, 0.96, 1.00, 1.06, False), 0.5, 0.45)
    elif t < 2.50: img, box = clipf(1, t, zz(t, 0.96, 2.5, 1.10, 1.18), 0.5, 0.42)
    elif t < 3.70: img, box = clipf(1, t, zz(t, 2.5, 3.7, 1.00, 1.05), 0.5, 0.5)
    elif t < 5.30: img = still("I1", zz(t, 3.7, 5.3, 1.00, 1.10), 0.5, 0.5)
    elif t < 6.78: img = crema()
    elif t < 8.10: img = still("I1", zz(t, 6.78, 8.1, 1.12, 1.20), 0.5, 0.36)
    elif t < 9.96: img = still("I5", zz(t, 8.1, 9.96, 1.00, 1.04), 0.5, 0.5)
    elif t < 11.40: img = still("I5", zz(t, 10.5, 11.4, 1.00, 1.12), 0.5, lerp(0.5, 0.58, ease(prog(t, 10.5, 11.4))))
    elif t < 12.30: img = still("I5", lerp(1.10, 1.03, ease(prog(t, 11.4, 12.3))), lerp(0.36, 0.5, ease(prog(t, 11.4, 12.3))), 0.55)
    elif t < 14.15: img = crema()
    elif t < 14.97: img, box = clipf(4, t - 14.15, 1.0)
    elif t < 15.45: img = Image.new("RGBA", (W, H), (30, 60, 120, 255))
    elif t < 16.20: img = Image.new("RGBA", (W, H), (255, 244, 220, 255))
    elif t < 18.50: img, box = clipf(4, t - 14.15, zz(t, 17.0, 18.0, 1.00, 1.12), 0.5, 0.45)
    elif t < 19.60: img, box = clipf(5, t - 18.5, zz(t, 18.5, 19.6, 1.00, 1.06), 0.5, 0.40)
    elif t < 22.18: img, box = clipf(5, t - 18.5, zz(t, 19.6, 22.18, 1.00, 1.10), 0.5, 0.5)
    elif t < 23.65: img, box = clipf(1, 3.95, zz(t, 22.18, 23.65, 1.00, 1.06), 0.5, 0.5)
    else: img, box = clipf(1, 3.95, zz(t, 23.65, 25.5, 1.12, 1.20, False), 0.5, 0.45)
    d = ImageDraw.Draw(lay)
    # ---- insertos
    if 0 <= t < 0.96:
        a = int(255 * min(1, prog(t, 0.0, 0.1))); text_c(lay, "¡ATENCIÓN!", 400, 150, YEL, 10, PX, shadow=True, alpha=a)
    if 3.70 <= t < 5.30:
        for j, (L, col) in enumerate((("M", CORAL), ("A", BLUE), ("P", (84, 201, 120)), ("S", (160, 110, 230)), ("L", YEL), ("T", (63, 200, 200)))):
            t0 = 4.2 + 0.15 * j
            if t < t0: continue
            x = prog(t, t0, t0 + 0.18); k = pop_scale(x) * 0.42
            paste_c(lay, scaled(letter_card(L, col), k), 150 + j * 155, 1330 + lerp(-160, 0, ease(x)), alpha=min(1, x * 3))
    if 5.30 <= t < 6.78:
        x = ease(prog(t, 5.3, 6.2)); 
        if t < 6.2:
            paste_c(lay, scaled(CARD_M, 0.95), lerp(-200, 380, x), 800); paste_c(lay, scaled(CARD_A, 0.95), lerp(1280, 700, x), 800)
        else:
            b = ease(prog(t, 6.2, 6.5)); bounce = math.sin(math.pi * min(1, (t - 6.2) / 0.5))
            paste_c(lay, scaled(CARD_M, 0.95), 380 - 220 * b, 800 - 80 * bounce, rot=-12 * b); paste_c(lay, scaled(CARD_A, 0.95), 700 + 220 * b, 800 - 80 * bounce, rot=12 * b)
    if 8.90 <= t < 10.50:   # portada del metodo: arriba a la izquierda, capa fija sin zoom, solo titulo
        a = min(prog(t, 8.9, 9.0), 1 - prog(t, 10.4, 10.5)); c = cover_strip(0, 312)
        paste_c(lay, c, 64 + c.width / 2, 300 + c.height / 2 + 30, alpha=a)
    if 12.30 <= t < 14.15:
        img = crema(); a = ease(prog(t, 12.3, 12.55))
        text_c(lay, "Del sonido", 560, 118, NAVY, 0, PX, alpha=int(255 * a)); text_c(lay, "a las sílabas", 700, 118, NAVY, 0, PX, alpha=int(255 * a))
        y = 850; x1, x2 = 300, 780
        d.rounded_rectangle((x1 - 8, y - 8, x2 + 8, y + 8), 8, fill=(220, 210, 190, 255))
        pl = ease(prog(t, 12.65, 13.42)); d.rounded_rectangle((x1 - 8, y - 8, lerp(x1, x2, pl) + 8, y + 8), 8, fill=CORAL + (255,))
        for xx, lab, t0, col in ((x1, "Sonido", 12.65, CORAL), (x2, "Sílabas", 13.42, BLUE)):
            on = t >= t0; k = 1.0 + (0.25 * math.sin(math.pi * prog(t, t0, t0 + 0.3)) if on else 0)
            r = int(52 * k); d.ellipse((xx - r, y - r, xx + r, y + r), fill=(col if on else (225, 218, 200)) + (255,), outline=NAVY + (255,), width=8)
            text_c(lay, lab, y + 115, 66, NAVY, 0, PB, cx=xx)
    if 14.15 <= t < 14.97 and box:
        cc = tracked_M(lay, t, box); rings(lay, cc, t, 14.2, 14.97, CORAL, n=3, maxr=300)
    if 14.97 <= t < 15.45:
        g = ImageDraw.Draw(img)
        for y in range(0, H, 8): g.rectangle((0, y, W, y + 8), fill=(int(lerp(40, 22, y / H)), int(lerp(90, 50, y / H)), int(lerp(170, 120, y / H)), 255))
        x = prog(t, 14.97, 15.09); k = lerp(0.3, 1.0, ease(x)) * (1 + 0.04 * math.sin(math.pi * x))
        rings(lay, (W // 2, 820), t, 14.97, 15.35, BLUE, n=2, maxr=380); paste_c(lay, scaled(letter_card("A", BLUE, 520), k), W // 2, 820)
    if 15.45 <= t < 16.20:
        g = ImageDraw.Draw(img)
        for y in range(0, H, 8): g.rectangle((0, y, W, y + 8), fill=(255, int(lerp(240, 205, y / H)), int(lerp(215, 160, y / H)), 255))
        x = ease(prog(t, 15.45, 15.62)); zoom = lerp(1.0, 1.10, prog(t, 15.62, 16.2))
        if t < 15.62:
            paste_c(lay, scaled(CARD_M, 0.95), lerp(-200, 380, x), 820); paste_c(lay, scaled(CARD_A, 0.95), lerp(1280, 700, x), 820)
        else:
            f = font(PX, int(430 * zoom)); tx = "MA"
            b = d.textbbox((0, 0), tx, font=f, stroke_width=14); cx0 = W / 2 - (b[0] + b[2]) / 2; cy0 = 820 - (b[1] + b[3]) / 2
            d.text((cx0 + 8, cy0 + 12), tx, font=f, fill=(0, 0, 0, 90), stroke_width=14, stroke_fill=(0, 0, 0, 90))
            d.text((cx0, cy0), "M", font=f, fill=CORAL + (255,), stroke_width=14, stroke_fill=DARK + (255,))
            d.text((cx0 + d.textlength("M", font=f), cy0), "A", font=f, fill=BLUE + (255,), stroke_width=14, stroke_fill=DARK + (255,))
            text_c(lay, "¡MA!", 1150, 200, YEL, 12, PX)
        confetti(lay, t, 15.55, W // 2, 820)
    if 20.18 <= t < 22.18:
        for j, i in enumerate((1, 2, 3, 4)):
            t0 = 20.18 + 0.27 * j
            if t < t0: continue
            x = ease(prog(t, t0, t0 + 0.2)); c = cover_strip(i, 255); cx = 190 + j * 233; cy = 1345 + (j % 2) * 14
            paste_c(lay, c, cx, cy + lerp(90, 0, x), rot=(-9, -3, 3, 9)[j], alpha=x)
    # ---- subtitulos y CTA
    s = sub_at(t)
    if s: sub_words(lay, s[0], s[1], s[2])
    if t >= 22.28: arrow(lay, W // 2, 1300, 110, int(255 * prog(t, 22.28, 22.48)))
    if t >= 22.55: text_c(lay, "Más información", 1430, 84, WHITE, 8, PB, alpha=int(255 * prog(t, 22.55, 22.75)), shadow=True)
    return Image.alpha_composite(img, lay).convert("RGB"), lay
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "frames":
        os.makedirs("work/fr", exist_ok=True)
        for t in map(float, sys.argv[2:]): render(t)[0].save(f"work/fr/f_{t:05.2f}.png")
    elif mode == "bbox":  # zona segura de capas 2D
        for t in map(float, sys.argv[2:]):
            lay = render(t)[1]; bb = lay.getchannel("A").getbbox(); print(t, bb)
    else:
        out = sys.argv[2]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-an", out], stdin=subprocess.PIPE)
        for i in range(int(round(DUR * FPS))): p.stdin.write(render(i / FPS)[0].tobytes())
        p.stdin.close(); p.wait()
