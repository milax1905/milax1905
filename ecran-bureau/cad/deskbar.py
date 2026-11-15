#!/usr/bin/env python3
"""DeskBar — boîtier paramétrique pour dalle "bar" 12,6" 1920x515 (BOE NV126B5M-N41).

Génère toutes les pièces à imprimer (STL + STEP), déjà orientées pour le plateau.

    pip install cadquery
    python3 deskbar.py                 # écrit ../stl et ../step
    python3 deskbar.py --viz DOSSIER   # exporte aussi les maillages assemblés (rendus)

Repère de modélisation (= orientation d'impression des coques) :
    X : largeur (plan de joint des deux moitiés en X = 0)
    Y : hauteur le long de la façade (0 = arête avant posée sur le bureau)
    Z : profondeur depuis la façade (Z = 0 sur le plateau, façade vers le bas)
Une fois posé, l'écran est incliné de THETA degrés vers l'arrière.
"""
import argparse
import json
import os
from math import cos, radians, sin, tan

import cadquery as cq

# --------------------------------------------------------------------------
# Paramètres — tout ce qui dépend du matériel acheté est ici
# --------------------------------------------------------------------------
# Dalle LCD (fiche technique BOE NV126B5M-N41)
PANEL_W = 315.61          # largeur hors tout
PANEL_H = 94.02           # hauteur hors tout
PANEL_T_EDGE = 3.0        # épaisseur sur les bords (typique)
PANEL_T_MAX = 5.3         # épaisseur maxi (zone carte électronique, en bas)
ACTIVE_W = 309.31         # zone d'image
ACTIVE_H = 82.97
BORDER_TOP = 3.15         # bord noir au-dessus de l'image (hypothèse, sert au tracé et à la version non tactile)
BORDER_BOTTOM = PANEL_H - ACTIVE_H - BORDER_TOP   # bord noir en dessous (~7,9)

# Verre tactile capacitif collé devant la dalle (VSDISPLAY VS126TC-B1)
TOUCH = True              # False = dalle seule, sans tactile
GLASS_W = 316.8           # largeur du verre tactile
GLASS_H = 94.9            # hauteur du verre tactile
GLASS_T = 2.0             # verre + adhésif  -> A MESURER au pied à coulisse
LIP_OVERLAP = 1.8         # recouvrement de la façade sur le bord du verre

# Jeux et épaisseurs
CLR_SIDE = 0.35           # jeu latéral dalle / coque (par côté)
CLR_TOP = 0.50            # jeu au-dessus de la dalle
REVEAL = 0.90             # version non tactile : marge entre zone d'image et bord de la fenêtre
WALL = 2.4                # parois
LIP = 1.6                 # épaisseur de la façade
COVER_T = 2.4             # épaisseur du capot arrière
COVER_CLR = 0.25          # jeu capot / coque

# Forme générale
THETA = 25.0              # inclinaison de l'écran vers l'arrière (degrés)
DEPTH = 40.0              # épaisseur du boîtier (façade -> dos)
FOOT = 88.0               # profondeur de l'appui sur le bureau
R_CORNER = 3.0            # rayon des angles extérieurs

# Bandeau lumineux
LED_HALF_W = 150.0        # demi-longueur de la fenêtre lumineuse
LED_Y0, LED_Y1 = 5.0, 10.6
STRIP_W = 12.5            # largeur réservée au ruban LED sur le capot

# Visserie (vis M3 vissées directement dans le plastique)
D_PILOT_M3 = 2.6
D_CLEAR_M3 = 3.4
D_HEAD_M3 = 6.4           # tête fraisée
D_PILOT_M25 = 2.2         # Raspberry Pi

# Raspberry Pi (carte 85 x 56, trous 58 x 49)
PI_X0, PI_Y0 = 20.0, 46.0     # coin de la carte côté ports USB-A / bord HDMI

T, C, S = tan(radians(THETA)), cos(radians(THETA)), sin(radians(THETA))

# --------------------------------------------------------------------------
# Cotes dérivées
# --------------------------------------------------------------------------
# Ce qui s'appuie contre la façade : le verre tactile s'il y en a un, sinon la dalle
FRONT_W, FRONT_H = (GLASS_W, GLASS_H) if TOUCH else (PANEL_W, PANEL_H)
STACK_T_EDGE = PANEL_T_EDGE + (GLASS_T if TOUCH else 0.0)   # épaisseur de l'empilement au bord
STACK_T_MAX = PANEL_T_MAX + (GLASS_T if TOUCH else 0.0)     # épaisseur maxi (carte de la dalle)
Z_LCD = LIP + (GLASS_T if TOUCH else 0.0)                   # face avant de la dalle
Z_COVER = DEPTH - COVER_T                  # face intérieure du capot
HALF_IN = FRONT_W / 2 + CLR_SIDE           # demi-largeur intérieure
HALF_OUT = HALF_IN + WALL                  # demi-largeur extérieure


def ybo(z):
    """Face extérieure de la semelle (paroi inclinée posée sur le bureau)."""
    return z * T


def ybi(z):
    """Face intérieure de la semelle."""
    return WALL / C + z * T


TIP_O = (FOOT * S, FOOT * C)
TIP_I = (TIP_O[0] + WALL * C, TIP_O[1] - WALL * S)
Y_GUSSET = 60.0

# Cloison inclinée du puits de lumière (imprimée avec la coque)
DIV_Y0 = LED_Y1 + 1.0                      # face côté LED, au niveau de la façade
DIV_ROOT = ybi(DEPTH) + COVER_CLR + STRIP_W + 0.2
DIV_SLOPE = (DIV_ROOT - DIV_Y0) / (Z_COVER - LIP)
DIV_DY = 2.0 * (1 + DIV_SLOPE ** 2) ** 0.5  # 2 mm d'épaisseur réelle


def div_up(z):
    """Face de la cloison côté dalle."""
    return DIV_Y0 + DIV_DY + DIV_SLOPE * (z - LIP)


# Hauteur du bas de l'empilement : juste assez pour que sa partie la plus épaisse passe devant la cloison
Y_P0 = round(div_up(LIP + STACK_T_MAX + 0.3) + 0.15, 1)
Y_IN = Y_P0 + FRONT_H + CLR_TOP            # face intérieure de la paroi haute
H = Y_IN + WALL                            # hauteur de façade
LCD_Y0 = Y_P0 + (FRONT_H - PANEL_H) / 2    # bas de la dalle (centrée derrière le verre)
ACTIVE_Y0 = LCD_Y0 + BORDER_BOTTOM         # bas de la zone d'image
if TOUCH:                                  # la fenêtre suit le contour du verre : bord de verre noir visible
    OPEN_HALF_W = FRONT_W / 2 - LIP_OVERLAP
    OPEN_Y0, OPEN_Y1 = Y_P0 + LIP_OVERLAP, Y_P0 + FRONT_H - LIP_OVERLAP
else:                                      # la fenêtre suit la zone d'image
    OPEN_HALF_W = ACTIVE_W / 2 + REVEAL
    OPEN_Y0, OPEN_Y1 = ACTIVE_Y0 - REVEAL, ACTIVE_Y0 + ACTIVE_H + REVEAL
OPEN_CHAMFER = 1.0 if TOUCH else 0.5       # chanfrein plus large : le doigt glisse sur le bord

Z0_HOOK = LIP + STACK_T_EDGE + 0.8         # départ des crochets au-dessus de la dalle

BOSS_INSET = 4.2                           # axe des vis de capot / paroi haute
Y_SCREW_TOP = Y_IN - BOSS_INSET
X_SCREWS_TOP = (4.0, 116.0, 154.3)
SCREW_CORNER = (154.3, 25.5)
SCREW_MID = (50.0, div_up(Z_COVER) + 1.5)       # vis de capot dans les goussets de la cloison
SPLICE_HOLES = ((9.0, 52.5), (9.0, 82.5))
SEAM_BOLT = (Y_IN - 11.5, 29.0)            # (y, z) du boulon d'assemblage des coques
SEAM_PEG = (Y_IN - 6.0, 24.0)
FOOT_SCREWS = ((9.0, 60.0), (23.0, 76.0))  # (x, distance le long de la semelle)

PI_HOLES = [(PI_X0 + dx, PI_Y0 + dy) for dx in (23.5, 81.5) for dy in (3.5, 52.5)]
PEG_ROWS = [46.0 + 10 * i for i in range(6)]
PEG_COLS = [-22.0 - 10 * i for i in range(13)]


# --------------------------------------------------------------------------
# Outils de construction
# --------------------------------------------------------------------------
def prism_x(pts_yz, x0, x1):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts_yz).close().extrude(x1 - x0)


def prism_y(pts_xz, y0, y1):
    plane = cq.Plane(origin=(0, y0, 0), xDir=(0, 0, 1), normal=(0, 1, 0))
    return cq.Workplane(plane).polyline([(z, x) for x, z in pts_xz]).close().extrude(y1 - y0)


def box(x0, x1, y0, y1, z0, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_z(x, y, z0, z1, d):
    return cq.Workplane("XY", origin=(x, y, z0)).circle(d / 2).extrude(z1 - z0)


def cyl_x(y, z, x0, x1, d):
    return cq.Workplane("YZ", origin=(x0, y, z)).circle(d / 2).extrude(x1 - x0)


def slot_z(xc, yc, length, width, z0, z1, angle=0):
    return (cq.Workplane("XY", origin=(xc, yc, z0)).slot2D(length, width, angle).extrude(z1 - z0))


def both(fn, *args):
    """Applique fn pour les deux moitiés (signe +1 / -1) et fusionne."""
    return fn(1, *args).union(fn(-1, *args))


def edge_box(p1, p2):
    return cq.selectors.BoxSelector(p1, p2)


def corbel(protr, x0, x1, z0=None, ztop=Z_COVER):
    """Console à 45° accrochée à la paroi haute : imprimable sans support."""
    z0 = Z0_HOOK if z0 is None else z0
    pts = [(Y_IN + 0.3, z0 - 0.3), (Y_IN - protr, z0 + protr), (Y_IN - protr, ztop), (Y_IN + 0.3, ztop)]
    return prism_x(pts, x0, x1)


def countersunk(x, y, z_face, depth=6.0):
    """Perçage M3 à tête fraisée, tête à z_face, corps vers -Z."""
    hole = cyl_z(x, y, z_face - depth, z_face + 0.01, D_CLEAR_M3)
    cone = (cq.Workplane("XY", origin=(x, y, z_face - 1.5)).circle(D_CLEAR_M3 / 2)
            .workplane(offset=1.52).circle(D_HEAD_M3 / 2).loft())
    return hole.union(cone)


# --------------------------------------------------------------------------
# Coque avant (2 moitiés)
# --------------------------------------------------------------------------
def outer_solid():
    prof = [(0, 0), (H, 0), (H, DEPTH), (Y_GUSSET, DEPTH), TIP_I, TIP_O]
    s = prism_x(prof, -HALF_OUT, HALF_OUT)
    sel = None
    for sx in (-1, 1):
        x = sx * HALF_OUT
        top = edge_box((x - 0.1, H - 0.1, 1), (x + 0.1, H + 0.1, DEPTH - 1))
        mid = (TIP_O[0] / 2, TIP_O[1] / 2)
        bot = edge_box((x - 0.1, mid[0] - 0.5, mid[1] - 0.5), (x + 0.1, mid[0] + 0.5, mid[1] + 0.5))
        sel = top + bot if sel is None else sel + top + bot
    s = s.edges(sel).fillet(R_CORNER)
    s = s.faces("<Z").edges().chamfer(0.6)
    rim = edge_box((-HALF_OUT - 1, Y_GUSSET + 1, DEPTH - 0.01), (HALF_OUT + 1, H + 1, DEPTH + 0.01))
    s = s.edges(rim).chamfer(0.8)
    return s


def build_shell():
    outer = outer_solid()
    cavity = prism_x([(ybi(LIP), LIP), (Y_IN, LIP), (Y_IN, DEPTH + 0.01), (ybi(DEPTH + 0.01), DEPTH + 0.01)],
                     -HALF_IN, HALF_IN)
    tail_void = prism_x([(ybi(DEPTH), DEPTH), (Y_GUSSET + 20, DEPTH), (Y_GUSSET + 20, 95), (ybi(95), 95)],
                        -HALF_IN, HALF_IN)
    shell = outer.cut(cavity).cut(tail_void)

    # Fenêtre d'écran et fenêtre du bandeau lumineux
    shell = shell.cut(box(-OPEN_HALF_W, OPEN_HALF_W, OPEN_Y0, OPEN_Y1, -1, LIP + 0.1))
    shell = shell.edges(edge_box((-OPEN_HALF_W - 0.1, OPEN_Y0 - 0.1, -0.01),
                                 (OPEN_HALF_W + 0.1, OPEN_Y1 + 0.1, 0.01))).chamfer(OPEN_CHAMFER)
    shell = shell.cut(box(-LED_HALF_W, LED_HALF_W, LED_Y0, LED_Y1, -1, LIP + 0.1))
    shell = shell.edges(edge_box((-LED_HALF_W - 0.1, LED_Y0 - 0.1, -0.01),
                                 (LED_HALF_W + 0.1, LED_Y1 + 0.1, 0.01))).chamfer(0.8)

    # Cloison inclinée du puits de lumière + butée basse de la dalle
    feats = prism_x([(DIV_Y0, LIP - 0.1), (DIV_Y0 + DIV_DY, LIP - 0.1), (DIV_ROOT + DIV_DY, Z_COVER),
                     (DIV_ROOT, Z_COVER)], -HALF_IN - 0.3, HALF_IN + 0.3)
    for sx in (-1, 1):                       # passages de fils du ruban LED vers l'intérieur
        for xa in (24, 136):
            feats = feats.cut(box(sx * xa, sx * (xa + 8), DIV_ROOT - 6, DIV_ROOT + DIV_DY + 4, Z_COVER - 4,
                                  Z_COVER + 1))
    feats = feats.union(prism_x([(DIV_Y0 + DIV_DY - 0.5, LIP - 0.1), (Y_P0, LIP - 0.1), (Y_P0, 4.0),
                                 (div_up(4.0) - 0.2, 4.0)], -HALF_IN, HALF_IN))

    def top_side(sgn):
        f = corbel(16.0, 0, sgn * 8.0)                                   # bloc d'assemblage central
        f = f.union(corbel(8.5, sgn * 112, sgn * 120))                   # bossage de capot
        f = f.union(corbel(8.5, sgn * (HALF_IN - 8), sgn * (HALF_IN + 0.35)))
        for xa in (36, 74):                                              # petits crochets de dalle
            pts = [(Y_IN + 0.3, Z0_HOOK - 0.3), (Y_IN - 3.5, Z0_HOOK + 3.5), (Y_IN - 3.5, Z0_HOOK + 5.5),
                   (Y_IN + 0.3, Z0_HOOK + 9.3)]
            f = f.union(prism_x(pts, sgn * xa, sgn * (xa + 8)))
        # bossage d'angle bas (dans le haut du puits de lumière)
        xe, xi = sgn * (HALF_IN + 0.35), sgn * (HALF_IN - 8)
        blk = prism_y([(xe, 21.1), (xe, Z_COVER), (xi, Z_COVER), (xi, 21.1 + 8.35)], ybo(Z_COVER) + 0.1, 30.0)
        f = f.union(blk)
        # gousset de vissage sur la cloison (dessous à 45°, au-dessus de la dalle)
        c_line = Y_P0 - (LIP + STACK_T_MAX + 0.7)
        y_face = div_up(Z_COVER) + 6.4
        z_s = (DIV_Y0 + DIV_DY - DIV_SLOPE * LIP - c_line) / (1 - DIV_SLOPE)
        pts = [(c_line + z_s, z_s), (y_face, y_face - c_line), (y_face, Z_COVER), (div_up(Z_COVER) - 0.6, Z_COVER),
               (c_line + z_s - 0.6, z_s)]
        return f.union(prism_x(pts, sgn * (SCREW_MID[0] - 4), sgn * (SCREW_MID[0] + 4)))

    feats = feats.union(both(top_side)).intersect(outer)
    shell = shell.union(feats)

    # Perçages
    cuts = cyl_x(SEAM_BOLT[0], SEAM_BOLT[1], -9, 9, D_CLEAR_M3)
    for sgn in (1, -1):
        for x in X_SCREWS_TOP:
            cuts = cuts.union(cyl_z(sgn * x, Y_SCREW_TOP, Z_COVER - 10, Z_COVER + 1, D_PILOT_M3))
        cuts = cuts.union(cyl_z(sgn * SCREW_CORNER[0], SCREW_CORNER[1], Z_COVER - 9.5, Z_COVER + 1, D_PILOT_M3))
        cuts = cuts.union(cyl_z(sgn * SCREW_MID[0], SCREW_MID[1], Z_COVER - 7.5, Z_COVER + 1, D_PILOT_M3))
        for x, dist in FOOT_SCREWS:                                      # vis de l'éclisse de pied
            plane = cq.Plane(origin=(sgn * x, dist * S, dist * C), xDir=(1, 0, 0), normal=(0, C, -S))
            hole = cq.Workplane(plane).workplane(offset=-0.01).circle(D_CLEAR_M3 / 2).extrude(6)
            cone = (cq.Workplane(plane).workplane(offset=-0.01).circle(D_HEAD_M3 / 2)
                    .workplane(offset=1.5).circle(D_CLEAR_M3 / 2).loft())
            cuts = cuts.union(hole).union(cone)
    return shell.cut(cuts)


def shell_half(shell, sgn):
    half = shell.intersect(box(0, sgn * (HALF_OUT + 5), -20, H + 20, -5, 120) if sgn > 0
                           else box(-(HALF_OUT + 5), 0, -20, H + 20, -5, 120))
    if sgn > 0:      # pion de centrage
        half = half.union(cyl_x(SEAM_PEG[0], SEAM_PEG[1], -2.0, 0.5, 4.0))
    else:            # logement du pion + empreinte d'écrou M3
        half = half.cut(cyl_x(SEAM_PEG[0], SEAM_PEG[1], -2.5, 0.01, 4.5))
        nut = (cq.Workplane("YZ", origin=(-8.01, SEAM_BOLT[0], SEAM_BOLT[1]))
               .polygon(6, 5.75 / cos(radians(30))).extrude(2.8))
        half = half.cut(nut)
    return half


# --------------------------------------------------------------------------
# Capot arrière (2 moitiés) : porte toute l'électronique
# --------------------------------------------------------------------------
def build_cover():
    xw = HALF_IN - COVER_CLR
    cover = box(-xw, xw, ybi(DEPTH) + COVER_CLR, Y_IN - COVER_CLR, Z_COVER, DEPTH)
    zt = LIP + STACK_T_EDGE + 2.0            # les doigts s'arrêtent 2 mm derrière la dalle (mousse entre les deux)

    def side(sgn):
        # doigt d'appui sur le bord latéral de la dalle
        f = box(sgn * 154.4, sgn * 157.6, 56, 68, zt, Z_COVER + 0.1)
        f = f.union(prism_y([(sgn * 154.5, Z_COVER + 0.1), (sgn * 146.0, Z_COVER + 0.1), (sgn * 154.5, 22.0)],
                            60.5, 63.5))
        # doigts d'appui sur le bord haut de la dalle
        y1 = LCD_Y0 + PANEL_H - 0.2
        for xa in (24, 92):
            f = f.union(box(sgn * xa, sgn * (xa + 10), y1 - 2.8, y1, zt, Z_COVER + 0.1))
            f = f.union(prism_x([(y1 - 2.7, Z_COVER + 0.1), (y1 - 10.8, Z_COVER + 0.1), (y1 - 2.7, 24.0)],
                                sgn * (xa + 3.8), sgn * (xa + 6.2)))
        return f

    cover = cover.union(both(side))

    # Entretoises Raspberry Pi (côté X > 0)
    for x, y in PI_HOLES:
        cover = cover.union(cyl_z(x, y, Z_COVER - 4.0, Z_COVER + 0.1, 6.5))
    # Nervures perforées pour la carte contrôleur (côté X < 0)
    for y in PEG_ROWS:
        cover = cover.union(box(PEG_COLS[-1] - 4, PEG_COLS[0] + 4, y - 2, y + 2, Z_COVER - 3.0, Z_COVER + 0.1))

    cuts = None

    def add(c):
        nonlocal cuts
        cuts = c if cuts is None else cuts.union(c)

    for x, y in PI_HOLES:
        add(cyl_z(x, y, Z_COVER - 4.1, DEPTH - 0.8, D_PILOT_M25))
    for y in PEG_ROWS:
        for x in PEG_COLS:
            add(cyl_z(x, y, Z_COVER - 3.1, DEPTH - 0.6, D_PILOT_M3))
    for sgn in (1, -1):
        for x in X_SCREWS_TOP:
            add(countersunk(sgn * x, Y_SCREW_TOP, DEPTH))
        add(countersunk(sgn * SCREW_CORNER[0], SCREW_CORNER[1], DEPTH))
        add(countersunk(sgn * SCREW_MID[0], SCREW_MID[1], DEPTH))
        for x, y in SPLICE_HOLES:
            add(countersunk(sgn * x, y, DEPTH))
    # Aérations
    for i in range(11):
        for y0, y1 in ((58, 76), (80, 94)):
            add(slot_z(30 + 8 * i, (y0 + y1) / 2, y1 - y0, 2.4, Z_COVER - 1, DEPTH + 1, 90))
    for xc in (75, 105):
        add(slot_z(xc, 41.5, 22, 3.0, Z_COVER - 1, DEPTH + 1))
    for xc in (-40, -70, -100, -130):
        for yc in (61, 71, 81):
            add(slot_z(xc, yc, 22, 2.5, Z_COVER - 1, DEPTH + 1))
    # Passage du câble d'alimentation + sonde
    add(slot_z(142, 42.5, 16, 9, Z_COVER - 1, DEPTH + 1))
    return cover.cut(cuts)


def cover_half(cover, sgn):
    xw = HALF_IN
    return cover.intersect(box(0.15, xw, -20, H + 20, -5, 60) if sgn > 0 else box(-xw, -0.15, -20, H + 20, -5, 60))


# --------------------------------------------------------------------------
# Petites pièces
# --------------------------------------------------------------------------
def build_cover_splice():
    """Eclisse qui réunit les deux moitiés du capot (vissée depuis l'extérieur)."""
    p = box(-15, 15, 45.5, 89.5, Z_COVER - 3.5, Z_COVER)
    for sgn in (1, -1):
        for x, y in SPLICE_HOLES:
            p = p.cut(cyl_z(sgn * x, y, Z_COVER - 4, Z_COVER + 1, D_PILOT_M3))
    return p


def build_foot_splice():
    """Eclisse de pied : réunit les deux semelles à l'arrière. Modélisée à plat."""
    p = cq.Workplane("XY").box(60, 26, 6, centered=(True, True, False))
    p = p.edges("|Z").fillet(3)
    for sgn in (1, -1):
        for x, dist in FOOT_SCREWS:
            p = p.cut(cyl_z(sgn * x, dist - 68.0, -1, 7, D_PILOT_M3))
    return p


def build_diffuser():
    width = (DIV_Y0 + DIV_SLOPE * 0.8) - ybi(LIP + 0.8) - 0.4      # largeur du fond du puits, moins le jeu
    return cq.Workplane("XY").box(2 * LED_HALF_W - 1.0, round(width, 1), 0.8, centered=(True, True, False))


def build_claw():
    """Griffe réglable pour brider une carte (profil extrudé, à imprimer sur le flanc)."""
    prof = [(-16, 0), (1.8, 0), (1.8, 3.0), (0, 3.0), (0, 4.9), (1.8, 4.9), (1.8, 6.7), (-3, 6.7), (-3, 3.5),
            (-16, 3.5)]
    c = cq.Workplane("XY").polyline(prof).close().extrude(8)
    slot = (cq.Workplane(cq.Plane(origin=(-9.5, -1, 4), xDir=(1, 0, 0), normal=(0, 1, 0)))
            .slot2D(10.4, D_CLEAR_M3).extrude(6))
    return c.cut(slot)


def build_sensor_pod():
    base = cq.Workplane("XY").box(31, 23, 8, centered=(True, True, False)).edges("|Z").fillet(2.5)
    base = base.cut(cq.Workplane("XY", origin=(0, 0, 1.6)).box(27.4, 19.4, 8, centered=(True, True, False)))
    base = base.cut(box(-16, -12, -2.6, 2.6, 5.0, 9))            # sortie du câble
    for i in range(5):
        base = base.cut(slot_z(-8 + 4 * i, 0, 13, 1.8, -1, 2, 90))
    lid = cq.Workplane("XY").box(31, 23, 1.6, centered=(True, True, False)).edges("|Z").fillet(2.5)
    rim = (cq.Workplane("XY", origin=(0, 0, 1.6)).rect(27.0, 19.0).rect(24.6, 16.6).extrude(2.0))
    lid = lid.union(rim).cut(box(-16, -11, -3.2, 3.2, 1.6, 4))
    for i in range(5):
        lid = lid.cut(slot_z(-8 + 4 * i, 0, 13, 1.8, -1, 2, 90))
    return base, lid


# --------------------------------------------------------------------------
# Composants (pour les rendus uniquement — pas à imprimer)
# --------------------------------------------------------------------------
def dummies():
    d = {}
    lcd = box(-PANEL_W / 2, PANEL_W / 2, LCD_Y0, LCD_Y0 + PANEL_H, Z_LCD, Z_LCD + PANEL_T_EDGE).union(
        box(-PANEL_W / 2 + 20, PANEL_W / 2 - 20, LCD_Y0 + 0.5, LCD_Y0 + 8, Z_LCD + PANEL_T_EDGE, Z_LCD + PANEL_T_MAX))
    if TOUCH:
        lcd = lcd.union(box(-GLASS_W / 2, GLASS_W / 2, Y_P0, Y_P0 + GLASS_H, LIP, Z_LCD))
    d["dalle"] = lcd
    zb = Z_COVER - 4.0
    pi = box(PI_X0, PI_X0 + 85, PI_Y0, PI_Y0 + 56, zb - 1.4, zb)
    pi = pi.union(box(PI_X0 - 2, PI_X0 + 19, PI_Y0 + 2, PI_Y0 + 17, zb - 17.4, zb - 1.4))     # USB
    pi = pi.union(box(PI_X0 - 2, PI_X0 + 19, PI_Y0 + 20, PI_Y0 + 35, zb - 17.4, zb - 1.4))    # USB
    pi = pi.union(box(PI_X0 - 2, PI_X0 + 19, PI_Y0 + 38, PI_Y0 + 54, zb - 15.0, zb - 1.4))    # Ethernet
    pi = pi.union(box(PI_X0 + 27, PI_X0 + 78, PI_Y0 + 50, PI_Y0 + 55, zb - 10.0, zb - 1.4))   # GPIO
    pi = pi.union(box(PI_X0 + 30, PI_X0 + 72, PI_Y0 + 12, PI_Y0 + 46, zb - 12.0, zb - 1.4))   # ventilateur
    d["raspberry_pi"] = pi
    zc = Z_COVER - 3.0 - 3.0
    drv = box(-125, -43, 42, 102, zc - 1.6, zc).union(box(-110, -80, 57, 82, zc - 4, zc - 1.6))
    d["carte_controleur"] = drv
    d["ruban_led"] = box(-LED_HALF_W + 2, LED_HALF_W - 2, DIV_ROOT - 12.2, DIV_ROOT - 0.2,
                         Z_COVER - 2.2, Z_COVER)
    return d


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
def to_bed(wp):
    """Pose la pièce sur le plateau (Z mini = 0) et la centre en X/Y."""
    bb = wp.val().BoundingBox()
    return wp.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))


def flip(wp):
    return wp.rotate((0, 0, 0), (1, 0, 0), 180)


def world(wp, dz=0.0, dy=0.0):
    """Repère de modélisation -> appareil posé sur le bureau (Z vers le haut, vue depuis +Y)."""
    return wp.translate((0, dy, dz)).rotate((0, 0, 0), (1, 0, 0), 90 + THETA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--viz", help="dossier où écrire les maillages assemblés pour les rendus")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    out_stl, out_step = os.path.join(here, "..", "stl"), os.path.join(here, "..", "step")
    os.makedirs(out_stl, exist_ok=True)
    os.makedirs(out_step, exist_ok=True)

    shell = build_shell()
    cover = build_cover()
    sh = {1: shell_half(shell, 1), -1: shell_half(shell, -1)}
    cv = {1: cover_half(cover, 1), -1: cover_half(cover, -1)}
    cover_splice, foot_splice, diffuser, claw = build_cover_splice(), build_foot_splice(), build_diffuser(), build_claw()
    pod, pod_lid = build_sensor_pod()
    gauge_box = box(-200, 200, -20, 200, -1, Z0_HOOK + 3.1)

    # Nom -> (pièce orientée pour l'impression, quantité)
    parts = {
        "01_coque_gauche": (to_bed(sh[1]), 1),
        "02_coque_droite": (to_bed(sh[-1]), 1),
        "03_capot_pi": (to_bed(flip(cv[1])), 1),
        "04_capot_controleur": (to_bed(flip(cv[-1])), 1),
        "05_diffuseur": (to_bed(diffuser.rotate((0, 0, 0), (0, 0, 1), 45)), 1),
        "06_eclisse_capot": (to_bed(flip(cover_splice)), 1),
        "07_eclisse_pied": (to_bed(foot_splice), 1),
        "08_griffe_carte": (to_bed(claw), 4),
        "09_boitier_sonde": (to_bed(pod), 1),
        "10_couvercle_sonde": (to_bed(pod_lid), 1),
        "00_gabarit_test_gauche": (to_bed(sh[1].intersect(gauge_box)), 1),
        "00_gabarit_test_droite": (to_bed(sh[-1].intersect(gauge_box)), 1),
    }
    report = {}
    for name, (wp, qty) in parts.items():
        cq.exporters.export(wp, os.path.join(out_stl, name + ".stl"), tolerance=0.03, angularTolerance=0.2)
        cq.exporters.export(wp, os.path.join(out_step, name + ".step"))
        bb, vol = wp.val().BoundingBox(), wp.val().Volume() / 1000.0
        report[name] = {"qty": qty, "x": round(bb.xlen, 1), "y": round(bb.ylen, 1), "z": round(bb.zlen, 1),
                        "cm3": round(vol, 1), "solids": wp.solids().size()}
        print(f"{name:26s} x{qty}  {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm   {vol:6.1f} cm3"
              f"   solides={wp.solids().size()}")
    with open(os.path.join(out_stl, "pieces.json"), "w") as f:
        json.dump(report, f, indent=1)

    if args.viz:
        os.makedirs(args.viz, exist_ok=True)
        dm = dummies()
        foot_placed = (foot_splice.rotate((0, 0, 0), (0, 0, 1), 180).rotate((0, 0, 0), (1, 0, 0), -(90 + THETA))
                       .translate((0, 68 * S + WALL * C, 68 * C - WALL * S)))
        asm = {
            "coque_gauche": (sh[1], "body"), "coque_droite": (sh[-1], "body"),
            "capot_pi": (cv[1], "cover"), "capot_controleur": (cv[-1], "cover"),
            "eclisse_capot": (cover_splice, "cover"), "eclisse_pied": (foot_placed, "body"),
            "diffuseur": (diffuser.translate((0, (ybi(LIP + 0.8) + DIV_Y0 + DIV_SLOPE * 0.8) / 2, LIP)), "diffuser"),
            "dalle": (dm["dalle"], "panel"), "raspberry_pi": (dm["raspberry_pi"], "pcb"),
            "carte_controleur": (dm["carte_controleur"], "pcb2"), "ruban_led": (dm["ruban_led"], "led"),
        }
        meta = {"theta": THETA, "parts": {}, "dims": {
            "W": round(2 * HALF_OUT, 2), "H": round(H, 2), "height": round(H * C, 1), "depth": FOOT,
            "open": [OPEN_HALF_W, OPEN_Y0, OPEN_Y1], "led": [LED_HALF_W, LED_Y0, LED_Y1], "S": S, "C": C, "touch": TOUCH}}
        for name, (wp, mat) in asm.items():
            cq.exporters.export(wp, os.path.join(args.viz, name + ".stl"), tolerance=0.05, angularTolerance=0.25)
            meta["parts"][name] = mat
        with open(os.path.join(args.viz, "meta.json"), "w") as f:
            json.dump(meta, f, indent=1)

    print(f"\nHors tout posé : {2 * HALF_OUT:.1f} (L) x {FOOT:.0f} (P) x {H * C:.1f} (H) mm — façade {H:.1f} mm, "
          f"inclinaison {THETA:.0f} deg")


if __name__ == "__main__":
    main()
