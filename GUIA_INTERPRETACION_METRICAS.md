# Guía de Interpretación de Métricas - Azure DevOps CLI Tool
## **VERSIÓN RESUMIDA CON PONDERACIONES**

---

## 🎯 **Overall Developer Score** (Métrica Principal)

### **Fórmula**
```
Score = (Avg Efficiency × 40%) + (Avg Delivery × 30%) + (Completion × 20%) + (On-Time × 10%)
```

### **Componentes**

| Métrica | Peso | Qué Mide | Rango Típico | Benchmark Sept |
|---------|------|----------|--------------|----------------|
| **Avg Efficiency %** | **40%** | Velocidad vs estimado | 0-150% | 10-96% |
| **Avg Delivery Score** | **30%** | Puntualidad de entrega | 60-130 | 70-105 |
| **Completion Rate %** | **20%** | % tareas completadas | 0-100% | 27-97% |
| **On-Time Delivery %** | **10%** | % a tiempo o antes | 0-100% | 13-79% |

### **Rangos de Desempeño** (Basado en Datos Sept 2025)

| Score | Nivel | Percentil | Acción |
|-------|-------|-----------|---------|
| **≥ 86** | 🟢 Excelente | Top 20% | Mantener |
| **65-85** | 🟡 Bueno | 20-60% | Mejorar |
| **55-64** | 🟠 Regular | 60-80% | Atención |
| **< 55** | 🔴 Bajo | Bottom 20% | Urgente |

**Datos Sept:** Fernando A. (97), Cristian S. (88), Andrés E. (86) vs Hans I. (54), Uriel C. (51), Luis N. (56)

---

## 📊 **Métricas Clave**

### **1. Efficiency % (40% del Score)**
- **>100%** = Más rápido que estimado ✅
- **=100%** = Exacto ⚖️
- **<100%** = Más lento ⚠️
- **0%** = Sin tiempo registrado
- **Importante:** Solo calcula items con Active Time > 0

**Sept 2025:** Fernando A. (96%), Cristian S. (97%), Hans I. (10%), Gerardo M. (28%)

### **2. Delivery Score (30% del Score)**
- **120-130** = Muy anticipado (+3-4 días)
- **100-119** = Puntual/anticipado
- **90-99** = Ligeramente tarde (1-3 días)
- **60-89** = Tarde (4+ días)

**Sept 2025:** Fernando A. (106), Andrés E. (98), Cristian S. (95), Osvaldo D. (94)

### **3. Completion Rate (20% del Score)**
- Promedio sept: **77%**
- Top: **97-100%** (Gerardo M., Daniel C., Fernando A.)
- Bajo: **27-43%** (Fernando H., Pablo R., Hans I.)

### **4. On-Time Delivery (10% del Score)**
- **>70%** = Excelente (Fernando A. 75%, Andrés E. 79%)
- **40-70%** = Bueno
- **<40%** = Requiere mejora

---

## 📈 **Benchmarks Sept 2025**

| Desarrollador | Score | Efficiency | Delivery | Completion | On-Time |
|---------------|-------|-----------|----------|------------|---------|
| Fernando Alcaraz | 97.3 | 96% | 106 | 85% | 75% |
| Cristian Soria | 88.4 | 97% | 95 | 85% | 40% |
| Andrés Escobedo | 86.5 | 62% | 98 | 94% | 79% |
| Alvaro Torres | 86.6 | 71% | 97 | 90% | 72% |
| Ximena Segura | 80.1 | 76% | 88 | 70% | 65% |
| --- | --- | --- | --- | --- | --- |
| Hans Izarraraz | 53.6 | 10% | 78 | 40% | 63% |
| Uriel Cortés | 51.4 | 5% | 73 | 71% | 31% |
| Luis Nocedal | 55.8 | 18% | 71 | 69% | 56% |

**Promedio General:** Score 66.5 | Efficiency 42% | Delivery 85 | Completion 77% | On-Time 47%

---

## 🔍 **Interpretación Rápida**

### **Efficiency %**
- Solo cuenta items con tiempo registrado
- Sept: 88% de items sin tiempo activo (checkpoints, dailys)
- Cap: 1.2x estimado (protege contra registros excesivos)

### **Items With Active Time**
- Fundamental para Efficiency %
- Sept: Rango 0-41 items con tiempo de 23-73 tareas totales
- Sample Confidence: 0-91% (>25% = confiable)

### **Delivery Categories** (Sept)
- **Early:** 0-24 items
- **On-Time:** 2-40 items
- **Late 1-3 días:** 0-30 items
- **Late 4-7 días:** 0-20 items
- **Late 8-14 días:** 0-14 items
- **Late 15+ días:** 0-25 items

---

## 💡 **Mejora Rápida del Score**

| Acción | Impacto | Peso |
|--------|---------|------|
| Registrar tiempo correctamente | +Efficiency | **40%** |
| Entregar anticipado | +Delivery | **30%** |
| Completar tareas asignadas | +Completion | **20%** |
| Cumplir deadlines | +On-Time | **10%** |

---

## ⚠️ **Notas Críticas**

1. **Average Efficiency:** Solo items con Active Time > 0
2. **Cap 1.2x:** Máximo 120% del tiempo estimado
3. **Delivery Score:** Todas las tareas completadas
4. **Sample Confidence:** % items con tiempo / total items

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

1. ✅ Registrar tiempo activo correctamente. Manejo de estados de tarea a tiempo y cierre de WI. 
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

Para dudas sobre interpretación, cálculos o configuración del sistema, contactar Sebastian Rojas. 

**Última actualización:** Septiembre 2025