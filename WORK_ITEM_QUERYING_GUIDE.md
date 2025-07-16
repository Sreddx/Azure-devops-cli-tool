# Guía de Consultas de Work Items y Análisis KPI

## Descripción General

Esta herramienta permite consultar work items de Azure DevOps y calcular métricas de productividad para desarrolladores y equipos. Proporciona análisis detallados de eficiencia, tiempos de entrega y rendimiento del equipo.

## Comandos de Ejemplo Mejorados

### Para Análisis Completo (Work Items Cerrados + Activos)
```bash
python main.py --query-work-items \
  --assigned-to "Luis Nocedal,Carlos Vazquez,Diego Lopez,Alex Valenzuela,Gerardo Melgoza,Hanz Izarraraz,Osvaldo de Luna,Uriel Cortes,Emmanuel Pérez,Fernando Alcaraz,Damian Gaspar,Cristian Soria,Eduardo Félix,Daniel Cayola,Karina González,Ximena Segura" \
  --work-item-types "Task,User Story,Bug" \
  --states "Closed,Done,Active,New,In Progress" \
  --start-date "2025-06-01" \
  --end-date "2025-07-01" \
  --productive-states "Active,In Progress,Code Review,Testing" \
  --export-csv "organization_sprint_analysis_complete.csv"
```

### Solo Work Items Cerrados (Análisis Original)
```bash
python main.py --query-work-items \
  --assigned-to "Luis Nocedal,Carlos Vazquez,Diego Lopez,Alex Valenzuela" \
  --work-item-types "Task,User Story,Bug" \
  --states "Closed,Done" \
  --start-date "2025-06-01" \
  --end-date "2025-07-01" \
  --productive-states "Active,In Progress" \
  --export-csv "organization_sprint_analysis_closed.csv"
```

## Métricas y Cálculos Principales

### Métricas por Desarrollador
Basándose en el análisis de datos reales del equipo:

**1. Tasa de Finalización (Completion Rate %)**
- % de work items completados vs. asignados
- Ejemplo: Carlos Vazquez = 100% (71/71 items completados)

**2. Entrega a Tiempo (On-Time Delivery %)**
- % de items entregados antes/en la fecha objetivo
- Ejemplo: Diego Lopez = 55.81% (el mejor del equipo)

**3. Eficiencia Promedio (Average Fair Efficiency)**
- Tiempo productivo vs. tiempo total en estados activos
- Ejemplo: Diego Lopez = 62.95% (el más eficiente)

**4. Puntuación de Entrega (Average Delivery Score)**
- Calificación ponderada basada en días de adelanto/retraso
- Ejemplo: Damian Gaspar = 93.02 (mejor puntuación)

**5. Puntuación Global del Desarrollador (Overall Developer Score)**
- Combinación de eficiencia y entrega a tiempo
- Fórmula: (Efficiency × 0.4) + (Delivery Score × 0.6)
- Ejemplo: Diego Lopez = 78.25 (mejor puntuación general)

## Parámetros del Comando

### Filtros Básicos
```bash
--assigned-to "Desarrollador1,Desarrollador2"    # Lista de desarrolladores separados por coma
--work-item-types "Task,User Story,Bug"          # Tipos de work items
--states "Closed,Done"                           # Estados finales
--start-date "2025-06-01"                        # Fecha de inicio (YYYY-MM-DD)
--end-date "2025-07-01"                          # Fecha de fin (YYYY-MM-DD)
```

### Estados Productivos vs. Bloqueados
```bash
--productive-states "Active,In Progress,Code Review"  # Estados considerados productivos
--blocked-states "Blocked,Waiting,On Hold"           # Estados considerados bloqueados
```

### Exportación
```bash
--export-csv "nombre_archivo.csv"                    # Exportar resultados a CSV
```

## Explicación de Columnas del CSV

### Archivo: `*_developer_summary.csv`

**Developer**: Nombre del desarrollador asignado

**Total Work Items**: Número total de work items procesados por el desarrollador

**Completed Items**: Work items en estado "Closed", "Done" o "Resolved"

**Completion Rate %**: 
```
(Completed Items / Total Work Items) × 100
```

**On-Time Delivery %**: 
```
(Items entregados a tiempo o antes / Items completados) × 100
```

**Average Fair Efficiency**: 
```
Promedio de: (Tiempo en Estados Productivos / Tiempo Total Activo) × 100
```
- Solo considera work items con historial de cambios de estado
- Estados productivos por defecto: "Active", "In Progress", "Code Review", "Testing"

**Average Delivery Score**: Puntuación promedio basada en días de adelanto/retraso
- Entregas tempranas: +20 puntos por día
- A tiempo: 100 puntos base  
- 1-3 días tarde: -5 puntos por día
- 4-7 días tarde: -10 puntos por día
- 8-14 días tarde: -15 puntos por día
- 15+ días tarde: -25 puntos por día

**Overall Developer Score**: 
```
(Average Efficiency × 0.4) + (Average Delivery Score × 0.6)
```

**Total Active Hours**: Suma de horas en estados productivos
- Solo días laborables (lunes-viernes)
- Máximo 10 horas por día
- Basado en historial real de cambios de estado

**Total Estimated Hours**: Suma de horas estimadas por work item
```
Si hay StartDate y TargetDate:
  días = (TargetDate - StartDate)
  días_laborables = días × (5/7)
  horas = días_laborables × 8
  mínimo = 4 horas

Si no hay fechas (fallback por tipo):
  User Story = 16 horas
  Task = 8 horas  
  Bug = 4 horas
  Otros = 8 horas
```

**Avg Days Ahead/Behind**: Promedio de días de adelanto (negativo) o retraso (positivo)

**Reopened Items Handled**: Work items que fueron reabiertos y reasignados

**Reopened Rate %**: 
```
(Reopened Items / Total Work Items) × 100
```

**Work Item Types**: Número de tipos diferentes de work items manejados

**Projects Count**: Número de proyectos en los que trabajó el desarrollador

**Early Deliveries**: Items entregados antes de la fecha objetivo

**On-Time Deliveries**: Items entregados exactamente en la fecha objetivo

**Late 1-3 Days**: Items con 1-3 días de retraso

**Late 4-7 Days**: Items con 4-7 días de retraso  

**Late 8-14 Days**: Items con 8-14 días de retraso

**Late 15+ Days**: Items con 15 o más días de retraso

## Fórmulas de Cálculo Principales

### Para Completion Rate Realista
Incluir work items activos con target date:
```bash
--states "Closed,Done,Active,New,In Progress"
```
- Work items cerrados: filtrados por `ClosedDate`
- Work items activos: filtrados por `TargetDate` ≤ fecha fin

### Para Horas Activas Reales (~160h mensuales)
Expandir estados productivos:
```bash
--productive-states "Active,In Progress,Code Review,Testing,To Do,New"
```

## Análisis de Resultados del Equipo

### Top Performers (basado en datos reales):
1. **Diego Lopez**: 78.25 - Excelente balance de eficiencia (62.95%) y entrega a tiempo (55.81%)
2. **Carlos Vazquez**: 69.38 - Buena eficiencia (50.81%) con entrega moderada (36.62%)
3. **Ximena Segura**: 62.75 - Alta eficiencia (43.49%) en menor volumen

### Áreas de Mejora Identificadas:
- **Luis Nocedal**: 0% entrega a tiempo - necesita mejora en estimación/planificación
- **Emmanuel Pérez**: 0% entrega a tiempo - requiere revisión de procesos
- **Osvaldo De Luna**: Solo 8.33% entrega a tiempo con alta carga de trabajo

## Personalización y Ajustes

### Modificar Estados Productivos
Para cambiar qué estados se consideran productivos, editar en `WorkItemOperations.py:line_number`:
```python
DEFAULT_PRODUCTIVE_STATES = ['Active', 'In Progress', 'Code Review', 'Testing']
```

### Ajustar Ponderaciones de Puntuación
Para modificar la fórmula de puntuación global, ubicar en `WorkItemOperations.py:line_number`:
```python
# Cambiar pesos: actualmente 40% eficiencia, 60% entrega
overall_score = (efficiency * 0.4) + (delivery_score * 0.6)
```

### Modificar Penalizaciones de Retraso
Para ajustar puntos por días de retraso, editar:
```python
delivery_penalties = {
    'early': 20,      # +20 puntos por día temprano
    'on_time': 100,   # 100 puntos base
    'late_1_3': -5,   # -5 puntos por día (1-3 días tarde)
    'late_4_7': -10,  # -10 puntos por día (4-7 días tarde)
    'late_8_14': -15, # -15 puntos por día (8-14 días tarde)
    'late_15_plus': -25 # -25 puntos por día (15+ días tarde)
}
```

## Interpretación de Resultados

### Rangos de Puntuación Recomendados:
- **75-100**: Excelente rendimiento
- **60-74**: Buen rendimiento
- **45-59**: Rendimiento promedio
- **30-44**: Necesita mejora
- **<30**: Requiere intervención inmediata

### Indicadores Clave para Monitoreo:
1. **Entrega a Tiempo > 50%**: Objetivo mínimo del equipo
2. **Eficiencia > 40%**: Límite inferior aceptable
3. **Puntuación Global > 60**: Meta del equipo
4. **Tasa de Reapertura < 10%**: Control de calidad

## Comandos Adicionales Útiles

### Análisis por Período Específico
```bash
# Sprint actual (ejemplo 2 semanas)
python main.py --query-work-items --start-date "2025-07-01" --end-date "2025-07-15"

# Análisis mensual
python main.py --query-work-items --start-date "2025-06-01" --end-date "2025-06-30"

# Análisis trimestral
python main.py --query-work-items --start-date "2025-04-01" --end-date "2025-06-30"
```

### Filtros por Tipo de Work Item
```bash
# Solo bugs
python main.py --query-work-items --work-item-types "Bug" --states "Closed,Done"

# Solo features/historias de usuario
python main.py --query-work-items --work-item-types "User Story,Feature" --states "Closed,Done"
```

### Análisis de Desarrollador Individual
```bash
# Análisis detallado de un desarrollador
python main.py --query-work-items --assigned-to "Diego Lopez" --export-csv "diego_analysis.csv"
```