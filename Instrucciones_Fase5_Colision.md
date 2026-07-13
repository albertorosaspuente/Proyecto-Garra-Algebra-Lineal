# Guía de Trabajo y Delegación: Fase 5 - Lógica de Colisión y Captura de Cajas

Este documento contiene las instrucciones técnicas precisas para que implementes exclusivamente la **Fase 5: Lógica de Colisión y Captura** del proyecto *Simulador de Garra Mecánica 2D*. 

Ya cuentas con la arquitectura base, el motor matemático (`math_engine.py`), el árbol de escena (`scene_graph.py`), el renderizador (`renderer.py`) y el bucle principal con los controles de la garra (`main.py`). Tu objetivo es lograr que la garra detecte, sujete y libere las cajas utilizando estrictamente el álgebra lineal del motor.

---

## 1. Objetivo Técnico de la Fase 5
Implementar la transición de la máquina de estados para la captura y liberación de objetos mediante:
1. **Validación geométrica pura:** Sin usar *bounding boxes* o rectángulos gráficos de Pygame. Toda la detección se basa en vectores y distancias.
2. **Re-emparentamiento dinámico (Re-parenting):** Modificar en tiempo real el nodo de la caja elegida dentro del árbol de escena, transfiriéndola del nodo "Mundo" al nodo "Brazo" y viceversa.

---

## 2. Especificación Matemática (Para resolver con tu GEMINI)

Pídele a tu **Gemini** que verifique o diseñe las funciones matemáticas necesarias en `math_engine.py` o dentro de la validación en `main.py` siguiendo este modelo exacto:

### A. Extracción de Posiciones Globales
Para evaluar la colisión, debes extraer los vectores de posición global $(x, y)$ desde la matriz de transformación global del nodo correspondiente. Dicha posición se extrae directamente de la tercera columna de la matriz homogénea 3x3:
$$M_{global} = egin{bmatrix} r_{11} & r_{12} & tx_{global} \ r_{21} & r_{22} & ty_{global} \ 0 & 0 & 1 \end{bmatrix}$$

### B. Centro de las Pinzas ($P_C$)
Sean $P_L = (x_L, y_L)$ la posición global del nodo `pinza_izquierda` y $P_R = (x_R, y_R)$ la posición global del nodo `pinza_derecha`. El centro técnico de agarre es el punto medio entre ambas:
$$x_C = rac{x_L + x_R}{2}, \quad y_C = rac{y_L + y_R}{2}$$

### C. Criterios Simultáneos de Éxito (Colisión)
Una caja solo pasa a estar capturada si al cerrarse las pinzas se cumplen dos condiciones simultáneas:
1. **Distancia Euclidiana:** La distancia entre el centro de las pinzas $P_C$ y la posición global del ancla de la caja $P_{Caja} = (x_{caja}, y_{caja})$ debe ser inferior a la tolerancia:
   $$d = \sqrt{(x_{caja} - x_C)^2 + (y_{caja} - y_C)^2} < 50.0 	ext{ unidades}$$
2. **Tolerancia de Profundidad (Equivalencia de Escalas):** Para evitar capturas fantasma entre planos distintos, la escala global en X del brazo ($S_{brazo}$) y la de la caja ($S_{caja}$) deben ser equivalentes dentro de un margen mínimo:
   $$|S_{brazo} - S_{caja}| < 0.05$$

---

## 3. Lógica de la Máquina de Estados e Interfaz (Para resolver con tu CLAUDE)

Proporciónale el archivo actual `main.py` a tu **Claude** junto con el siguiente *prompt* estructurado para codificar el bucle físico:

> **PROMPT PARA CLAUDE:**
> Actúas como el Arquitecto Gráfico del proyecto. Necesitamos actualizar la máquina de estados en `main.py` para completar la Fase 5. Modifica el flujo del ciclo principal para que actúe cuando las pinzas pasen al estado CERRADO (o se presione la tecla de acción):
> 
> 1. **Evaluación del Agarre:**
>    - Itera sobre las cajas vivas en la escena (actualmente hijas directas del nodo 'Mundo').
>    - Calcula el punto medio global entre las posiciones de ambas pinzas.
>    - Aplica la validación de Distancia Euclidiana ($< 50$) y de Escala ($|S_{brazo} - S_{caja}| < 0.05$) usando las utilidades de `math_engine.py`.
> 
> 2. **Proceso de Re-emparentamiento (Capturar):**
>    - Si una caja cumple con los requisitos, descompón su relación con el mundo: remuévela de la lista de hijos del nodo 'Mundo'.
>    - Añade dicha caja como hija directa del nodo 'Brazo'.
>    - **Cálculo de Matriz Local Relativa:** Para evitar saltos bruscos en pantalla, define su nueva matriz local con una traslación fija en `(0, offset_y)` de modo que cuelgue de forma natural justo abajo del pivote del brazo. Al ser hija del brazo, heredará automáticamente cualquier traslación en X o cambio de escala en Z (profundidad).
> 
> 3. **Proceso de Liberación (Soltar):**
>    - Al abrir de nuevo las pinzas, si hay una caja en estado capturado, efectúa el proceso inverso.
>    - Remueve la caja del nodo 'Brazo' y re-emparéntala de vuelta en el nodo 'Mundo'.
>    - Su nueva matriz local dentro del Mundo debe conservar la posición global exacta en la que se soltó (puesto que la matriz de transformación del mundo es la Identidad, su nueva matriz local será exactamente igual a su última matriz global calculada antes de soltarse).
> 
> Por favor, genérame el fragmento de código limpio y optimizado para integrarlo directamente en los condicionales de control de `main.py`.

---

## 4. Criterios de Aceptación y Éxito de la Fase
La entrega se considerará exitosa únicamente si:
- El usuario puede alinear la garra sobre una caja en el mismo plano visual (misma escala), cerrar las pinzas y ver que la caja se desplaza y escala en perfecta sincronía solidaria con el brazo.
- Al abrir las pinzas, la caja se desprende de forma fluida, quedando estática en su coordenada del plano actual.
- Queda estrictamente prohibido el uso de `pygame.Rect.colliderect` o cualquier método de colisión nativo de la biblioteca gráfica. Todo debe resolverse en el `Scene Graph`.
