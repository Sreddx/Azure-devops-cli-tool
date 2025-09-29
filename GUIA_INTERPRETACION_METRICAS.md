# Guía de Interpretación de Métricas - Azure DevOps CLI Tool

## 📊 CSV Detallado por Work Item

### Columnas Principales

| Columna | Descripción | Valores Esperados |
|---------|-------------|-------------------|
| **Efficiency %** | (Estimado ÷ Activo) × 100 | >100% = eficiente, =100% = exacto, <100% = ineficiente, 0% = sin tiempo |
| **Active Time (Hours)** | Horas trabajadas (cap 1.2x estimado) | 0 a 1.2× Estimated Hours |
| **Delivery Score** | Puntualidad de entrega | 60-130 (130=muy anticipado, 100=puntual, 60=muy tarde) |
| **Days Ahead/Behind Target** | Días antes(-)/después(+) objetivo | Negativo = anticipado, Positivo = tarde |
| **Completion Bonus** | Bono por completar (20% estimado) | 0 o 20% de Estimated Hours |
| **Timing Bonus** | Bono en horas por entrega anticipada | Depende de días adelantados |

### Interpretación de Efficiency %

- **> 100%** = ✅ **Eficiente** (completó más rápido que lo estimado)
- **= 100%** = ⚖️ **En objetivo** (usó tiempo exacto)
- **< 100%** = ⚠️ **Ineficiente** (tomó más tiempo del estimado)
- **= 0%** = Sin tiempo registrado (común en checkpoints/dailys)

**Ejemplos:**
- 133% = Estimado 12h, usó 9h (muy eficiente)
- 100% = Estimado 12h, usó 12h (exacto)
- 83% = Estimado 12h, usó 14.4h (ineficiente)
- 0% = Sin tiempo activo registrado

---

## 👤 CSV Resumen por Desarrollador

### Columnas y Significado

| Columna | Descripción | Interpretación |
|---------|-------------|----------------|
| **Developer** | Nombre del desarrollador | - |
| **Total Work Items** | Total de tareas asignadas | Todas las tareas en el período |
| **Completed Items** | Tareas completadas | Estado: Closed/Done/Resolved |
| **Items With Active Time** | Tareas con tiempo activo > 0 | Solo items donde se registró tiempo de trabajo |
| **Completion Rate %** | % de completado | (Completed ÷ Total) × 100 |
| **On-Time Delivery %** | % entregado a tiempo o antes | De las tareas completadas |
| **Average Efficiency %** | Promedio de eficiencia | **Solo de items con Active Time > 0** |
| **Average Delivery Score** | Promedio de puntualidad | 60-130, refleja timing |
| **Overall Developer Score** | **Puntuación global** | **Métrica principal (0-100+)** |
| **Total Active Hours** | Suma de horas trabajadas | Con cap de 1.2x por tarea |
| **Total Estimated Hours** | Suma de horas estimadas | Total de todas las tareas |
| **Avg Days Ahead/Behind** | Promedio días anticipado/tarde | Negativo = anticipado |
| **Reopened Items/Rate** | Tareas reabiertas | Cantidad y % de reopened |
| **Early/On-Time/Late** | Desglose de entregas | Cantidad por categoría de timing |

---

## 🎯 Overall Developer Score (Métrica Principal)

### Fórmula de Cálculo

```
Overall Score = (Average Efficiency % × 40%) +
                (Average Delivery Score × 30%) +
                (Completion Rate % × 20%) +
                (On-Time Delivery % × 10%)
```

### Componentes y Pesos

| Factor | Peso | Qué Mide | Ejemplo |
|--------|------|----------|---------|
| **Average Efficiency %** | 40% | Velocidad de trabajo | 106% = 6% más rápido |
| **Average Delivery Score** | 30% | Puntualidad | 108.7 = entregas anticipadas |
| **Completion Rate %** | 20% | % tareas terminadas | 100% = todas completadas |
| **On-Time Delivery %** | 10% | % a tiempo o antes | 74% = 3 de 4 a tiempo |

### Rangos de Interpretación

| Score | Interpretación | Acción Recomendada |
|-------|----------------|-------------------|
| **≥ 80** | 🟢 Excelente | Mantener desempeño |
| **70-79** | 🟡 Bueno | Pequeñas mejoras |
| **60-69** | 🟠 Regular | Requiere atención |
| **50-59** | 🔴 Bajo | Mejora inmediata |
| **< 50** | ⚫ Crítico | Intervención necesaria |

---

## 📌 Notas Importantes

### 1. Items With Active Time

- **Muestra:** Solo tareas donde se registró tiempo activo (> 0 horas)
- **Excluye:** Checkpoints, dailys, y tareas sin registro de tiempo
- **Por qué importa:** Es la base para calcular Average Efficiency %
- **Ejemplo:** 50 tareas totales, 16 con tiempo registrado → Items With Active Time = 16

### 2. Average Efficiency % - Cálculo

- **Solo incluye** tareas con Active Time > 0
- Tareas con 0 horas (checkpoints, dailys) **NO** afectan el promedio
- Refleja eficiencia real en tareas productivas
- **Ejemplo:** 16 tareas con tiempo → promedio de esas 16 solamente

### 3. Cap de Tiempo Activo (1.2x)

- Máximo contabilizado = 1.2× tiempo estimado
- **Ejemplo:** Estimado 10h → máximo 12h
- Si trabajó 15h → se cuenta como 12h
- Protege contra registros excesivos o errores

### 4. Delivery Score vs Efficiency

| Métrica | Qué Mide | Rango |
|---------|----------|-------|
| **Efficiency %** | Velocidad (tiempo usado) | 0-150% |
| **Delivery Score** | Puntualidad (fecha entrega) | 60-130 |

Son métricas **independientes** y complementarias.

### 5. Otras Métricas (Delivery, Estimated Hours)

- **Delivery Score:** Se calcula con **todas** las tareas completadas
- **Estimated Hours:** Suma de **todas** las tareas asignadas
- **On-Time Delivery %:** De **todas** las tareas completadas
- **Solo Efficiency %** filtra por active_time > 0

---

## 🔍 Ejemplos de Lectura

### Ejemplo 1: Fernando Alcaraz (Excelente)
```
Total Work Items: 50
Completed Items: 50
Items With Active Time: 16
Average Efficiency %: 106%
Average Delivery Score: 108.7
Overall Developer Score: 95.3
```

**Análisis:**
- ✅ 100% completion rate (50/50)
- ✅ 106% efficiency → 6% más rápido que lo estimado (de 16 tareas con tiempo)
- ✅ 108.7 delivery score → Entregas anticipadas
- ✅ Score 95.3 → Excelente desempeño
- **Conclusión:** Excelente en todas las métricas. De 50 tareas, 16 tienen tiempo registrado y fueron completadas 6% más rápido del estimado

### Ejemplo 2: Damian Gaspar (Bajo Efficiency)
```
Total Work Items: 45
Completed Items: 32
Items With Active Time: 45
Average Efficiency %: 16.18%
Average Delivery Score: 76.67
Overall Developer Score: 47.03
```

**Análisis:**
- ✅ 71.11% completion (32/45)
- 🔴 16.18% efficiency → Muy bajo, tomó más tiempo del estimado
- ⚖️ 76.67 delivery score → Algunas entregas tardías
- 🔴 Score 47.03 → Bajo, requiere mejora
- **Conclusión:** Efficiency muy baja indica que está tomando mucho más tiempo del estimado en sus tareas

### Ejemplo 3: Osvaldo De Luna (Alto Efficiency)
```
Total Work Items: 72
Completed Items: 25
Items With Active Time: 72
Average Efficiency %: 4.57%
Average Delivery Score: 95.42
Overall Developer Score: 46.15
```

**Análisis:**
- ⚠️ 34.72% completion (25/72) → Bajo
- 🔴 4.57% efficiency → Muy bajo
- ✅ 95.42 delivery score → Excelente puntualidad
- ⚠️ Score 46.15 → Bajo por completion rate
- **Conclusión:** Aunque entrega a tiempo, el bajo completion rate y efficiency reducen su score

### Ejemplo 4: Cristian Soria (Balanceado)
```
Total Work Items: 40
Completed Items: 31
Items With Active Time: 40
Average Efficiency %: 39.4%
Average Delivery Score: 87.38
Overall Developer Score: 61.97
```

**Análisis:**
- ✅ 77.5% completion (31/40)
- ⚖️ 39.4% efficiency → Moderado
- ✅ 87.38 delivery score → Buena puntualidad
- ⚖️ Score 61.97 → Regular, margen de mejora
- **Conclusión:** Desempeño balanceado con oportunidades de mejora en efficiency

---

## 💡 Cómo Mejorar el Overall Developer Score

### Para Mejorar Efficiency % (40% del score)

1. ✅ Registrar tiempo activo correctamente
2. ✅ Estimar mejor las tareas (evitar sobrestimar)
3. ✅ Minimizar interrupciones durante el trabajo
4. ✅ Identificar y remover blockers rápidamente

### Para Mejorar Delivery Score (30% del score)

1. ✅ Entregar antes de la fecha objetivo cuando sea posible
2. ✅ Comunicar retrasos temprano
3. ✅ Priorizar tareas por fecha de entrega
4. ✅ Evitar acumular tareas cerca del deadline

### Para Mejorar Completion Rate (20% del score)

1. ✅ Completar tareas asignadas
2. ✅ Evitar dejar tareas abiertas
3. ✅ Solicitar reasignación si no se puede completar
4. ✅ Mantener un flujo constante de cierre de tareas

### Para Mejorar On-Time Delivery (10% del score)

1. ✅ Monitorear fechas objetivo
2. ✅ Alertar sobre posibles retrasos
3. ✅ Ajustar carga de trabajo según capacidad
4. ✅ Priorizar entregas próximas

---

## 📞 Soporte

Para dudas sobre interpretación, cálculos o configuración del sistema, contactar al equipo técnico.

**Última actualización:** Septiembre 2025