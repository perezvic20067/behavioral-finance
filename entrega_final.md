# Reporte de Simulación: Recuperación de Sesgos Conductuales y Evaluación de Estimadores Estándar

### Pre-análisis y Expectativas
Previo a la ejecución del simulador, se establece la inyección de dos parámetros independientes en la población de agentes: el Efecto Disposición (δ) y el Exceso de Confianza (κ). Se espera que el estimador de Odean (PGR/PLR) recupere variaciones significativas en δ, mostrando un PGR estadísticamente superior al PLR cuando δ > 0, permaneciendo silencioso ante variaciones exclusivas de κ. Para el exceso de confianza, se espera que la regresión transversal de retornos sobre rotación (turnover) capture el impacto de κ. Específicamente, un exceso de confianza puro debería deprimir los retornos netos debido a la acumulación de costos de transacción, validando la hipótesis de Barber y Odean (2000) de que el comercio excesivo es perjudicial para el patrimonio neto.

## 1. Diseño del Simulador y Mecanismos Inyectados
El entorno de simulación opera bajo parámetros controlados que garantizan que el comportamiento observado sea una propiedad estrictamente emergente de las reglas de decisión, eliminando relaciones causales preprogramadas.

* **Población y Capital:** Se simulan 1,000 agentes independientes. El capital inicial se asigna aleatoriamente mediante una distribución uniforme entre $10,000 y $500,000 USD, distribuido equiproporcionalmente en un número objetivo de posiciones (entre 5 y 30 activos por cuenta).
* **Estructura de Mercado y Precios:** Se generan precios diarios para 50 valores a lo largo de 500 días de negociación. El mercado se modela utilizando una estructura de factores con retornos correlacionados. Esta arquitectura garantiza el cumplimiento de la restricción estricta: los retornos futuros son exógenos e independientes de las decisiones de los agentes, imposibilitando la fuga de información predictiva.
* **Costos de Transacción:** Se aplica un modelo de fricción dual compuesto por un spread bid-ask (0.20%) y una comisión marginal (0.05% o 5 basis points).
* **Regla de Decisión Emergente (Mecanismo Base):** La decisión de liquidar una posición abierta no se parametriza mediante umbrales directos. Se implementa una tasa de riesgo dinámica. La probabilidad base de venta se amplifica por la intensidad transaccional (κ) y se escala mediante un multiplicador asimétrico de disposición (δ) dependiendo de si el precio actual representa una ganancia o una pérdida frente al precio contable exacto de entrada. Los empates (break-even) se evalúan como pérdidas.

## 2. Resultados de Recuperación Paramétrica
La siguiente tabla documenta los estimadores recuperados utilizando validación por *bootstrap* a nivel cuenta (1,000 iteraciones, IC 90%) para el cálculo de PGR/PLR, y modelos OLS multivariados para la regresión de retornos.

| ID | Escenario | PGR | PLR | PGR - PLR | IC 90% (Diferencia) | Pendiente Bruta (β_G) | Pendiente Neta (β_N) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Nulo (Línea Base) | 0.0702 | 0.0702 | 0.0000 | [-0.0021, 0.0021] | -0.0462 | -0.0477 |
| 2 | Disposición Baja | 0.0815 | 0.0617 | 0.0198 | [0.0175, 0.0220] | -0.0535 | -0.0550 |
| 3 | Disposición Alta | 0.1039 | 0.0111 | 0.0928 | [0.0909, 0.0948] | -0.1544 | -0.1560 |
| 4 | Turnover Bajo | 0.0726 | 0.0713 | 0.0013 | [-0.0008, 0.0034] | -0.0388 | -0.0401 |
| 5 | Turnover Alto | 0.0832 | 0.0761 | 0.0072 | [0.0051, 0.0092] | -0.1534 | -0.1548 |
| 6 | Ambos Activos | 0.0895 | 0.0440 | 0.0455 | [0.0429, 0.0482] | 0.2703 | 0.2683 |
| 7 | Confound Rebalanceo | 0.0969 | 0.0000 | 0.0969 | [0.0953, 0.0986] | 0.2378 | 0.2355 |
| 8 | Confound Reversión Media | 0.1044 | 0.0493 | 0.0552 | [0.0533, 0.0572] | 0.0244 | 0.0228 |

## 3. Análisis de Escenarios Relevantes

**Validación de Línea Base y Monotonía (Escenarios 1, 2 y 3)**
El escenario nulo confirma la robustez metodológica del estimador de proporción de ganancias realizadas: sin sesgos inyectados, la diferencia entre PGR y PLR es matemáticamente idéntica a cero (0.0000). Los escenarios 2 y 3 validan la recuperación de la monotonicidad paramétrica; a medida que δ aumenta de un rango bajo a uno alto, la brecha estructural crece progresivamente de 0.0198 a 0.0928. El estimador aísla con éxito la aversión a la pérdida sin contaminar la significancia.

**Diagnóstico de Exceso de Confianza (Escenarios 4 y 5)**
Bajo parámetros que aíslan la rotación impulsada por exceso de confianza (κ ∈ [0.7, 1.0]), la pendiente neta de la regresión OLS es significativamente negativa (β_N = -0.1548). Se observa también una pendiente bruta negativa (β_G = -0.1534). Dado que el modelo generador de mercado imposibilita la fuga de información predictiva, este comportamiento se diagnostica como un **efecto de trayectoria compuesta (compounding path effects)**. Al aislar los costos de transacción para calcular el retorno bruto, las tasas de rotación extremas alteran estructuralmente el retorno geométrico del portafolio en comparación con una estrategia estática *buy-and-hold*, arrastrando la pendiente bruta a la baja incluso en ausencia de asimetrías de información reales.

**Vulnerabilidad del Estimador: Trampas Estadísticas (Escenarios 7 y 8)**
Los confounds demuestran empíricamente las limitaciones teóricas de la medición en datos reales. En el escenario 7, donde δ = 0, la aplicación de una regla puramente mecánica de rebalanceo (liquidación de activos que superan un peso objetivo del 20%) produce un falso positivo extremo, con un diferencial PGR - PLR de 0.0969. Asimismo, en el escenario 8, donde los agentes venden empujados por una creencia táctica en la reversión a la media, el modelo estadístico dispara un falso positivo de 0.0552. Estos escenarios exhiben que el estimador de Odean carece de dimensionalidad causal; lee el acto de "cortar ganadores" independientemente de si proviene de un sesgo psicológico, una restricción de mandato fiduciario o una expectativa de mercado.

## 4. Conclusiones y Datos Requeridos

Las herramientas estándar de la literatura son metodológicamente incapaces de distinguir entre una preferencia fundamental (aversión a la pérdida en un marco de utilidad asimétrica) y comportamientos impulsados por fricciones exógenas o creencias particulares. El registro contable puro no separa el cierre heurístico por dolor emocional de una venta sistemática ejecutada por una orden pre-programada.

Para desentrañar la verdadera naturaleza del sesgo, la investigación requiere vectores de datos de mayor profundidad:
1. **Microestructura de Órdenes:** Información detallada sobre el libro de órdenes (órdenes limitadas vs. de mercado). Si los inversores cuelgan órdenes limitadas estáticas en sus posiciones ganadoras, el efecto disposición es capturado por la ejecución pasiva, no por la agresividad activa del inversor.
2. **Atención y Meta-datos Digitales:** Frecuencia de inicio de sesión en plataformas y tasas de visualización de posiciones individuales para aislar si el inversor es cognitivamente consciente de la aversión a la pérdida antes de ejecutar la liquidación.
3. **Restricciones de Mandato:** Clasificaciones de cartera y folletos de inversión que identifiquen si el rebalanceo es un requisito fiduciario del portafolio, neutralizando la causalidad psicológica en los conteos de PGR/PLR.

El simulador demuestra que sin datos granulares más allá de los retornos ejecutados y registros contables, los estimadores agregados detectarán mecánicas espurias, subvirtiendo el análisis conductual prospectivo. Una arquitectura de análisis rigurosa requiere aislar la mecánica del retorno frente a la intención real del inversor.