"""
PROYECTO GARRA — Main  (Fase 3 final + Fase 4)
===============================================
Ventana 1280×720:
  Simulador  800×720  izquierda   (coords matemáticas Y↑)
  Panel Mat  480×720  derecha

Controles
─────────
  ←  /  →       Traslación en X del brazo
  ↑  /  ↓       Escala del brazo (profundidad Z simulada)
  ESPACIO        Abrir / Cerrar pinzas
  TAB            Cicla nodo seleccionado en el panel
  Click izq      Selecciona nodo más cercano
  D              Activa/desactiva ejes y etiquetas debug
  ESC            Salir

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

# Límites
BRAZO_X_MIN  = 60.0
BRAZO_X_MAX  = 740.0
BRAZO_SCALE_MIN = 0.25
BRAZO_SCALE_MAX = 1.20

# Estado inicial del brazo
BRAZO_INIT_X     = 400.0
BRAZO_INIT_Y     = 600.0
BRAZO_INIT_SCALE = 0.55

# Ángulos de pinzas
PINZA_ABIERTA_IZQ  =  0.0    
PINZA_CERRADA_IZQ  =  28.0   # Ahora positivo para que cierre hacia adentro
PINZA_ABIERTA_DER  =  0.0
PINZA_CERRADA_DER  = -28.0   # Ahora negativo para que cierre hacia adentro

# Colores
BG_SIM   = (12, 14, 22)


# ─────────────────────────────────────────────────────────────────── #
#  Carga de sprites                                                   #
# ─────────────────────────────────────────────────────────────────── #

def load_sprites(asset_dir: str) -> dict[str, pygame.Surface]:
    """
    Carga los PNG con canal alfa.
    Si el archivo no existe, devuelve None para ese key
    (el renderizador usará el rectángulo de debug en su lugar).
    """
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

    # ── 1. Cajas (hijas del Mundo) DIBUJADAS PRIMERO ───────────── #
    caja_cfg = [
        {"name": "Caja1", "tx": 160, "ty": 120, "rot":  6},
        {"name": "Caja2", "tx": 400, "ty": 100, "rot": -5},
        {"name": "Caja3", "tx": 630, "ty": 130, "rot": 10},
    ]
    cajas: list[SceneNode] = []
    for cfg in caja_cfg:
        c = SceneNode(name=cfg["name"], pivot=(0, 0), color=(210, 160, 50), size=(80, 80))
        # Y invertida para el PNG: 800 - 411 = 389
        c.pivot_img = (406, 389) 
        c.sprite    = sprites["caja"]
        c.set_translation(cfg["tx"], cfg["ty"])
        c.set_scale(0.15, 0.15)  # <- Escala corregida para que no sean gigantes
        c.set_rotation(cfg["rot"])
        world.add_child(c)
        cajas.append(c)

    # ── 2. Brazo y Pinzas DIBUJADOS DESPUÉS (Por encima) ───────── #
    brazo = SceneNode(name="Brazo", pivot=(0, 0), color=(70, 130, 200), size=(80, 180))
    # Y invertida: 800 - 461 = 339
    brazo.pivot_img = (414, 339) 
    brazo.sprite    = sprites["brazo"]
    brazo.set_translation(BRAZO_INIT_X, BRAZO_INIT_Y)
    brazo.set_scale(BRAZO_INIT_SCALE, BRAZO_INIT_SCALE)

    pinza_izq = SceneNode(name="PinzaIzq", pivot=(0, 0), color=(100, 180, 100), size=(50, 80))
    # Y invertida: 800 - 734 = 66
    pinza_izq.pivot_img = (622, 66)
    pinza_izq.sprite    = sprites["pinza_izq"]
    pinza_izq.set_translation(-61, -364)
    pinza_izq.set_scale(0.8, 0.8)  # <--- ESCALA AL 80% AGREGADA
    pinza_izq.set_rotation(PINZA_ABIERTA_IZQ)

    pinza_der = SceneNode(name="PinzaDer", pivot=(0, 0), color=(180, 100, 100), size=(50, 80))
    # Y invertida: 800 - 734 = 66
    pinza_der.pivot_img = (145, 66)
    pinza_der.sprite    = sprites["pinza_der"]
    pinza_der.set_translation(59, -364)
    pinza_der.set_scale(0.8, 0.8)  # <--- ESCALA AL 80% AGREGADA
    pinza_der.set_rotation(PINZA_ABIERTA_DER)

    brazo.add_child(pinza_izq)
    brazo.add_child(pinza_der)
    world.add_child(brazo)

    world.update()
    return world, brazo, pinza_izq, pinza_der, cajas


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

    # ejes del mundo
    ax_c = (38, 50, 75)
    ox, oy = renderer.math_to_screen(0, 0)
    pygame.draw.line(surface, ax_c, (ox, 0),      (ox, WINDOW_H))
    pygame.draw.line(surface, ax_c, (0,  oy),     (WORLD_W, oy))


# ─────────────────────────────────────────────────────────────────── #
#  HUD de controles                                                   #
# ─────────────────────────────────────────────────────────────────── #

def draw_hud(surface, selected, idx, total, pinzas_cerradas, debug):
    font = pygame.font.SysFont("monospace", 11)
    c    = (60, 85, 130)

    estado = "CERRADAS" if pinzas_cerradas else "ABIERTAS"
    dbg    = "ON" if debug else "OFF"

    lines = [
        f"← →  Mover brazo en X",
        f"↑ ↓  Profundidad (escala)",
        f"SPC  Pinzas [{estado}]",
        f"TAB  Nodo [{idx+1}/{total}]: {selected.name if selected else '—'}",
        f"D    Debug ejes [{dbg}]",
        f"ESC  Salir",
    ]
    for i, ln in enumerate(lines):
        surface.blit(font.render(ln, True, c), (10, 10 + i * 14))


# ─────────────────────────────────────────────────────────────────── #
#  Bucle principal                                                    #
# ─────────────────────────────────────────────────────────────────── #

def main():
    pygame.init()
    pygame.display.set_caption(
        "Simulador Garra — Motor de Transformaciones Lineales")

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()

    # Buscar assets junto al script
    asset_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.isdir(asset_dir):
        asset_dir = os.path.dirname(__file__)   # fallback: mismo directorio

    print(f"\nBuscando sprites en: {asset_dir}")
    sprites = load_sprites(asset_dir)

    panel_rect = pygame.Rect(WORLD_W, 0, PANEL_W, WINDOW_H)
    renderer   = Renderer(screen)
    panel      = MathPanel(screen, panel_rect)

    world, brazo, pinza_izq, pinza_der, cajas = build_scene(sprites)
    all_nodes  = [brazo, pinza_izq, pinza_der] + cajas

    selected_idx   = 0
    selected       = all_nodes[0]
    pinzas_cerradas = False
    debug_axes      = True

    panel.select(selected)

    # ── Estado de movimiento (Fase 4) ──────────────────────────── #
    brazo_tx    = BRAZO_INIT_X
    brazo_scale = BRAZO_INIT_SCALE

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ── Eventos ─────────────────────────────────────────────── #
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
                    # ── Máquina de estados: abrir / cerrar pinzas ── #
                    pinzas_cerradas = not pinzas_cerradas
                    if pinzas_cerradas:
                        pinza_izq.set_rotation(PINZA_CERRADA_IZQ)
                        pinza_der.set_rotation(PINZA_CERRADA_DER)
                    else:
                        pinza_izq.set_rotation(PINZA_ABIERTA_IZQ)
                        pinza_der.set_rotation(PINZA_ABIERTA_DER)

                elif event.key == pygame.K_d:
                    debug_axes = not debug_axes

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event.pos[0] < WORLD_W:
                    picked = pick_node(event.pos, all_nodes, renderer)
                    if picked:
                        selected     = picked
                        selected_idx = all_nodes.index(picked)
                        panel.select(selected)

        # ── Controles continuos (teclas mantenidas) ──────────────── #
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

        # Aplicar al brazo (las pinzas heredan automáticamente)
        brazo.set_translation(brazo_tx, BRAZO_INIT_Y)
        brazo.set_scale(brazo_scale, brazo_scale)

        # ── Actualizar matrices ───────────────────────────────────── #
        world.update()

        # ── Dibujar ──────────────────────────────────────────────── #
        screen.fill((8, 10, 16))
        draw_background(screen, renderer)

        renderer.draw_scene(world,
                            draw_axes=debug_axes,
                            draw_labels=debug_axes)

        # Resalte del nodo seleccionado
        if selected:
            wp    = selected.get_world_position()
            sx,sy = renderer.math_to_screen(wp[0], wp[1])
            pygame.draw.circle(screen, (255, 220, 0), (sx, sy), 11, 2)

        draw_hud(screen, selected, selected_idx, len(all_nodes),
                 pinzas_cerradas, debug_axes)

        # Separador visual simulador ↔ panel
        pygame.draw.rect(screen, (28, 33, 52),
                         pygame.Rect(WORLD_W - 1, 0, 3, WINDOW_H))

        panel.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()