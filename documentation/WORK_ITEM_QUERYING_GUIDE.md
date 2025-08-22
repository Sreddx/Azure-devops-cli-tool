# Guía de Consultas de Work Items y Análisis KPI

## Descripción General

Esta herramienta permite consultar work items de Azure DevOps y calcular métricas de productividad para desarrolladores y equipos. Proporciona análisis detallados de eficiencia, tiempos de entrega y rendimiento del equipo.

## Estructura del Proyecto

La herramienta ahora está organizada en:
- **`entry_points/main.py`** - Interfaz de línea de comandos principal
- **`config/azure_devops_config.json`** - Configuración centralizada
- **`run.py`** - Script de conveniencia para ejecutar la herramienta
- **`classes/`** - Clases principales de funcionalidad
- **`documentation/`** - Esta y otras guías

## Formas de Ejecución

### Opción 1: Script de Conveniencia (Recomendado)
```bash
python run.py <comando> [opciones]
```

### Opción 2: Ejecución Directa
```bash
python entry_points/main.py <comando> [opciones]
```

## Configuración: Archivo vs. Parámetros de Línea de Comandos

### Archivo de Configuración (config/azure_devops_config.json)

La herramienta incluye un archivo de configuración centralizada que define:

**Estados y Categorías:**
```json
{
  "state_categories": {
    "productive_states": ["Active", "In Progress", "Development", "Code Review", "Testing"],
    "pause_stopper_states": ["Stopper", "Blocked", "On Hold", "Waiting"],
    "completion_states": ["Resolved", "Closed", "Done"],
    "ignored_states": ["Removed", "Discarded", "Cancelled"]
  }
}
```

**Horarios de Negocio (México):**
```json
{
  "business_hours": {
    "office_start_hour": 9,
    "office_end_hour": 18,
    "max_hours_per_day": 8,
    "timezone": "America/Mexico_City",
    "working_days": [1, 2, 3, 4, 5]
  }
}
```

**Puntuación de Eficiencia:**
```json
{
  "efficiency_scoring": {
    "completion_bonus_percentage": 0.20,
    "max_efficiency_cap": 150.0,
    "early_delivery_thresholds": {
      "very_early_days": 5,
      "early_days": 3,
      "slightly_early_days": 1
    }
  }
}
```

### Usar Configuración del Archivo (Recomendado)

```bash
# Usa configuración predefinida en config/azure_devops_config.json
python run.py --query-work-items \
  --assigned-to "Luis Nocedal,Carlos Vazquez,Diego Lopez,Alejandro Valenzuela,Gerardo Melgoza,Hanz Izarraraz,Osvaldo de Luna,Uriel Cortés,Emmanuel Pérez,Fernando Alcaraz,Damian Gaspar,Cristian Soria,Daniel Cayola,Ximena Segura" \
  --start-date "2025-08-01" \
  --end-date "2025-08-21" \
  --export-csv "results.csv"
```

### Sobrescribir con Parámetros de Línea de Comandos

```bash
# Sobrescribe estados productivos de la configuración
python run.py --query-work-items \
  --assigned-to "Luis Nocedal,Carlos Vazquez" \
  --productive-states "Active,In Progress,Doing,Code Review" \
  --start-date "2025-08-01" \
  --end-date "2025-08-21" \
  --export-csv "results.csv"
```

### Usar Configuración Personalizada

```bash
# Especifica un archivo de configuración diferente
python run.py --query-work-items \
  --scoring-config "mi_config_personalizada.json" \
  --assigned-to "Luis Nocedal,Carlos Vazquez" \
  --start-date "2025-08-01" \
  --end-date "2025-08-21" \
  --export-csv "results.csv"
```

### Prioridad de Configuración

La herramienta aplica configuraciones en el siguiente orden de prioridad (mayor a menor):

1. **Parámetros de línea de comandos** - Máxima prioridad
2. **Archivo de configuración personalizado** (`--scoring-config`)
3. **Archivo de configuración por defecto** (`config/azure_devops_config.json`)
4. **Valores por defecto en el código**

**Ejemplo de Combinación:**
```bash
# La configuración se toma de:
# - Estados productivos: parámetro --productive-states (línea de comandos)
# - Horarios de negocio: config/azure_devops_config.json (archivo por defecto)
# - Timezone: America/Mexico_City (archivo por defecto)
python run.py --query-work-items \
  --assigned-to "Luis Nocedal" \
  --productive-states "Active,In Progress,Doing" \
  --start-date "2025-08-01" \
  --end-date "2025-08-21"
```

### Ventajas del Archivo de Configuración

✅ **Consistencia:** Todos los análisis usan los mismos criterios  
✅ **Facilidad:** Comandos más cortos y legibles  
✅ **Mantenimiento:** Cambios centralizados sin modificar comandos  
✅ **Documentación:** Configuración visible y versionable  
✅ **Timezone:** Configurado para México (America/Mexico_City)  

### Cuándo Usar Parámetros de Línea de Comandos

🔧 **Experimentación:** Probar diferentes estados o configuraciones  
🔧 **Casos especiales:** Análisis con criterios únicos  
🔧 **Debugging:** Aislar problemas con configuraciones específicas  
🔧 **Automatización:** Scripts con configuraciones variables  

## Comandos de Ejemplo Mejorados

### Para Análisis Completo (Work Items Cerrados + Activos)
```bash
python run.py --query-work-items \
  --assigned-to "Luis Nocedal,Carlos Vazquez,Diego Lopez,Alex Valenzuela,Gerardo Melgoza,Hanz Izarraraz,Osvaldo de Luna,Uriel Cortes,Emmanuel Pérez,Fernando Alcaraz,Damian Gaspar,Cristian Soria,Eduardo Félix,Daniel Cayola,Karina González,Ximena Segura" \
  --work-item-types "Task,User Story,Bug" \
  --states "Closed,Done,Active,New,In Progress" \
  --start-date "2025-07-01" \
  --end-date "2025-07-31" \
  --productive-states "Active,In Progress,Code Review,Testing" \
  --export-csv "organization_sprint_analysis_complete.csv"
```

```bash
python run.py --query-work-items \
  --assigned-to "Luis Nocedal,Carlos Vazquez,Diego Lopez,Alejandro Valenzuela,Gerardo Melgoza,Hanz Izarraraz,Osvaldo de Luna,Uriel Cortés,Emmanuel Pérez,Fernando Alcaraz,Damian Gaspar,Cristian Soria,Daniel Cayola,Ximena Segura" \
  --work-item-types "Task,User Story,Bug" \
  --states "Closed,Done,Active,New,In Progress,Resolved" \
  --start-date "2025-08-01" \
  --end-date "2025-08-21" \
  --productive-states "Active,In Progress,Code Review,Testing,Doing" \
  --export-csv "organization_sprint_analysis_complete.csv"
```

### Solo Work Items Cerrados (Análisis Original)
```bash
python run.py --query-work-items \
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
(Average Fair Efficiency × 0.4) + (Average Delivery Score × 0.6)
```

**Total Active Hours**: Suma de horas en estados productivos
- Solo días laborables (lunes-viernes)
- Máximo 10 horas por día
- Basado en historial real de cambios de estado

**Total Estimated Hours**: Suma de horas estimadas por work item
```
SOLO work items con Target Date:
  Si hay Start Date y Target Date:
    días = (Target Date - Start Date)
    días_laborables = días × (5/7)
    horas = días_laborables × 8
    mínimo = 4 horas

  Si solo hay Target Date (fallback por tipo):
    User Story = 16 horas
    Task = 8 horas  
    Bug = 4 horas
    Otros = 8 horas

Work items SIN Target Date = 0 horas
```

**Avg Days Ahead/Behind**: Promedio de días de adelanto (negativo) o retraso (positivo)

**Reopened Items Handled**: Work items que fueron reabiertos y reasignados

**Reopened Rate %**: 
```
(Reopened Items Handled / Total Work Items) × 100
```

**Work Item Types**: Número de tipos diferentes de work items manejados

**Projects Count**: Número de proyectos en los que trabajó el desarrollador

**Early Deliveries**: Items entregados antes de la fecha objetivo

**On-Time Deliveries**: Items entregados exactamente en la fecha objetivo

**Late 1-3 Days**: Items con 1-3 días de retraso

**Late 4-7 Days**: Items con 4-7 días de retraso  

**Late 8-14 Days**: Items con 8-14 días de retraso

**Late 15+ Days**: Items con 15 o más días de retraso

### Archivo: `*_detailed.csv`

**ID**: Work item ID único

**Title**: Título del work item

**Project Name**: Nombre del proyecto

**Assigned To**: Desarrollador asignado

**State**: Estado actual del work item

**Work Item Type**: Tipo (Task, User Story, Bug, etc.)

**Start Date**: Fecha de inicio planificada

**Target Date**: Fecha objetivo planificada

**Closed Date**: Fecha de cierre real

**Estimated Hours**: Horas estimadas (solo si tiene Target Date)

**Active Time (Hours)**: Horas en estados productivos

**Blocked Time (Hours)**: Horas en estados bloqueados

**Traditional Efficiency %**: Eficiencia tradicional

**Fair Efficiency Score**: Puntuación de eficiencia justa

**Delivery Score**: Puntuación de entrega

**Days Ahead/Behind Target**: Días de adelanto(-) o retraso(+)

**Completion Bonus**: Bonus por completar

**Timing Bonus**: Bonus por timing

**Was Reopened**: Si fue reabierto (True/False)

**Active After Reopen**: Horas activas después de reapertura

## Fórmulas de Cálculo Principales

### Para Completion Rate Realista
Incluir work items activos con target date:
```bash
--states "Closed,Done,Active,New,In Progress,Resolved"
```
- Work items cerrados: filtrados por `ClosedDate`
- Work items activos: filtrados por `TargetDate` ≤ fecha fin

### Para Horas Activas Reales (~160h mensuales)
Expandir estados productivos:
```bash
--productive-states "Active,In Progress,Code Review,Testing,To Do,New"
```

## Ejemplo Completo de Cálculo de Eficiencia

### 📋 Work Item de Ejemplo
```
ID: 12345
Tipo: "User Story"
Start Date: 2024-01-15T09:00:00Z
Target Date: 2024-01-20T17:00:00Z
Closed Date: 2024-01-18T16:00:00Z

Historial de Estados:
Rev 1: "New" - 2024-01-15T09:00:00Z
Rev 2: "Active" - 2024-01-15T10:00:00Z
Rev 3: "Blocked" - 2024-01-16T14:00:00Z
Rev 4: "Active" - 2024-01-17T09:00:00Z
Rev 5: "Closed" - 2024-01-18T16:00:00Z

Parámetros:
--productive-states "Active"
--blocked-states "Blocked"
```

### 🔢 Cálculos Paso a Paso

#### 1. **Estimated Hours**
```python
# Duración entre Start Date y Target Date
start = 2024-01-15T09:00:00Z
target = 2024-01-20T17:00:00Z
duration = 5.33 días
working_days = 5.33 × (5/7) = 3.81 días
estimated_hours = 3.81 × 8 = 30.48 horas
```

#### 2. **Active Time (Hours)** - Solo estados productivos
```python
# Rev 2→3: Active (2024-01-15T10:00:00Z → 2024-01-16T14:00:00Z)
# 1.5 días laborales × 8h/día = 12h, pero máximo 10h/día
active_time_1 = 10h (lunes) + 4h (martes) = 14 horas

# Rev 4→5: Active (2024-01-17T09:00:00Z → 2024-01-18T16:00:00Z)
# 1.29 días laborales × 8h/día = 10.32h
active_time_2 = 10h (miércoles) + 0.32h (jueves) = 10.32 horas

total_active_hours = 14 + 10.32 = 24.32 horas
```

#### 3. **Blocked Time (Hours)** - Solo estados bloqueados
```python
# Rev 3→4: Blocked (2024-01-16T14:00:00Z → 2024-01-17T09:00:00Z)
# 19 horas totales (incluye noche y madrugada)
blocked_time = 19 horas
```

#### 4. **Completion Bonus** - 20% del tiempo estimado
```python
# Work item está "Closed" = completado
completion_bonus = 30.48 × 0.20 = 6.096 horas
```

#### 5. **Delivery Timing Bonus**
```python
# Cerrado 2 días antes del target date
days_difference = -2 días (temprano)
# Bonus por entrega temprana (1-3 días): 2 × 0.5 = 1 hora
timing_bonus_hours = 1.0 horas
```

#### 6. **Fair Efficiency Score**
```python
numerator = active_hours + completion_bonus + timing_bonus
numerator = 24.32 + 6.096 + 1.0 = 31.416 horas

denominator = estimated_hours + late_penalty_mitigation
denominator = 30.48 + 0.0 = 30.48 horas

fair_efficiency = (31.416 / 30.48) × 100 = 103.07%
```

#### 7. **Traditional Efficiency** (para comparación)
```python
total_time = tiempo_entre_primera_y_ultima_transicion
total_time = 67 horas (lunes 9:00 → jueves 16:00)

traditional_efficiency = (24.32 / 67) × 100 = 36.3%
```

### 📊 Resultado Final en CSV
```json
{
  "ID": 12345,
  "Estimated Hours": 30.48,
  "Active Time (Hours)": 24.32,
  "Blocked Time (Hours)": 19.0,
  "Traditional Efficiency %": 36.3,
  "Fair Efficiency Score": 103.07,
  "Delivery Score": 120.0,
  "Days Ahead/Behind Target": -2,
  "Completion Bonus": 6.096,
  "Timing Bonus": 1.0,
  "Was Reopened": false
}
```

### 🎯 Interpretación Correcta

**Fair Efficiency Score (103.07%) NO significa** que tardaste 31 horas en 30 estimadas.

**SÍ significa** que:
- Trabajaste **24.32 horas reales** (menos que las 30.48 estimadas)
- Generaste **31.416 "puntos de valor"** por entregar temprano y completar
- Tu **"eficiencia valorada"** es 103% vs. lo estimado

**Es un sistema de recompensas** que:
- ✅ Reconoce entrega temprana
- ✅ Premia completar tareas
- ✅ Puede superar 100% legítimamente
- ❌ NO es tiempo real trabajado vs. estimado

**Comparación**:
- **Traditional Efficiency**: 36.3% = "Trabajaste 24.32h de un total de 67h"
- **Fair Efficiency Score**: 103.07% = "Generaste 103% del valor esperado"

## Personalización y Ajustes

### Opción 1: Modificar Archivo de Configuración (Recomendado)

#### Estados Productivos
Editar en `config/azure_devops_config.json`:
```json
{
  "state_categories": {
    "productive_states": ["Active", "In Progress", "Development", "Code Review", "Testing", "Doing"]
  }
}
```

#### Ponderaciones de Puntuación
Editar en `config/azure_devops_config.json`:
```json
{
  "developer_scoring": {
    "weights": {
      "fair_efficiency": 0.4,
      "delivery_score": 0.3,
      "completion_rate": 0.2,
      "on_time_delivery": 0.1
    }
  }
}
```

#### Penalizaciones de Retraso
Editar en `config/azure_devops_config.json`:
```json
{
  "efficiency_scoring": {
    "early_delivery_scores": {
      "very_early": 130.0,
      "early": 120.0,
      "slightly_early": 110.0,
      "on_time": 100.0
    },
    "late_delivery_scores": {
      "late_1_3": 90.0,
      "late_4_7": 80.0,
      "late_8_14": 70.0,
      "late_15_plus": 60.0
    }
  }
}
```

#### Horarios de Negocio y Timezone
Editar en `config/azure_devops_config.json`:
```json
{
  "business_hours": {
    "office_start_hour": 9,
    "office_end_hour": 18,
    "max_hours_per_day": 8,
    "timezone": "America/Mexico_City"
  }
}
```

### Opción 2: Modificar Código Fuente

#### Estados Productivos
Para cambiar qué estados se consideran productivos, editar en `classes/WorkItemOperations.py`:
```python
DEFAULT_PRODUCTIVE_STATES = ['Active', 'In Progress', 'Code Review', 'Testing']
```

#### Ajustar Ponderaciones de Puntuación
Para modificar la fórmula de puntuación global, ubicar en `classes/efficiency_calculator.py`:
```python
# Cambiar pesos en developer_score_weights
'developer_score_weights': {
    'fair_efficiency': 0.4,    # 40%
    'delivery_score': 0.3,     # 30%
    'completion_rate': 0.2,    # 20%
    'on_time_delivery': 0.1    # 10%
}
```

## Interpretación de Resultados

### Rangos de Overall Developer Score:
- **80-100**: Excelente rendimiento
- **65-79**: Buen rendimiento
- **60-64**: Rendimiento aceptable (umbral mínimo)
- **45-59**: Necesita mejora
- **<45**: Requiere intervención inmediata

### Indicadores Clave para Monitoreo:
1. **On-Time Delivery % > 50%**: Objetivo mínimo del equipo
2. **Average Fair Efficiency > 40%**: Límite inferior aceptable
3. **Overall Developer Score > 60**: Meta mínima del equipo
4. **Reopened Rate % < 10%**: Control de calidad