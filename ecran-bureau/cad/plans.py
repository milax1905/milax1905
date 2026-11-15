#!/usr/bin/env python3
"""Génère les plans cotés (SVG) à partir des paramètres de deskbar.py -> ../docs/"""
import os

import deskbar as d

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
INK, DIM, BODY, MUTED = "#1c2430", "#c2410c", "#39404d", "#5b6676"
FONT = "font-family='Inter,Segoe UI,Helvetica,Arial,sans-serif'"


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.el = w, h, []
        self.el.append(f"<rect width='{w}' height='{h}' fill='#fbfbf9'/>")
        self.el.append("<defs><marker id='a' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' "
                       f"orient='auto-start-reverse'><path d='M0 1 L10 5 L0 9 z' fill='{DIM}'/></marker></defs>")

    def poly(self, pts, fill=BODY, stroke="none", sw=1, dash=None, op=1):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = f" stroke-dasharray='{dash}'" if dash else ""
        self.el.append(f"<polygon points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{da} opacity='{op}'/>")

    def rect(self, x, y, w, h, fill=BODY, stroke="none", sw=1, rx=0):
        self.el.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{rx}' fill='{fill}' "
                       f"stroke='{stroke}' stroke-width='{sw}'/>")

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1, dash=None, arrows=False):
        da = f" stroke-dasharray='{dash}'" if dash else ""
        ar = " marker-start='url(#a)' marker-end='url(#a)'" if arrows else ""
        self.el.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{stroke}' "
                       f"stroke-width='{sw}'{da}{ar}/>")

    def text(self, x, y, s, size=15, fill=INK, anchor="start", weight=400, rot=None):
        tr = f" transform='rotate({rot} {x:.1f} {y:.1f})'" if rot is not None else ""
        self.el.append(f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' fill='{fill}' text-anchor='{anchor}' "
                       f"font-weight='{weight}' {FONT}{tr}>{s}</text>")

    def hdim(self, x1, x2, y, label, ext_from=None):
        if ext_from is not None:
            for x in (x1, x2):
                self.line(x, ext_from, x, y + (6 if y > ext_from else -6), DIM, 0.8)
        self.line(x1, y, x2, y, DIM, 1.2, arrows=True)
        self.text((x1 + x2) / 2, y - 7, label, 15, DIM, "middle", 600)

    def vdim(self, x, y1, y2, label, ext_from=None, side=-1):
        if ext_from is not None:
            for y in (y1, y2):
                self.line(ext_from, y, x + (6 if x > ext_from else -6), y, DIM, 0.8)
        self.line(x, y1, x, y2, DIM, 1.2, arrows=True)
        self.text(x + side * 8, (y1 + y2) / 2, label, 15, DIM, "middle", 600, rot=-90)

    def leader(self, x, y, tx, ty, label, anchor="start"):
        self.line(x, y, tx, ty, MUTED, 1)
        self.el.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.6' fill='{MUTED}'/>")
        self.text(tx + (6 if anchor == "start" else -6), ty + 5, label, 15, INK, anchor, 500)

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, name), "w") as f:
            f.write(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {self.w} {self.h}' "
                    f"width='{self.w}' height='{self.h}'>" + "".join(self.el) + "</svg>")
        print("écrit", name)


def side_shapes():
    """Polygones de la coupe (repère modèle y, z)."""
    lip = [[(a, 0), (b, 0), (b, d.LIP), (a, d.LIP)] for a, b in
           ((0, d.LED_Y0), (d.LED_Y1, d.OPEN_Y0), (d.OPEN_Y1, d.H))]
    body = lip + [
        [(0, 0), (d.WALL / d.C, 0), d.TIP_I, d.TIP_O],                                   # semelle
        [(d.Y_IN, 0), (d.H, 0), (d.H, d.DEPTH), (d.Y_IN, d.DEPTH)],                      # paroi haute
        [(d.DIV_Y0, d.LIP), (d.DIV_Y0 + d.DIV_DY, d.LIP), (d.DIV_ROOT + d.DIV_DY, d.Z_COVER),
         (d.DIV_ROOT, d.Z_COVER)],                                                       # cloison
        [(d.DIV_Y0 + d.DIV_DY, d.LIP), (d.Y_P0, d.LIP), (d.Y_P0, 4.0), (d.div_up(4.0), 4.0)],
    ]
    return body


def general():
    s = Svg(1300, 690)
    s.text(40, 46, "DeskBar — encombrement", 24, INK, weight=700)
    s.text(40, 70, "cotes en mm · dalle 12,6\" 1920×515 (BOE NV126B5M-N41)", 15, MUTED)
    # ---- vue de face (2,6 px/mm)
    k, ox, oy = 2.4, 96, 150
    w, h = 2 * d.HALF_OUT * k, d.H * k
    s.rect(ox, oy, w, h, BODY, rx=8)
    fx = lambda x: ox + (d.HALF_OUT - x) * k            # +X modèle = gauche vu de face
    fy = lambda y: oy + (d.H - y) * k
    s.rect(fx(d.OPEN_HALF_W), fy(d.OPEN_Y1), 2 * d.OPEN_HALF_W * k, (d.OPEN_Y1 - d.OPEN_Y0) * k, "#0d1016")
    ax, ay = fx(d.ACTIVE_W / 2), fy(d.Y_P0 + d.PANEL_H - d.BORDER_TOP)
    s.rect(ax, ay, d.ACTIVE_W * k, d.ACTIVE_H * k, "#1d2a44")
    s.text(ox + w / 2, ay + d.ACTIVE_H * k / 2 + 6, f"image {d.ACTIVE_W:.1f} × {d.ACTIVE_H:.1f}".replace(".", ","),
           17, "#c9d6f2", "middle", 500)
    s.rect(fx(d.LED_HALF_W), fy(d.LED_Y1), 2 * d.LED_HALF_W * k, (d.LED_Y1 - d.LED_Y0) * k, "#9aa6ff")
    s.line(ox + w / 2, oy - 6, ox + w / 2, oy + h + 6, "#8a94a6", 1, "5 4")
    s.text(ox + w / 2, oy + h + 24, "plan de joint (2 demi-coques)", 14, MUTED, "middle")
    s.hdim(ox, ox + w, oy - 34, f"{2 * d.HALF_OUT:.1f}".replace(".", ","), ext_from=oy)
    s.vdim(ox - 34, oy, oy + h, f"façade {d.H:.1f}".replace(".", ","), ext_from=ox)
    s.hdim(fx(d.LED_HALF_W), fx(-d.LED_HALF_W), oy + h + 56, f"bandeau lumineux {2 * d.LED_HALF_W:.0f} × "
           f"{d.LED_Y1 - d.LED_Y0:.1f}".replace(".", ","))
    s.text(ox, oy + h + 92, "Vue de face", 16, INK, weight=700)
    # ---- profil posé (3,4 px/mm)
    k2, px, py = 3.0, 985, 560
    wp = lambda y, z: (px + (y * d.S + z * d.C) * k2, py - (y * d.C - z * d.S) * k2)
    prof = [(0, 0), (d.H, 0), (d.H, d.DEPTH), (d.Y_GUSSET, d.DEPTH), d.TIP_I, d.TIP_O]
    s.poly([wp(*p) for p in prof], "#d9dde4", BODY, 1.2)
    s.poly([wp(*p) for p in [(0, 0), (d.H, 0), (d.H, d.DEPTH), (d.ybo(d.DEPTH), d.DEPTH)]], BODY)
    s.poly([wp(*p) for p in [(0, 0), (d.WALL / d.C, 0), d.TIP_I, d.TIP_O]], BODY)
    s.line(px - 60, py, px + d.FOOT * k2 + 30, py, "#8a94a6", 1.2)
    top = wp(d.H, 0)
    s.vdim(px - 44, top[1], py, f"{d.H * d.C:.1f}".replace(".", ","), ext_from=px - 4)
    s.hdim(px, px + d.FOOT * k2, py + 40, f"{d.FOOT:.0f}", ext_from=py)
    s.line(px, py, px, py - 150, "#8a94a6", 1, "5 4")
    s.text(px + 12, py - 132, f"{d.THETA:.0f}°", 16, DIM, weight=600)
    a, b = wp(d.H, 0), wp(d.H, d.DEPTH)
    s.line(a[0] + 6, a[1] - 14, b[0] + 6, b[1] - 14, DIM, 1.2, arrows=True)
    s.text((a[0] + b[0]) / 2 + 12, (a[1] + b[1]) / 2 - 22, f"{d.DEPTH:.0f}", 15, DIM, "middle", 600)
    s.text(px - 60, py + 92, "Profil (posé sur le bureau)", 16, INK, weight=700)
    s.save("plan_encombrement.svg")


def section():
    s = Svg(1340, 800)
    s.text(40, 46, "DeskBar — coupe", 24, INK, weight=700)
    s.text(40, 70, "appareil posé, vu de côté · la dalle se glisse dans les demi-coques par le plan de joint", 15, MUTED)
    k, px, py = 5.6, 450, 700
    wp = lambda y, z: (px + (y * d.S + z * d.C) * k, py - (y * d.C - z * d.S) * k)
    P = lambda pts, **kw: s.poly([wp(*p) for p in pts], **kw)
    s.line(px - 120, py, px + d.FOOT * k + 150, py, "#8a94a6", 1.2)
    P([(d.ybi(d.DEPTH), d.DEPTH), (d.Y_GUSSET, d.DEPTH), d.TIP_I], fill="#e6e9ee", stroke="#9aa3b2", dash="5 4")
    for pts in side_shapes():
        P(pts)
    # crochet haut + doigt d'appui du capot
    P([(d.Y_IN, d.Z0_HOOK), (d.Y_IN - 3.5, d.Z0_HOOK + 3.5), (d.Y_IN - 3.5, d.Z0_HOOK + 5.5),
       (d.Y_IN, d.Z0_HOOK + 9)])
    yt = d.Y_P0 + d.PANEL_H - 0.2
    zt = d.LIP + d.PANEL_T_EDGE + 2.0
    P([(yt - 2.8, zt), (yt, zt), (yt, d.Z_COVER), (yt - 2.8, d.Z_COVER)], fill="#6f7a8c")
    # capot
    P([(d.ybi(d.DEPTH) + d.COVER_CLR, d.Z_COVER), (d.Y_IN - d.COVER_CLR, d.Z_COVER),
       (d.Y_IN - d.COVER_CLR, d.DEPTH), (d.ybi(d.DEPTH) + d.COVER_CLR, d.DEPTH)], fill="#6f7a8c")
    # dalle
    P([(d.Y_P0, d.LIP), (d.Y_P0 + d.PANEL_H, d.LIP), (d.Y_P0 + d.PANEL_H, d.LIP + d.PANEL_T_EDGE),
       (d.Y_P0, d.LIP + d.PANEL_T_EDGE)], fill="#11151c")
    P([(d.Y_P0 + 0.5, d.LIP + d.PANEL_T_EDGE), (d.Y_P0 + 8, d.LIP + d.PANEL_T_EDGE),
       (d.Y_P0 + 8, d.LIP + d.PANEL_T_MAX), (d.Y_P0 + 0.5, d.LIP + d.PANEL_T_MAX)], fill="#11151c")
    # diffuseur, ruban LED, faisceau lumineux
    y0d, y1d = d.ybi(d.LIP + 0.8) + 0.2, d.DIV_Y0 + d.DIV_SLOPE * 0.8 - 0.2
    P([(d.DIV_ROOT - 8.5, d.Z_COVER - 2.2), (d.DIV_ROOT - 3.9, d.Z_COVER - 2.2), (d.LED_Y1, d.LIP + 0.8),
       (d.LED_Y0, d.LIP + 0.8)], fill="#8f9bff", op=0.28)
    P([(y0d, d.LIP), (y1d, d.LIP), (y1d, d.LIP + 0.8), (y0d, d.LIP + 0.8)], fill="#b8c0ff")
    P([(d.DIV_ROOT - 12.2, d.Z_COVER - 2.2), (d.DIV_ROOT - 0.2, d.Z_COVER - 2.2), (d.DIV_ROOT - 0.2, d.Z_COVER),
       (d.DIV_ROOT - 12.2, d.Z_COVER)], fill="#e2b93b")
    # Raspberry Pi
    zb = d.Z_COVER - 4.0
    P([(d.PI_Y0, zb - 1.4), (d.PI_Y0 + 56, zb - 1.4), (d.PI_Y0 + 56, zb), (d.PI_Y0, zb)], fill="#2f8f4e")
    P([(d.PI_Y0 + 12, zb - 13), (d.PI_Y0 + 46, zb - 13), (d.PI_Y0 + 46, zb - 1.4), (d.PI_Y0 + 12, zb - 1.4)],
      fill="#57b377")
    for y in (d.PI_Y0 + 3.5, d.PI_Y0 + 52.5):
        P([(y - 3, zb), (y + 3, zb), (y + 3, d.Z_COVER), (y - 3, d.Z_COVER)], fill="#6f7a8c")
    # légendes
    L = lambda y, z, tx, ty, t, anchor="start": s.leader(*wp(y, z), tx, ty, t, anchor)
    L(75, d.LIP + 1.5, 290, 250, "Dalle LCD 12,6\"", "end")
    L(d.H - 6, 0.8, 290, 170, "Façade : 5 mm autour de l'image", "end")
    L(d.Y_IN - 2, d.Z0_HOOK + 4, 640, 96, "Crochet de la coque + doigt du capot (mousse)")
    L(d.H - 1.2, 30, 960, 150, "Paroi haute")
    L(85, d.DEPTH - 1.2, 980, 300, "Capot arrière (porte l'électronique)")
    L(d.PI_Y0 + 30, zb - 8, 980, 370, "Raspberry Pi 5 + ventilateur")
    L(d.DIV_ROOT - 6, d.Z_COVER - 1.1, 980, 520, "Ruban LED collé sous le capot")
    L((d.DIV_Y0 + d.DIV_ROOT) / 2 + 1, (d.LIP + d.Z_COVER) / 2, 980, 450, "Cloison inclinée du puits de lumière")
    L(d.TIP_O[0] * 0.8, d.TIP_O[1] * 0.8 + 1, 980, 640, "Semelle (pied intégré)")
    L(d.Y_GUSSET - 8, d.DEPTH + 9, 980, 585, "Gousset d'extrémité")
    L((d.LED_Y0 + d.LED_Y1) / 2, d.LIP + 0.4, 290, 640, "Diffuseur", "end")
    L(d.Y_P0 + 4, d.LIP + d.PANEL_T_MAX - 0.5, 290, 560, "Carte de la dalle (5,3 max)", "end")
    s.vdim(px - 400, wp(d.H, 0)[1], py, f"{d.H * d.C:.1f}".replace(".", ","), ext_from=px - 380)
    s.hdim(px, px + d.FOOT * k, py + 44, f"{d.FOOT:.0f}", ext_from=py)
    s.save("plan_coupe.svg")


def wiring():
    s = Svg(1240, 790)
    s.text(40, 46, "DeskBar — câblage", 24, INK, weight=700)
    s.text(40, 70, "tout se branche sur le connecteur 40 broches du Raspberry Pi (numéros de broche physiques)", 15, MUTED)

    def block(x, y, w, h, title, sub=None, fill="#ffffff"):
        s.rect(x, y, w, h, fill, "#39404d", 1.6, 12)
        s.text(x + 16, y + 28, title, 17, INK, weight=700)
        if sub:
            s.text(x + 16, y + 50, sub, 13.5, MUTED)

    def pin(x, y, label, color, right=True):
        s.rect(x - (0 if right else 150), y - 13, 150, 26, "#f2f4f7", color, 1.6, 6)
        s.text(x + (10 if right else -140), y + 5, label, 13.5, INK, weight=600)

    def wire(pts, color, label=None, lx=0, ly=0):
        p = " ".join(f"{x},{y}" for x, y in pts)
        s.el.append(f"<polyline points='{p}' fill='none' stroke='{color}' stroke-width='3.2' "
                    "stroke-linejoin='round' stroke-linecap='round'/>")
        if label:
            s.text(lx, ly, label, 13, color, weight=600)

    R, K, B, G, Y, P = "#d6312b", "#20242b", "#2563c9", "#0e9f6e", "#c98a04", "#7c3aed"
    block(470, 110, 300, 420, "Raspberry Pi 5", "connecteur GPIO 40 broches")
    pins = [("1 · 3V3", Y, 180), ("3 · SDA (GPIO2)", B, 216), ("5 · SCL (GPIO3)", G, 252), ("9 · GND", K, 288),
            ("2 · 5V", R, 356), ("6 · GND", K, 392), ("19 · MOSI (GPIO10)", P, 428)]
    for label, col, y in pins[:4]:
        pin(770, y, label, col, right=False)
    for label, col, y in pins[4:]:
        pin(770, y, label, col, right=False)
    # sonde
    block(930, 150, 270, 170, "Sonde SHT40 / SHT41", "température + humidité (I²C 0x44)")
    for i, (lab, col) in enumerate((("VIN", Y), ("SDA", B), ("SCL", G), ("GND", K))):
        y = 180 + 36 * i
        wire([(770, y), (850 + 12 * i, y), (850 + 12 * i, 222 + 22 * i), (930, 222 + 22 * i)], col)
        s.text(940, 227 + 22 * i, lab, 13, col, weight=700)
    s.text(930, 342, "câble 4 fils de 30 à 50 cm :", 13, MUTED)
    s.text(930, 360, "la sonde reste hors du boîtier", 13, MUTED)
    # LED
    block(930, 400, 270, 130, "74AHCT125", "adaptateur de niveau 3,3 V → 5 V")
    block(930, 590, 270, 130, "Ruban WS2812B", "144 LED/m · 30 cm · 43 LED")
    wire([(770, 356), (880, 356), (880, 472), (930, 472)], R)
    wire([(880, 472), (880, 650), (930, 650)], R)
    wire([(770, 392), (862, 392), (862, 492), (930, 492)], K)
    wire([(862, 492), (862, 682), (930, 682)], K)
    wire([(770, 428), (845, 428), (845, 512), (930, 512)], P)
    s.text(942, 477, "VCC", 13, R, weight=700)
    s.text(942, 497, "GND + 1OE", 13, K, weight=700)
    s.text(942, 517, "1A (entrée)", 13, P, weight=700)
    wire([(1140, 530), (1140, 590)], P)
    s.text(1132, 565, "1Y → 330 Ω → DIN", 13, P, "end", 700)
    s.text(942, 655, "+5V", 13, R, weight=700)
    s.text(942, 687, "GND", 13, K, weight=700)
    s.text(930, 744, "1000 µF entre +5V et GND,", 13, MUTED)
    s.text(930, 762, "au plus près du ruban", 13, MUTED)
    # alimentation + écran
    block(40, 150, 250, 90, "Alimentation 27 W", "USB-C 5,1 V · 5 A (officielle)")
    wire([(290, 195), (470, 195)], R, "USB-C (adaptateur coudé)", 298, 185)
    block(40, 330, 250, 120, "Carte contrôleur", "HDMI · fournie avec la dalle")
    wire([(290, 365), (470, 365)], B, "micro-HDMI → HDMI", 298, 355)
    wire([(290, 415), (470, 415)], R, "USB-A → 5 V carte", 298, 405)
    block(40, 540, 250, 100, "Dalle 12,6\" 1920×515", "BOE NV126B5M-N41")
    wire([(165, 450), (165, 540)], G, "nappe eDP 40 broches", 177, 500)
    s.save("plan_cablage.svg")


if __name__ == "__main__":
    general()
    section()
    wiring()
