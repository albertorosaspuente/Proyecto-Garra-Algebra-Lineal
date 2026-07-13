Markdown# Simulador Garra — Motor de Transformaciones Lineales 2D

## 🎯 Descripción del Proyecto
Un simulador interactivo de una garra mecánica de premios 2D construido en Python (Pygame + NumPy). 
**Regla de Oro:** Todo el proyecto está gobernado al 100% por Álgebra Lineal (matrices de transformación homogéneas de 3x3). Las imágenes y la pantalla no dictan la lógica; únicamente renderizan el estado matemático subyacente.

## 📂 Estructura del Proyecto
```text
garra_sim/
├── math_engine.py   # Capa 1 — Motor matemático puro (matrices 3×3)
├── scene_graph.py   # Capa 2 — Scene Graph jerárquico (Nodos, padres e hijos)
├── renderer.py      # Capa 3 — Renderizador (Lee matrices, dibuja PNGs y compensa pivotes)
├── main.py          # Capa 4 — Bucle principal, máquina de estados y controles
└── math_panel.py    # Capa 5 — Panel matemático en tiempo real (Pendiente)
🚀 Instalación y EjecuciónAsegúrate de tener Python 3.x instalado y ejecuta:Bashpip install pygame numpy
python main.py
🎮 Controles de la SimulaciónTeclaAcciónFlecha Izquierda / Flecha DerechaTraslación de la garra en el Eje X (Movimiento lateral)Flecha Arriba / Flecha AbajoModifica la escala global (Efecto de profundidad en Z)Espacio / EnterCerrar/Abrir pinzas y evaluar captura de cajaESCSalir del simulador📐 Convención de CoordenadasEl simulador reconcilia de manera transparente dos sistemas de coordenadas:PlaintextEspacio Matemático (Motor)      Espacio Pygame (Renderizador)
(0,0) = Esquina inferior izq.   (0,0) = Esquina superior izq.
El eje Y crece hacia ARRIBA     El eje Y crece hacia ABAJO

Conversión (interna en la Capa 3):
  px = mx + OFFSET_X
  py = (WORLD_H - my) + OFFSET_Y
🌳 Árbol de Escena (Scene Graph)La posición de cada elemento se calcula mediante composición jerárquica (Matriz global = Matriz Padre × Matriz Local). Las coordenadas exactas y escalas han sido rigurosamente calibradas:PlaintextWorld (Mundo - Matriz Identidad)
├── Brazo (tx, ty controlados por teclado, scale para profundidad)
│   ├── PinzaIzq (tx=-61, ty=-364, rot dinámica sobre pivote)
│   └── PinzaDer (tx=59, ty=-364, rot dinámica sobre pivote)
├── Caja1 (Hija del mundo, escala base: 0.15)
├── Caja2 (Hija del mundo, capturable)
└── Caja3 (Hija del mundo, capturable)
Nota Técnica: Cuando una caja es capturada exitosamente mediante validación vectorial, cambia de padre (Re-parenting) pasando del nodo World al nodo Brazo, heredando instantáneamente todos sus movimientos.🗺️ Estado del Proyecto y Roadmap[x] Fase 1: Motor Matemático (math_engine.py) - Matrices, inversas y validaciones puras en NumPy.[x] Fase 2: Sistema de Escena (scene_graph.py) - Nodos jerárquicos y herencia matricial.[x] Fase 3: Renderizador Base (renderer.py) - Manejo de pivotes excéntricos, trigonometría y escalado.[x] Fase 4: Integración Visual y Controles (main.py) - Movimiento X/Z y cinemática de las pinzas.[ ] Fase 5: Lógica de Colisión (En progreso) - Captura de cajas validando la Distancia Euclidiana (< 50) y la equivalencia de escalas de profundidad.[ ] Fase 6: Panel Matemático UI (Capa 5) - Visualización en vivo de las matrices de transformación en un panel lateral de 480x720px.[ ] Fase 7: Demostración de Matrices Inversas - Uso explícito y verificable en el motor.🤖 Metodología de Desarrollo IAEste proyecto se codiseña utilizando una distribución estratégica entre múltiples inteligencias artificiales:Director Técnico (Gemini): Orquestación del proyecto, desarrollo del motor matemático (math_engine.py) y depuración central de alto nivel.Arquitecto Gráfico (Claude): Construcción del Scene Graph, el renderizador visual en Pygame y la máquina de estados.Especialista UI (ChatGPT): Desarrollo de utilidades, extracción de coordenadas y diseño del Panel Matemático.

```python?code_reference&code_event_index=3
with open("README_actualizado.md", "w", encoding="utf-8") as f:
    f.write("""# Simulador Garra — Motor de Transformaciones Lineales 2D

## 🎯 Descripción del Proyecto
Un simulador interactivo de una garra mecánica de premios 2D construido en Python (Pygame + NumPy). 
**Regla de Oro:** Todo el proyecto está gobernado al 100% por Álgebra Lineal (matrices de transformación homogéneas de 3x3). Las imágenes y la pantalla no dictan la lógica; únicamente renderizan el estado matemático subyacente.

## 📂 Estructura del Proyecto
garra_sim/├── math_engine.py   # Capa 1 — Motor matemático puro (matrices 3×3)├── scene_graph.py   # Capa 2 — Scene Graph jerárquico (Nodos, padres e hijos)├── renderer.py      # Capa 3 — Renderizador (Lee matrices, dibuja PNGs y compensa pivotes)├── main.py          # Capa 4 — Bucle principal, máquina de estados y controles└── math_panel.py    # Capa 5 — Panel matemático en tiempo real (Pendiente)
## 🚀 Instalación y Ejecución
Asegúrate de tener Python 3.x instalado y ejecuta:
```bash
pip install pygame numpy
python main.py
🎮 Controles de la SimulaciónTeclaAcciónFlecha Izquierda / Flecha DerechaTraslación de la garra en el Eje X (Movimiento lateral)Flecha Arriba / Flecha AbajoModifica la escala global (Efecto de profundidad en Z)Espacio / EnterCerrar/Abrir pinzas y evaluar captura de cajaESCSalir del simulador📐 Convención de CoordenadasEl simulador reconcilia de manera transparente dos sistemas de coordenadas:PlaintextEspacio Matemático (Motor)      Espacio Pygame (Renderizador)
(0,0) = Esquina inferior izq.   (0,0) = Esquina superior izq.
El eje Y crece hacia ARRIBA     El eje Y crece hacia ABAJO

Conversión (interna en la Capa 3):
  px = mx + OFFSET_X
  py = (WORLD_H - my) + OFFSET_Y
🌳 Árbol de Escena (Scene Graph)La posición de cada elemento se calcula mediante composición jerárquica (Matriz global = Matriz Padre × Matriz Local). Las coordenadas exactas y escalas han sido rigurosamente calibradas:World (Mundo - Matriz Identidad)
├── Brazo (tx, ty controlados por teclado, scale para profundidad)
│   ├── PinzaIzq (tx=-61, ty=-364, rot dinámica sobre pivote)
│   └── PinzaDer (tx=59, ty=-364, rot dinámica sobre pivote)
├── Caja1 (Hija del mundo, escala base: 0.15)
├── Caja2 (Hija del mundo, capturable)
└── Caja3 (Hija del mundo, capturable)
Nota Técnica: Cuando una caja es capturada exitosamente mediante validación vectorial, cambia de padre (Re-parenting) pasando del nodo World al nodo Brazo, heredando instantáneamente todos sus movimientos.🗺️ Estado del Proyecto y Roadmap[x] Fase 1: Motor Matemático (math_engine.py) - Matrices, inversas y validaciones puras en NumPy.[x] Fase 2: Sistema de Escena (scene_graph.py) - Nodos jerárquicos y herencia matricial.[x] Fase 3: Renderizador Base (renderer.py) - Manejo de pivotes excéntricos, trigonometría y escalado.[x] Fase 4: Integración Visual y Controles (main.py) - Movimiento X/Z y cinemática de las pinzas.[ ] Fase 5: Lógica de Colisión (En progreso) - Captura de cajas validando la Distancia Euclidiana (< 50) y la equivalencia de escalas de profundidad.[ ] Fase 6: Panel Matemático UI (Capa 5) - Visualización en vivo de las matrices de transformación en un panel lateral de 480x720px.[ ] Fase 7: Demostración de Matrices Inversas - Uso explícito y verificable en el motor.🤖 Metodología de Desarrollo IAEste proyecto se codiseña utilizando una distribución estratégica entre múltiples inteligencias artificiales:Director Técnico (Gemini): Orquestación del proyecto, desarrollo del motor matemático (math_engine.py) y depuración central de alto nivel.Arquitecto Gráfico (Claude): Construcción del Scene Graph, el renderizador visual en Pygame y la máquina de estados.Especialista UI (ChatGPT): Desarrollo de utilidades, extracción de coordenadas y diseño del Panel Matemático.""")print("Archivo regenerado")Y aquí genero nuevamente el archivo en caso de que la interfaz ahora sí te permita descargarlo:
[file-tag: code-generated-file-0-1783968876952296752]

Dime si así logras copiar el texto o si necesitas alguna modificación adicional.
