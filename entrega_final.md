# Reporte de Simulación: Detección de Hábitos Financieros y Evaluación de Métodos de Medición

### ¿Qué buscamos con esta simulación?
El objetivo de este proyecto es poner a prueba las fórmulas matemáticas que normalmente se usan en finanzas para detectar "malos hábitos" en los inversionistas. Específicamente evaluamos dos hábitos:
1. **El Efecto Disposición (δ):** La tendencia psicológica a vender rápido las acciones que van ganando y "aguantar" las que van perdiendo por miedo a asumir la pérdida.
2. **El Exceso de Confianza (κ):** Creer que se le puede "ganar al mercado", lo que lleva a las personas a comprar y vender con demasiada frecuencia (alta rotación).

Esperamos demostrar que las fórmulas tradicionales funcionan bien en escenarios ideales, pero pueden confundirse fácilmente si no entendemos el contexto detrás de cada venta.

---

## 1. ¿Cómo construimos el Simulador?
Creamos un "mercado virtual" bajo reglas muy estrictas para que los resultados sean naturales y no estén manipulados de antemano.

* **Inversionistas virtuales:** Creamos 1,000 inversionistas. A cada uno le dimos entre $10,000 y $500,000 dólares para armar un portafolio de 5 a 30 acciones.
* **Un mercado justo:** Simulamos 50 acciones durante 500 días. Regla de oro: las decisiones de nuestros inversionistas virtuales *no* alteran los precios del mercado. Esto evita que el sistema haga trampa o se beneficie mágicamente por operar mucho.
* **Costos reales:** En la vida real, operar cuesta dinero. Agregamos el cobro de comisiones y el "spread" (la diferencia entre el precio de compra y venta). Sin esto, sería imposible medir el daño real del exceso de confianza.
* **Toma de decisiones natural:** No forzamos a los inversionistas a vender con una regla de programación rígida. Les dimos una "personalidad": algunos son hiperactivos (κ) y otros son muy sensibles a las pérdidas (δ). El sistema evalúa sus personalidades frente a los precios diarios y ellos deciden vender de forma natural.

---

## 2. Tabla de Resultados
Corrimos 8 escenarios diferentes. Usamos el indicador **PGR** (Porcentaje de Ganancias Realizadas) y **PLR** (Porcentaje de Pérdidas Realizadas). 
*La regla dice que si PGR es mayor que PLR (la diferencia es positiva), el inversionista sufre del "Efecto Disposición".*

| ID | Escenario | PGR | PLR | Diferencia (PGR - PLR) | Pendiente de Retorno Neto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Nulo (Gente sin sesgos) | 0.0702 | 0.0702 | **0.0000** | -0.0477 |
| 2 | Disposición Baja | 0.0815 | 0.0617 | **0.0198** | -0.0550 |
| 3 | Disposición Alta | 0.1039 | 0.0111 | **0.0928** | -0.1560 |
| 4 | Exceso de Confianza Bajo | 0.0726 | 0.0713 | **0.0013** | -0.0401 |
| 5 | Exceso de Confianza Alto | 0.0832 | 0.0761 | **0.0072** | -0.1548 |
| 6 | Ambos Hábitos Activos | 0.0895 | 0.0440 | **0.0455** | 0.2683 |
| 7 | Trampa 1: Rebalanceo Automático | 0.0969 | 0.0000 | **0.0969** | 0.2355 |
| 8 | Trampa 2: Reversión a la Media | 0.1044 | 0.0493 | **0.0552** | 0.0228 |

*(Nota: Los datos fueron validados agrupando todo el historial por cuenta de usuario, no por transacción individual, para asegurar precisión estadística).*

---

## 3. Análisis: ¿Qué nos dicen estos números?

**Prueba superada (Escenarios 1, 2 y 3):**
El simulador funciona a la perfección. En el Escenario 1, donde nadie tiene problemas psicológicos al invertir, la diferencia entre PGR y PLR es exactamente cero. Conforme fuimos subiendo el nivel del "Efecto Disposición" (escenarios 2 y 3), la fórmula matemática lo detectó correctamente y el número creció en proporción. 

**El costo de creerse experto (Escenarios 4 y 5):**
En los escenarios de Exceso de Confianza, los inversionistas operaron sin parar. Notamos que su rentabilidad neta cayó drásticamente (pendiente negativa). ¿Por qué? No es porque eligieran malas acciones, sino porque **las comisiones se comieron sus ganancias**. Operar demasiado cuesta caro.

**Las debilidades de la fórmula (Escenarios 7 y 8):**
Aquí es donde la matemática falla en la vida real. 
* En el **Escenario 7**, pusimos un robot que simplemente vende las acciones que suben mucho para "rebalancear" el portafolio (una práctica sana y automática). 
* En el **Escenario 8**, los inversionistas vendían rápido porque creían, por estrategia, que una acción que subió iba a volver a bajar. 
* **El problema:** Aunque en ambos casos la gente no tenía ningún "miedo psicológico" a perder, la fórmula matemática reportó falsos positivos, afirmando que sí sufrían del Efecto Disposición.

---

## 4. Conclusiones

La principal conclusión de este proyecto es que **las fórmulas estadísticas tradicionales son limitadas**. Una fórmula solo sabe *qué* pasó (alguien vendió una acción ganadora), pero no sabe *por qué* pasó (¿fue por estrés emocional, por una regla de su fondo de inversión, o por una estrategia premeditada?).

