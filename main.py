"""
PROYECTO GARRA — Main  (Fase 3 final + Fase 4 + Fase 5 rev.3)
=========================================================
Ventana 1280×720:
  Simulador  800×720  izquierda   (coords matemáticas Y↑)
  Panel Mat  480×720  derecha

Controles
─────────
  ←  /  →       Traslación en X del brazo
  ↑  /  ↓       Escala del brazo (profundidad Z simulada)
  ESPACIO        Abrir / Cerrar pinzas
                   - Al CERRAR: intenta capturar caja si cumple criterios
                   - Al ABRIR:  suelta la caja capturada (si hay alguna)
  TAB            Cicla nodo seleccionado en el panel
  Click izq      Selecciona nodo más cercano
  D              Activa/desactiva ejes y etiquetas debug
  ESC            Salir

Fase 5 rev.3 — Corrección de Offset de Puntas de Pinza
────────────────────────────────────────────────────────
  Problema anterior: el punto de captura y el ancla de re-parenting
  apuntaban a las BISAGRAS de las pinzas (pivot_img Y=734 en el PNG),
  provocando que el sprite de la caja quedara incrustado dentro de los
  sprites de las pinzas al capturar.

  Solución aplicada — OFFSET_PINZAS_Y:
  ─────────────────────────────────────
  El sprite de cada pinza mide 800×800 px.
  La bisagra (pivot_img) está en Y_png = 734 → Y_math = 800−734 = 66 px.
  La punta estimada está en Y_png ≈ 790 → distancia bisagra→punta en PNG = 56 px.
  Con escala local de pinza = 0.5:
      OFFSET_PINZAS_Y = 56 × 0.5 = 28 px   (en espacio local del brazo, Y↓ math)

  Se aplica en DOS lugares únicamente:
    1. _get_pinzas_tip(): punto de colisión desplazado −28 en Y (puntas).
    2. CAJA_ANCHOR_TY: −364 − 28 = −392   (la caja cuelga de las puntas).

  CAJA_Y se recalcula para que las cajas estén alineadas con las puntas
  cuando el brazo alcanza BRAZO_SCALE_MAX:
      Y_puntas = 600 + (−392 × 0.625) = 600 − 245 = 355.0

  Los pivotes del brazo y de las pinzas NO se modifican; son correctos
  para la rotación y jerarquía de transformaciones.

Pivotes calibrados por el Director Técnico (Gemini):
  brazo.png     pivot_img = (414, 461)   — punto de dibujo: articulación brazo
  pinza_izq.png pivot_img = (622, 734)   — bisagra izq (Y↓ PNG)
  pinza_der.png pivot_img = (145, 734)   — bisagra der (Y↓ PNG)
  caja.png      pivot_img = (406, 411)   — centro de la caja

Traslaciones locales calibradas:
  PinzaIzq respecto al brazo: tx = -61,  ty = -364
  PinzaDer respecto al brazo: tx =  59,  ty = -364
"""

import sys
import os
import math
import numpy as np
import pygame

from math_engine import MathEngine
from scene_graph import WorldNode, SceneNode
from renderer    import Renderer, WORLD_W, WORLD_H
from math_panel  import MathPanel


# ─────────────────────────────────────────────────────────────────── #
#  Constantes                                                         #
# ─────────────────────────────────────────────────────────────────── #
WINDOW_W  = 1280
WINDOW_H  = 720
PANEL_W   = 480
FPS       = 60

# Velocidades de control
MOVE_SPEED  = 180.0    # px/s en X
SCALE_SPEED = 0.45     # factor/s para escala Z

# ── Escala de referencia del primer plano (cajas) ────────────────── #
ESCALA_FRENTE = 0.15            # escala base de las cajas — NO tocar

# Límites originales del brazo
BRAZO_X_MIN     = 60.0
BRAZO_X_MAX     = 740.0
BRAZO_SCALE_MIN = 0.20
BRAZO_SCALE_MAX = 0.625

# Estado inicial del brazo — "Home": fondo izquierdo
BRAZO_INIT_X     = BRAZO_X_MIN
BRAZO_INIT_Y     = 600.0
BRAZO_INIT_SCALE = BRAZO_SCALE_MIN

# Ángulos de pinzas
PINZA_ABIERTA_IZQ  =  0.0
PINZA_CERRADA_IZQ  =  28.0
PINZA_ABIERTA_DER  =  0.0
PINZA_CERRADA_DER  = -28.0

# ── OFFSET_PINZAS_Y (rev.5) ──────────────────────────────────────── #
#
# Distancia VISUAL en pantalla desde la bisagra hasta la PUNTA de las
# pinzas, expresada en UNIDADES MATEMÁTICAS (Y↑) para que sea coherente
# con las posiciones globales que maneja el scene graph.
#
# El renderer usa pivot_img en espacio Y↓ del sprite PNG (Pygame).
# Para las pinzas el código asigna pivot_img.y = 66 (= 800−734, espacio
# Y↑). El renderer lo interpreta como Y↓ PNG, por lo que el sprite se
# desplaza hacia abajo en pantalla respecto al pivot matemático:
#
#   s_global_pinza = PINZA_SCALE_LOCAL × BRAZO_SCALE_MAX = 0.5 × 0.625 = 0.3125
#   center_sprite  = 800 × 0.3125 / 2 = 125 px  (semialtura del sprite escalado)
#   offset_y       = pivot_img.y × s_global − center = 66×0.3125 − 125 = −104.375
#   rot_center.y   = screen_y_bisagra − offset_y = screen_y_bisagra + 104.375
#
# La punta del sprite (Y_png = 790) en pantalla:
#   pos_punta_en_sprite = 790 × s_global = 246.875 px desde el borde sup
#   screen_y_punta = (rot_center.y − 125) + 246.875 = screen_y_bisagra + 225.5 px
#
# En coordenadas matemáticas (Y↑):
#   ty_bisagra_mundo = 600 + (−364) × 0.625 = 372.5
#   screen_y_bisagra = 720 − 372.5 = 347.5
#   screen_y_punta   = 347.5 + 225.5 = 573.0  (con punta y_png=790)
#   ty_punta_mundo   = 720 − 573.0 = 147.0
#
# _get_pinzas_tip() trabaja en coordenadas MUNDO (Y↑). El desplazamiento
# que debe aplicar es: bisagra_Y − punta_Y = 372.5 − 147.0 = 225.5 px.
# Ese valor ya lleva toda la cadena de escalas, así que lo aplicamos como
# offset FIJO en coordenadas mundo, SIN multiplicar por ninguna escala
# adicional (la escala ya está implícita en la derivación visual anterior).
#
# Para escala variable (brazo en posición intermedia), escalamos linealmente:
#   OFFSET_PINZAS_Y_MUNDO_MAX = 225.5 px  a BRAZO_SCALE_MAX=0.625
#   En un frame cualquiera: offset = 225.5 × (s_brazo_actual / BRAZO_SCALE_MAX)
#   Equivalente: offset = OFFSET_PINZAS_Y_PNG_FACTOR × s_pinza_global
#   donde OFFSET_PINZAS_Y_PNG_FACTOR = (790−66) / (0.5×0.625) × s_global  ...
#
# SIMPLIFICACIÓN PRÁCTICA: expresamos el offset como:
#   offset_mundo = OFFSET_PINZAS_Y_FACTOR × s_pinza_global
#   OFFSET_PINZAS_Y_FACTOR = (790 − 66)  ← dist en PNG desde pivot hasta punta
# Esto da: 724 × 0.3125 = 226.25 px ≈ 225.5 ✓
#
OFFSET_PINZAS_Y_FACTOR = 724.0  # dist en px PNG: punta(790) − pivot_img.y(66)

# ── Fase 5: parámetros de captura ─────────────────────────────────── #
CAPTURE_DIST_MAX   = 50.0
CAPTURE_SCALE_TOL  = 0.05

# CAJA_ANCHOR_TY (rev.5):
# Cuando la caja queda capturada, su traslación local respecto al brazo
# debe colocarla en las PUNTAS de las pinzas, no en las bisagras.
#
# En espacio LOCAL del brazo:
#   ty_bisagra_local  = −364  (ya estaba calibrado)
#   dist_bisagra_punta en espacio LOCAL brazo
#     = OFFSET_PINZAS_Y_FACTOR × PINZA_SCALE_LOCAL
#     = 724 × 0.5 = 362 px (hacia abajo → negativo en Y↑)
#   CAJA_ANCHOR_TY = −364 − 362 = −726
#
# Verificación en espacio MUNDO (a BRAZO_SCALE_MAX = 0.625):
#   ty_punta_mundo = 600 + (−726) × 0.625 = 600 − 453.75 = 146.25
#   → coincide con ty_punta_mundo ≈ 147 calculado por cadena visual ✓
#
CAJA_ANCHOR_TX = 0.0
CAJA_ANCHOR_TY = -364.0 - (OFFSET_PINZAS_Y_FACTOR * 0.5)  # = −364 − 362 = −726.0

# Colores
BG_SIM   = (12, 14, 22)


# ─────────────────────────────────────────────────────────────────── #
#  Carga de sprites                                                   #
# ─────────────────────────────────────────────────────────────────── #

def load_sprites(asset_dir: str) -> dict[str, pygame.Surface]:
    sprites: dict[str, pygame.Surface | None] = {}
    files = {
        "brazo":      "brazo.png",
        "pinza_izq":  "pinza_izq.png",
        "pinza_der":  "pinza_der.png",
        "caja":       "caja.png",
    }
    for key, fname in files.items():
        path = os.path.join(asset_dir, fname)
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
            sprites[key] = surf
            print(f"  ✓  {fname}  ({surf.get_width()}×{surf.get_height()})")
        else:
            sprites[key] = None
            print(f"  ⚠  {fname} no encontrado — usando rect debug")
    return sprites


# ─────────────────────────────────────────────────────────────────── #
#  Construcción del Scene Graph                                       #
# ─────────────────────────────────────────────────────────────────── #

def build_scene(sprites: dict) -> tuple[WorldNode, SceneNode, SceneNode, SceneNode, list[SceneNode]]:
    world = WorldNode()

    # ── 1. Cajas — Un solo plano frontal ──────────────────────────── #
    #
    # CAJA_SCALE = ESCALA_FRENTE = 0.15  (NO se modifica)
    #
    # CAJA_Y (rev.5 — derivado del pipeline VISUAL completo del renderer):
    #
    # El renderer desplaza el sprite de cada pinza porque pivot_img.y=66
    # (espacio Y↑) es interpretado como Y↓ en el PNG. Eso hace que el
    # sprite baje visualmente, colocando las puntas MUCHO más abajo de lo
    # que indica la bisagra en coordenadas mundo.
    #
    # Cadena completa a BRAZO_SCALE_MAX = 0.625:
    #   s_global_pinza     = 0.5 × 0.625 = 0.3125
    #   ty_bisagra_mundo   = 600 + (−364) × 0.625 = 372.5
    #   screen_y_bisagra   = 720 − 372.5 = 347.5
    #   offset_y_renderer  = 66 × 0.3125 − 125 = −104.375
    #   rot_center.y       = 347.5 + 104.375 = 451.875
    #   pos_punta_sprite   = 790 × 0.3125 = 246.875 px desde borde sup
    #   screen_y_punta     = (451.875 − 125) + 246.875 = 573.75
    #   CAJA_Y             = 720 − 573.75 = 146.25  ← Y↑ mundo
    #
    # → El pivot de la caja (406, 411 en PNG ≈ centro del sprite de 120px)
    #   queda en screen_y = 720 − 146.25 = 573.75, alineado con las puntas
    #   visuales de las pinzas. Distancia vertical de colisión ≈ 0. ✓
    #
    # X distribuidas para cubrir el área de juego (0…800 px):
    #   Caja1 (izq): tx = 200
    #   Caja2 (cen): tx = 400
    #   Caja3 (der): tx = 600
    #
    CAJA_SCALE = ESCALA_FRENTE   # 0.15 — NO tocar

    # CAJA_Y calculado con la cadena visual completa (ver derivación arriba)
    _s_pinza_global  = 0.5 * BRAZO_SCALE_MAX                      # 0.3125
    _center_sprite   = 800.0 * _s_pinza_global / 2                # 125 px
    _ty_bisagra      = BRAZO_INIT_Y + (-364.0) * BRAZO_SCALE_MAX  # 372.5
    _screen_y_bisag  = WORLD_H - _ty_bisagra                      # 347.5
    _offset_y_rend   = 66.0 * _s_pinza_global - _center_sprite    # −104.375
    _rot_center_y    = _screen_y_bisag - _offset_y_rend           # 451.875
    _punta_en_sprite = 790.0 * _s_pinza_global                    # 246.875
    _screen_y_punta  = (_rot_center_y - _center_sprite) + _punta_en_sprite  # 573.75
    CAJA_Y           = WORLD_H - _screen_y_punta                  # 146.25

    caja_cfg = [
        {"name": "Caja1", "tx": 200, "rot":  6},
        {"name": "Caja2", "tx": 400, "rot": -5},
        {"name": "Caja3", "tx": 600, "rot": 10},
    ]
    cajas: list[SceneNode] = []
    for cfg in caja_cfg:
        c = SceneNode(name=cfg["name"], pivot=(0, 0), color=(210, 160, 50), size=(80, 80))
        c.pivot_img = (406, 389)   # Y invertida: 800 - 411 = 389
        c.sprite    = sprites["caja"]
        c.set_translation(cfg["tx"], CAJA_Y)
        c.set_scale(CAJA_SCALE, CAJA_SCALE)
        c.set_rotation(cfg["rot"])
        world.add_child(c)
        cajas.append(c)

    # ── 2. Brazo y Pinzas ──────────────────────────────────────────── #
    brazo = SceneNode(name="Brazo", pivot=(0, 0), color=(70, 130, 200), size=(80, 180))
    brazo.pivot_img = (414, 339)   # Y invertida: 800 - 461 = 339
    brazo.sprite    = sprites["brazo"]
    brazo.set_translation(BRAZO_INIT_X, BRAZO_INIT_Y)
    brazo.set_scale(BRAZO_INIT_SCALE, BRAZO_INIT_SCALE)

    pinza_izq = SceneNode(name="PinzaIzq", pivot=(0, 0), color=(100, 180, 100), size=(50, 80))
    pinza_izq.pivot_img = (622, 66)   # Y invertida: 800 - 734 = 66
    pinza_izq.sprite    = sprites["pinza_izq"]
    pinza_izq.set_translation(-61, -364)
    pinza_izq.set_scale(0.5, 0.5)
    pinza_izq.set_rotation(PINZA_ABIERTA_IZQ)

    pinza_der = SceneNode(name="PinzaDer", pivot=(0, 0), color=(180, 100, 100), size=(50, 80))
    pinza_der.pivot_img = (145, 66)   # Y invertida: 800 - 734 = 66
    pinza_der.sprite    = sprites["pinza_der"]
    pinza_der.set_translation(59, -364)
    pinza_der.set_scale(0.5, 0.5)
    pinza_der.set_rotation(PINZA_ABIERTA_DER)

    brazo.add_child(pinza_izq)
    brazo.add_child(pinza_der)
    world.add_child(brazo)

    world.update()
    return world, brazo, pinza_izq, pinza_der, cajas


# ─────────────────────────────────────────────────────────────────── #
#  Fase 5 — Lógica de colisión y re-parenting                        #
# ─────────────────────────────────────────────────────────────────── #

def _get_global_position(node: SceneNode) -> np.ndarray:
    """Extrae (tx, ty) de la columna de traslación de la matriz global 3×3."""
    m = node.global_matrix
    return np.array([m[0, 2], m[1, 2]])


def _get_global_scale_x(node: SceneNode) -> float:
    """Extrae la escala global en X como norma de la primera columna."""
    m = node.global_matrix
    return float(np.linalg.norm(m[:2, 0]))


def _get_pinzas_tip(pinza_izq: SceneNode, pinza_der: SceneNode) -> np.ndarray:
    """
    Calcula el punto de captura: punto medio entre las PUNTAS VISUALES de
    ambas pinzas, en coordenadas matemáticas (Y↑, espacio mundo).

    Rev.5 — Derivación desde el pipeline real del renderer:
    ────────────────────────────────────────────────────────
    El renderer usa pivot_img.y=66 como si fuera Y↓ del PNG.
    Eso desplaza el sprite hacia abajo en pantalla respecto a la bisagra:
      offset_y = pivot_img.y × s_global − center_sprite
               = 66 × s − (800s/2) = s(66 − 400) = −334s
      rot_center.y = screen_y_bisagra + 334 × s_global

    La punta del sprite (Y_png=790) en pantalla:
      screen_y_punta = (rot_center.y − 400s) + 790s
                     = screen_y_bisagra + 334s − 400s + 790s
                     = screen_y_bisagra + 724s

    En coordenadas mundo (Y↑):
      ty_bisagra_mundo = 720 − screen_y_bisagra
      ty_punta_mundo   = 720 − (screen_y_bisagra + 724s)
                       = ty_bisagra_mundo − 724 × s_global

    Por tanto:
      tip_y_offset = OFFSET_PINZAS_Y_FACTOR × s_global
      con OFFSET_PINZAS_Y_FACTOR = 724  (= 790 − 66, dist punta−pivot en PNG)

    Se escala con s_pinza_global en cada frame → sigue la profundidad Z. ✓
    """
    p_l = _get_global_position(pinza_izq)
    p_r = _get_global_position(pinza_der)
    mid = (p_l + p_r) / 2.0

    # s_global incluye escala_local_pinza(0.5) × escala_brazo(variable)
    s_pinza = _get_global_scale_x(pinza_izq)

    # Desplazamiento en Y↑ mundo: bisagra → punta visual (negativo = baja)
    tip_y_offset = OFFSET_PINZAS_Y_FACTOR * s_pinza  # ej: 724×0.3125 = 226.25

    return np.array([mid[0], mid[1] - tip_y_offset])


def intentar_captura(
    world: WorldNode,
    brazo: SceneNode,
    pinza_izq: SceneNode,
    pinza_der: SceneNode,
    cajas: list[SceneNode]
) -> SceneNode | None:
    """
    Evalúa si alguna caja libre cumple los criterios de captura.

    Criterios simultáneos:
      1. d(Pt, P_caja) < CAPTURE_DIST_MAX   — Pt = punta de pinzas (rev.3)
      2. |t_brazo_norm − t_caja_norm| < CAPTURE_SCALE_TOL

    Rev.3: usa _get_pinzas_tip() en vez de _get_pinzas_center().
    """
    world.update()

    # ── Rev.3: punto de colisión = PUNTAS de las pinzas ─────────────
    pt      = _get_pinzas_tip(pinza_izq, pinza_der)
    s_brazo = _get_global_scale_x(brazo)

    rango_brazo = BRAZO_SCALE_MAX - BRAZO_SCALE_MIN
    if rango_brazo > 1e-6:
        t_brazo = (s_brazo - BRAZO_SCALE_MIN) / rango_brazo
    else:
        t_brazo = 1.0
    t_brazo = max(0.0, min(1.0, t_brazo))

    for caja in cajas:
        if caja.parent is not world:
            continue

        p_caja = _get_global_position(caja)
        s_caja = _get_global_scale_x(caja)

        # ── Criterio 1: Distancia euclidiana punta→caja ──────────── #
        dist = MathEngine.get_euclidean_distance(pt.tolist(), p_caja.tolist())
        if dist >= CAPTURE_DIST_MAX:
            continue

        # ── Criterio 2: Equivalencia de plano Z ──────────────────── #
        t_caja = 1.0   # cajas siempre en primer plano

        if abs(t_brazo - t_caja) >= CAPTURE_SCALE_TOL:
            continue

        # ── Ambos criterios cumplidos → RE-PARENTING ─────────────── #
        if s_brazo > 1e-6:
            s_rel = s_caja / s_brazo
        else:
            s_rel = 1.0

        world.remove_child(caja)
        brazo.add_child(caja)

        # Nueva matriz local: caja anclada en las PUNTAS (rev.4)
        # CAJA_ANCHOR_TY = -397  (bisagra −364 − offset punta 33)
        caja.set_translation(CAJA_ANCHOR_TX, CAJA_ANCHOR_TY)
        caja.set_rotation(0.0)
        caja.set_scale(s_rel, s_rel)

        print(f"  [Fase5 rev.4] CAPTURA: {caja.name}  "
              f"dist={dist:.1f}  tip=({pt[0]:.1f},{pt[1]:.1f})  "
              f"t_brazo={t_brazo:.3f}  s_rel={s_rel:.4f}")
        return caja

    return None


def liberar_caja(
    world: WorldNode,
    brazo: SceneNode,
    caja_capturada: SceneNode
) -> None:
    """
    Suelta la caja capturada y la devuelve al Mundo.
    La nueva matriz local = última M_global (sin salto visual).
    """
    m_global_actual = caja_capturada.global_matrix.copy()

    brazo.remove_child(caja_capturada)
    world.add_child(caja_capturada)

    tx  = float(m_global_actual[0, 2])
    ty  = float(m_global_actual[1, 2])
    sx  = float(np.linalg.norm(m_global_actual[:2, 0]))
    sy  = float(np.linalg.norm(m_global_actual[:2, 1]))
    ang = float(np.degrees(np.arctan2(m_global_actual[1, 0], m_global_actual[0, 0])))

    caja_capturada.set_translation(tx, ty)
    caja_capturada.set_scale(sx, sy)
    caja_capturada.set_rotation(ang)

    print(f"  [Fase5] LIBERACIÓN: {caja_capturada.name}  "
          f"pos=({tx:.1f}, {ty:.1f})  s=({sx:.4f}, {sy:.4f})  rot={ang:.2f}°")


# ─────────────────────────────────────────────────────────────────── #
#  Selección por clic                                                 #
# ─────────────────────────────────────────────────────────────────── #

def pick_node(mouse_pos, nodes, renderer, radius=50):
    mx, my = mouse_pos
    best, best_dist = None, float("inf")
    for node in nodes:
        wp    = node.get_world_position()
        sx,sy = renderer.math_to_screen(wp[0], wp[1])
        d     = math.hypot(mx - sx, my - sy)
        if d < radius and d < best_dist:
            best_dist = d
            best      = node
    return best


# ─────────────────────────────────────────────────────────────────── #
#  Fondo con cuadrícula                                               #
# ─────────────────────────────────────────────────────────────────── #

def draw_background(surface, renderer):
    pygame.draw.rect(surface, BG_SIM, pygame.Rect(0, 0, WORLD_W, WINDOW_H))

    grid_c = (24, 29, 44)
    font   = pygame.font.SysFont("monospace", 9)
    lbl_c  = (45, 55, 82)

    for x in range(0, WORLD_W + 1, 100):
        sx, _ = renderer.math_to_screen(x, 0)
        pygame.draw.line(surface, grid_c, (sx, 0), (sx, WINDOW_H))
        surface.blit(font.render(str(x), True, lbl_c), (sx + 2, WINDOW_H - 16))

    for y in range(0, WORLD_H + 1, 100):
        _, sy = renderer.math_to_screen(0, y)
        pygame.draw.line(surface, grid_c, (0, sy), (WORLD_W, sy))
        surface.blit(font.render(str(y), True, lbl_c), (4, sy - 10))

    ax_c = (38, 50, 75)
    ox, oy = renderer.math_to_screen(0, 0)
    pygame.draw.line(surface, ax_c, (ox, 0),      (ox, WINDOW_H))
    pygame.draw.line(surface, ax_c, (0,  oy),     (WORLD_W, oy))


# ─────────────────────────────────────────────────────────────────── #
#  HUD de controles                                                   #
# ─────────────────────────────────────────────────────────────────── #

def draw_hud(surface, selected, idx, total, pinzas_cerradas, debug, caja_capturada):
    font   = pygame.font.SysFont("monospace", 11)
    c      = (60, 85, 130)
    c_warn = (255, 200, 60)

    estado = "CERRADAS" if pinzas_cerradas else "ABIERTAS"
    dbg    = "ON" if debug else "OFF"

    lines = [
        (f"← →  Mover brazo en X",                        c),
        (f"↑ ↓  Profundidad (escala)",                    c),
        (f"SPC  Pinzas [{estado}]",                       c),
        (f"TAB  Nodo [{idx+1}/{total}]: {selected.name if selected else '—'}", c),
        (f"D    Debug ejes [{dbg}]",                      c),
        (f"ESC  Salir",                                   c),
    ]

    if caja_capturada is not None:
        lines.append((f"★ CAPTURADA: {caja_capturada.name}", c_warn))
    else:
        lines.append((f"○ Sin caja capturada",              c))

    for i, (ln, color) in enumerate(lines):
        surface.blit(font.render(ln, True, color), (10, 10 + i * 14))


# ─────────────────────────────────────────────────────────────────── #
#  Bucle principal                                                    #
# ─────────────────────────────────────────────────────────────────── #

def main():
    pygame.init()
    pygame.display.set_caption(
        "Simulador Garra — Motor de Transformaciones Lineales [Fase 5 rev.3]")

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()

    asset_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.isdir(asset_dir):
        asset_dir = os.path.dirname(__file__)

    print(f"\nBuscando sprites en: {asset_dir}")
    sprites = load_sprites(asset_dir)

    panel_rect = pygame.Rect(WORLD_W, 0, PANEL_W, WINDOW_H)
    renderer   = Renderer(screen)
    panel      = MathPanel(screen, panel_rect)

    world, brazo, pinza_izq, pinza_der, cajas = build_scene(sprites)
    all_nodes  = [brazo, pinza_izq, pinza_der] + cajas

    selected_idx    = 0
    selected        = all_nodes[0]
    pinzas_cerradas = False
    debug_axes      = True

    caja_capturada: SceneNode | None = None

    panel.select(selected)

    brazo_tx    = BRAZO_INIT_X
    brazo_scale = BRAZO_INIT_SCALE

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_TAB:
                    selected_idx = (selected_idx + 1) % len(all_nodes)
                    selected     = all_nodes[selected_idx]
                    panel.select(selected)

                elif event.key == pygame.K_SPACE:
                    pinzas_cerradas = not pinzas_cerradas

                    if pinzas_cerradas:
                        pinza_izq.set_scale(0.5, 0.5)
                        pinza_izq.set_rotation(PINZA_CERRADA_IZQ)
                        pinza_der.set_scale(0.5, 0.5)
                        pinza_der.set_rotation(PINZA_CERRADA_DER)

                        world.update()

                        if caja_capturada is None:
                            caja_capturada = intentar_captura(
                                world, brazo, pinza_izq, pinza_der, cajas
                            )

                    else:
                        pinza_izq.set_scale(0.5, 0.5)
                        pinza_izq.set_rotation(PINZA_ABIERTA_IZQ)
                        pinza_der.set_scale(0.5, 0.5)
                        pinza_der.set_rotation(PINZA_ABIERTA_DER)

                        if caja_capturada is not None:
                            world.update()
                            liberar_caja(world, brazo, caja_capturada)
                            caja_capturada = None

                elif event.key == pygame.K_d:
                    debug_axes = not debug_axes

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event.pos[0] < WORLD_W:
                    picked = pick_node(event.pos, all_nodes, renderer)
                    if picked:
                        selected     = picked
                        selected_idx = all_nodes.index(picked)
                        panel.select(selected)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            brazo_tx = max(BRAZO_X_MIN, brazo_tx - MOVE_SPEED * dt)

        if keys[pygame.K_RIGHT]:
            brazo_tx = min(BRAZO_X_MAX, brazo_tx + MOVE_SPEED * dt)

        if keys[pygame.K_UP]:
            brazo_scale = min(BRAZO_SCALE_MAX,
                              brazo_scale + SCALE_SPEED * dt)

        if keys[pygame.K_DOWN]:
            brazo_scale = max(BRAZO_SCALE_MIN,
                              brazo_scale - SCALE_SPEED * dt)

        brazo.set_translation(brazo_tx, BRAZO_INIT_Y)
        brazo.set_scale(brazo_scale, brazo_scale)

        world.update()

        screen.fill((8, 10, 16))
        draw_background(screen, renderer)

        renderer.draw_scene(world,
                            draw_axes=debug_axes,
                            draw_labels=debug_axes)

        if selected:
            wp    = selected.get_world_position()
            sx,sy = renderer.math_to_screen(wp[0], wp[1])
            pygame.draw.circle(screen, (255, 220, 0), (sx, sy), 11, 2)

        if caja_capturada is not None:
            wp    = caja_capturada.get_world_position()
            sx,sy = renderer.math_to_screen(wp[0], wp[1])
            pygame.draw.circle(screen, (255, 100, 50), (sx, sy), 14, 2)

        draw_hud(screen, selected, selected_idx, len(all_nodes),
                 pinzas_cerradas, debug_axes, caja_capturada)

        pygame.draw.rect(screen, (28, 33, 52),
                         pygame.Rect(WORLD_W - 1, 0, 3, WINDOW_H))

        panel.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
