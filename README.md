# Simulador Garra — Motor de Transformaciones Lineales

## Estructura del proyecto

```
garra_sim/
├── math_engine.py   # Capa 1 — Motor matemático (matrices 3×3)
├── scene_graph.py   # Capa 2 — Scene Graph jerárquico
├── renderer.py      # Capa 3 — Renderizador (solo lee matrices)
├── math_panel.py    # Capa 5 — Panel matemático en tiempo real
└── main.py          # Bucle principal + mockup de escena
```

## Instalación

```bash
pip install pygame numpy
python main.py
```

## Controles (Fases 2-3, mockup)

| Tecla | Acción |
|-------|--------|
| Click izq | Seleccionar nodo más cercano |
| TAB | Ciclar entre todos los nodos |
| ESC | Salir |

## Convención de coordenadas

```
Espacio matemático           Espacio Pygame
(0,0) = esquina inf-izq      (0,0) = esquina sup-izq
Y crece hacia ARRIBA         Y crece hacia ABAJO

Conversión (en Renderer):
  px = mx + OFFSET_X
  py = (WORLD_H - my) + OFFSET_Y
```

## Árbol de escena (mockup)

```
World (identidad)
├── Brazo        → tx=120, ty=580, scale=0.55
│   ├── PinzaIzq → tx=-55, ty=-80, rot=+15°
│   └── PinzaDer → tx=+25, ty=-80, rot=-15°
├── Caja1        → tx=160, ty=100, rot=+5°
├── Caja2        → tx=400, ty=90,  rot=-8°
└── Caja3        → tx=620, ty=110, rot=+12°
```

## Próximas fases

- **Fase 4**: Controles de teclado (flechas = traslación/escala)
- **Fase 5**: Carga de sprites PNG + calibración de pivotes (modo debug)
- **Fase 6**: Máquina de estados + captura de caja (re-parenting)
- **Fase 7**: Colisión matemática (distancia euclidiana + comparación de escala)
- **Fase 8**: Uso explícito de matrices inversas en animaciones
