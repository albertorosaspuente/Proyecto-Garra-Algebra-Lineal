"""
CAPA 2 — Scene Graph
===================
Cada SceneNode contiene:
  - Transformaciones locales (traslación, rotación, escala, shear)
  - Matriz local  : composición de las transformaciones propias
  - Matriz global : composición jerárquica con el padre
  - Pivote local  : punto de articulación expresado en coordenadas del sprite
  - Referencia al padre y lista de hijos

Regla: NADIE fuera de esta capa escribe en las matrices.
La Capa 3 solo las lee; la Capa 4 llama a los setters de transformación.
"""

import numpy as np
from math_engine import MathEngine


class SceneNode:
    """
    Nodo del grafo de escena.

    Parámetros de construcción
    --------------------------
    name       : identificador legible (solo para depuración)
    pivot      : (px, py) en coords LOCALES del sprite (espacio matemático, Y-arriba)
    color      : (R, G, B) para el rectángulo de debug mientras no haya sprite
    size       : (w, h)  ancho y alto del rectángulo de debug
    """

    def __init__(self, name: str, pivot=(0.0, 0.0),
                 color=(200, 200, 200), size=(60, 60)):
        self.name = name

        # --- jerarquía ---
        self.parent: "SceneNode | None" = None
        self.children: list["SceneNode"] = []

        # --- pivote (coords locales) ---
        self.pivot = np.array(pivot, dtype=float)

        # --- debug visual ---
        self.color = color
        self.size = size          # (ancho, alto) en unidades de mundo

        # --- transformaciones locales (parámetros) ---
        self._tx = 0.0
        self._ty = 0.0
        self._angle = 0.0        # grados
        self._sx = 1.0
        self._sy = 1.0
        self._shx = 0.0
        self._shy = 0.0

        # --- matrices (actualizadas en update) ---
        self.local_matrix  = MathEngine.get_identity()
        self.global_matrix = MathEngine.get_identity()

        # --- sprite (se asigna desde fuera cuando esté disponible) ---
        self.sprite = None          # pygame.Surface o None

        # Calculamos la matriz local inicial
        self._rebuild_local_matrix()

    # ------------------------------------------------------------------ #
    #  API de transformación (Capa 4 la usará)                            #
    # ------------------------------------------------------------------ #

    def set_translation(self, tx: float, ty: float):
        self._tx, self._ty = tx, ty
        self._rebuild_local_matrix()

    def set_rotation(self, angle_degrees: float):
        self._angle = angle_degrees
        self._rebuild_local_matrix()

    def set_scale(self, sx: float, sy: float):
        self._sx, self._sy = sx, sy
        self._rebuild_local_matrix()

    def set_shear(self, shx: float, shy: float):
        self._shx, self._shy = shx, shy
        self._rebuild_local_matrix()

    # Accesores de lectura
    @property
    def translation(self):
        return (self._tx, self._ty)

    @property
    def rotation(self):
        return self._angle

    @property
    def scale(self):
        return (self._sx, self._sy)

    # ------------------------------------------------------------------ #
    #  Jerarquía                                                          #
    # ------------------------------------------------------------------ #

    def add_child(self, child: "SceneNode"):
        """Adjunta un nodo como hijo. Actualiza su referencia al padre."""
        if child.parent is not None:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: "SceneNode"):
        """Desvincula un hijo de este nodo."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    # ------------------------------------------------------------------ #
    #  Actualización de matrices                                           #
    # ------------------------------------------------------------------ #

    def _rebuild_local_matrix(self):
        """
        Compone la matriz local en el orden canónico:
            M_local = T * R * S * Shear

        El pivote se maneja en el renderizador:
        la traslación aquí mueve el PIVOTE, no la esquina del sprite.
        """
        T     = MathEngine.get_translation_matrix(self._tx, self._ty)
        R     = MathEngine.get_rotation_matrix(self._angle)
        S     = MathEngine.get_scale_matrix(self._sx, self._sy)
        Shear = MathEngine.get_shear_matrix(self._shx, self._shy)

        self.local_matrix = MathEngine.compose_matrices(T, R, S, Shear)

    def update(self):
        """
        Recalcula la matriz global de este nodo y de todos sus descendientes.

        Regla jerárquica:
            M_global = M_global_padre · M_local
        Si no hay padre, M_global = M_local.
        """
        if self.parent is None:
            self.global_matrix = self.local_matrix.copy()
        else:
            self.global_matrix = np.dot(
                self.parent.global_matrix,
                self.local_matrix
            )

        for child in self.children:
            child.update()

    # ------------------------------------------------------------------ #
    #  Utilidades matemáticas                                             #
    # ------------------------------------------------------------------ #

    def get_world_position(self) -> np.ndarray:
        """
        Devuelve la posición del pivote en coordenadas de mundo (Y-arriba).
        Aplica la matriz global al punto homogéneo del pivote local.
        """
        local_point = np.array([self.pivot[0], self.pivot[1], 1.0])
        world_point = self.global_matrix @ local_point
        return world_point[:2]

    def get_inverse_matrix(self) -> np.ndarray:
        return MathEngine.get_inverse(self.global_matrix)

    def verify_inverse(self) -> np.ndarray:
        """Retorna M · M⁻¹ — debe ser ≈ I para verificación numérica."""
        return self.global_matrix @ self.get_inverse_matrix()

    def get_decomposed(self) -> dict:
        """
        Extrae traslación, escala y rotación aproximada de la matriz global.
        Útil para el Panel Matemático (Capa 5).
        """
        m = self.global_matrix
        tx = m[0, 2]
        ty = m[1, 2]
        sx = float(np.linalg.norm(m[:2, 0]))
        sy = float(np.linalg.norm(m[:2, 1]))
        angle_rad = float(np.arctan2(m[1, 0], m[0, 0]))
        return {
            "tx": tx, "ty": ty,
            "sx": sx, "sy": sy,
            "angle_deg": float(np.degrees(angle_rad))
        }

    def __repr__(self):
        return f"<SceneNode '{self.name}' pos=({self._tx:.1f},{self._ty:.1f}) rot={self._angle:.1f}°>"


# ------------------------------------------------------------------ #
#  Nodo raíz del mundo (sin padre, sin transformación propia)         #
# ------------------------------------------------------------------ #

class WorldNode(SceneNode):
    """
    Nodo raíz. Su matriz local es siempre identidad.
    Todos los demás nodos descienden de él.
    """
    def __init__(self):
        super().__init__(name="World", color=(0, 0, 0), size=(0, 0))

    def _rebuild_local_matrix(self):
        # El mundo no tiene transformación: siempre identidad
        self.local_matrix = MathEngine.get_identity()
