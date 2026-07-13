"""
CAPA 5 — Panel Matemático (stub para Fases 2-3)
===============================================
Muestra en tiempo real las matrices del nodo seleccionado:
  - Matriz local
  - Matriz global
  - Matriz inversa
  - Verificación M·M⁻¹ ≈ I
  - Posición del pivote (antes y después de la transformación)
  - Descomposición (tx, ty, sx, sy, ángulo)
"""

import numpy as np
import pygame
from scene_graph import SceneNode
from math_engine import MathEngine


# Colores del panel
BG_COLOR      = (18, 18, 28)
TITLE_COLOR   = (130, 200, 255)
LABEL_COLOR   = (160, 160, 200)
VALUE_COLOR   = (220, 240, 200)
MATRIX_COLOR  = (180, 255, 180)
WARN_COLOR    = (255, 180, 80)
SEP_COLOR     = (50, 55, 75)
ACCENT        = (80, 140, 255)


class MathPanel:
    """
    Panel matemático derecho (480×720 px).

    Parámetros
    ----------
    surface      : superficie de la ventana completa
    panel_rect   : pygame.Rect que define el área del panel dentro de la ventana
    """

    def __init__(self, surface: pygame.Surface, panel_rect: pygame.Rect):
        self.surface    = surface
        self.rect       = panel_rect
        self.selected: SceneNode | None = None

        pygame.font.init()
        self._font_title  = pygame.font.SysFont("monospace", 13, bold=True)
        self._font_label  = pygame.font.SysFont("monospace", 11, bold=True)
        self._font_value  = pygame.font.SysFont("monospace", 11)
        self._font_matrix = pygame.font.SysFont("monospace", 10)

    def select(self, node: SceneNode | None):
        """Establece el nodo cuyas matrices se mostrarán."""
        self.selected = node

    def draw(self):
        """Dibuja el panel completo."""
        # Fondo
        pygame.draw.rect(self.surface, BG_COLOR, self.rect)
        # Borde izquierdo (separador del simulador)
        pygame.draw.line(
            self.surface, ACCENT,
            (self.rect.left, self.rect.top),
            (self.rect.left, self.rect.bottom), 2
        )

        if self.selected is None:
            self._draw_text("Sin nodo seleccionado", self.rect.left + 20,
                            self.rect.top + 40, WARN_COLOR, self._font_label)
            return

        y = self.rect.top + 12
        x = self.rect.left + 14

        # ---- Título ----
        y = self._section_title(f"▸ {self.selected.name}", x, y)
        y += 4

        # ---- Descomposición ----
        y = self._draw_separator(x, y)
        y = self._draw_label("DESCOMPOSICIÓN GLOBAL", x, y)
        d = self.selected.get_decomposed()
        y = self._draw_kv("Traslación",  f"tx={d['tx']:+.2f}  ty={d['ty']:+.2f}", x, y)
        y = self._draw_kv("Escala",      f"sx={d['sx']:.3f}   sy={d['sy']:.3f}",  x, y)
        y = self._draw_kv("Rotación",    f"{d['angle_deg']:.2f}°",                 x, y)

        # ---- Pivote en mundo ----
        wp = self.selected.get_world_position()
        y = self._draw_kv("Pivote mundo", f"({wp[0]:.1f}, {wp[1]:.1f})", x, y)
        y += 6

        # ---- Matriz local ----
        y = self._draw_separator(x, y)
        y = self._draw_label("MATRIZ LOCAL  (3×3)", x, y)
        y = self._draw_matrix(self.selected.local_matrix, x, y, MATRIX_COLOR)
        y += 4

        # ---- Matriz global ----
        y = self._draw_separator(x, y)
        y = self._draw_label("MATRIZ GLOBAL  (3×3)", x, y)
        y = self._draw_matrix(self.selected.global_matrix, x, y, MATRIX_COLOR)
        y += 4

        # ---- Matriz inversa ----
        y = self._draw_separator(x, y)
        y = self._draw_label("MATRIZ INVERSA  (3×3)", x, y)
        inv = self.selected.get_inverse_matrix()
        y = self._draw_matrix(inv, x, y, (255, 210, 120))
        y += 4

        # ---- Verificación M·M⁻¹ ≈ I ----
        y = self._draw_separator(x, y)
        y = self._draw_label("VERIFICACIÓN  M · M⁻¹", x, y)
        product = self.selected.verify_inverse()
        error   = np.max(np.abs(product - np.eye(3)))
        color   = VALUE_COLOR if error < 1e-8 else WARN_COLOR
        y = self._draw_matrix(product, x, y, color)
        err_txt = f"error máx: {error:.2e}  {'✓ ≈ I' if error < 1e-8 else '⚠ revisar'}"
        y = self._draw_text(err_txt, x, y, color, self._font_value)
        y += 4

        # ---- Jerarquía ----
        y = self._draw_separator(x, y)
        y = self._draw_label("JERARQUÍA", x, y)
        parent_name = self.selected.parent.name if self.selected.parent else "—"
        children_names = ", ".join(c.name for c in self.selected.children) or "—"
        y = self._draw_kv("Padre",  parent_name,    x, y)
        y = self._draw_kv("Hijos",  children_names, x, y)

    # ------------------------------------------------------------------ #
    #  Helpers de dibujado                                                #
    # ------------------------------------------------------------------ #

    def _draw_text(self, text, x, y, color, font) -> int:
        surf = font.render(text, True, color)
        self.surface.blit(surf, (x, y))
        return y + surf.get_height() + 2

    def _section_title(self, text, x, y) -> int:
        surf = self._font_title.render(text, True, TITLE_COLOR)
        self.surface.blit(surf, (x, y))
        # Línea bajo el título
        pygame.draw.line(self.surface, ACCENT,
                         (x, y + surf.get_height() + 1),
                         (self.rect.right - 10, y + surf.get_height() + 1), 1)
        return y + surf.get_height() + 6

    def _draw_label(self, text, x, y) -> int:
        return self._draw_text(text, x, y, LABEL_COLOR, self._font_label)

    def _draw_kv(self, key, value, x, y) -> int:
        line = f"  {key:<14}: {value}"
        return self._draw_text(line, x, y, VALUE_COLOR, self._font_value)

    def _draw_separator(self, x, y) -> int:
        pygame.draw.line(self.surface, SEP_COLOR,
                         (x, y + 2), (self.rect.right - 10, y + 2), 1)
        return y + 7

    def _draw_matrix(self, mat: np.ndarray, x, y, color) -> int:
        """Dibuja una matriz 3×3 formateada."""
        for row in mat:
            values = "  ".join(f"{v:+7.3f}" for v in row)
            y = self._draw_text(f"  [{values}]", x, y, color, self._font_matrix)
        return y + 2
