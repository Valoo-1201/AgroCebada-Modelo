# Rendimiento de cebada con datos satelitales, clima y suelo — Reto AgroCebada FIRA 2026

**Equipo Mystical Circles**

Este repositorio contiene el código completo con el que el equipo estimó el rendimiento de cebada (t/ha) de las 59 parcelas de predicción del Reto AgroCebada FIRA 2026, junto con la incertidumbre de cada estimación. El flujo parte de los datos originales del reto, limpia las series satelitales de PlanetScope, Sentinel-2 y Landsat, extrae clima, terreno y suelo por polígono, compara diez modelos con una validación fijada de antemano y entrega intervalos de predicción calibrados y un «rendimiento financiable» (percentil 20) por parcela.

El modelo final es un **proceso gaussiano jerárquico** que combina un efecto de municipio con la correlación espacial entre parcelas vecinas (a escala de finca, ~0.3 km) e incorpora intervalos calibrados mediante predicción conforme.

## Resultados principales

Validación cruzada estratificada de 5 pliegues repetida 10 veces (50 pliegues) sobre las 138 parcelas de entrenamiento:

| Modelo | RMSE (t/ha) | MAE (t/ha) | R² |
|---|---|---|---|
| Media municipal (referencia) | 0.498 | 0.331 | 0.640 |
| **Proceso gaussiano jerárquico (final)** | **0.494** | 0.347 | **0.649** |

El RMSE y el MAE se promedian por pliegue; con todas las predicciones fuera de pliegue juntas, el RMSE del modelo final es 0.503 t/ha. Los intervalos P10–P90 cubrieron el 79.1 % de los rendimientos observados (nominal: 80 %) y el 79.5 % de las parcelas superó su rendimiento financiable P20. Ninguna variable satelital, climática o de suelo mostró señal superior al azar dentro de cada municipio (prueba de permutación con 1 000 permutaciones). El detalle está en el reporte técnico y en `qa/nb06_report.md` y `qa/nb07_report.md`, que generan los cuadernos.

Las predicciones entregadas están en [`outputs/predicciones_finales.csv`](outputs/predicciones_finales.csv).

Los cuadernos de `notebooks/` se publican ya ejecutados en Google Colab, con sus salidas y figuras. Esa ejecución reprodujo byte por byte el archivo de predicciones entregado.

## Estructura del repositorio

```
.
├── README.md
├── requirements.txt           paquetes y versiones usadas
├── notebooks/                 flujo completo, en orden de ejecución
│   ├── 01_setup_audit.ipynb
│   ├── 02_satellite_cleaning.ipynb
│   ├── 03_phenology_features.ipynb
│   ├── 04_climate_topography.ipynb
│   ├── 05_soils_master_folds.ipynb
│   ├── 06_models.ipynb
│   └── 07_final_predictions.ipynb
├── src/
│   └── agc_models.py          código compartido de modelado (lo escribe el cuaderno 06)
├── docs/
│   └── sources.md             fuentes de datos y referencias de métodos
└── outputs/
    ├── predicciones_finales.csv     las 59 parcelas de predicción (entrega)
    ├── predicciones_todas.csv       las 197 parcelas, para la aplicación web
    ├── app_bundle/                  parámetros del modelo y tablas de las preguntas guía
    └── referencia/                  copia de las predicciones entregadas, para verificar la reproducción
```

Al ejecutar los cuadernos se crean además estas carpetas, que no se incluyen en el repositorio porque se regeneran: `raw/` (datos del reto), `interim/`, `features/`, `models/`, `raw_external/` (suelo descargado de SoilGrids) y `qa/` (reportes, figuras y verificaciones de cada cuaderno).

## Datos necesarios

Los datos del reto los proporciona FIRA en la plataforma del Reto AgroCebada 2026 y no se redistribuyen aquí. Copia **todos** los archivos del reto, sin modificarlos, dentro de `raw/`. Las subcarpetas no importan: el cuaderno 01 busca cada archivo por su contenido y detecta copias duplicadas.

| Archivo o carpeta del reto | Contenido |
|---|---|
| `ID_area_rendimiento_70_30_Reto_AgroCebada.csv` | identificador, área, rendimiento y conjunto (entrenamiento o predicción) |
| `Parcelas_Reto_AGC_CONJUNTO.shp` (con `.dbf`, `.shx`, `.prj`, `.cpg`) | polígonos de las 197 parcelas |
| `Conjunto_datos_PRO_AgroCebada.csv` | índices de PlanetScope, 2025 |
| `Conjunto_datos_BASICO_AgroCebada2026.csv` | índices de Sentinel-2 y Landsat, 2022–2025 |
| `Reto_AgroCebada_CHIRPS_Precipitacion_2022_2025/` | precipitación mensual (48 GeoTIFF) |
| `Reto_AgroCebada_Temperatura_2022_2025/` | temperatura mínima y máxima mensual (96 GeoTIFF) |
| `Reto_AgroCebada_Topografia_INEGI_CEM4/` | elevación y pendiente a 120 m |

Las propiedades de suelo se descargan automáticamente de SoilGrids 2.0 (ISRIC) en el cuaderno 05, por lo que se necesita conexión a internet la primera vez. Los mosaicos quedan guardados en `raw_external/soilgrids/` y no se vuelven a descargar.

## Cómo reproducir los resultados

### En Google Colab (recomendado)

1. Copia el contenido de este repositorio en tu Google Drive, en la carpeta `MyDrive/AgroCebada/`. Los cuadernos buscan esa ruta; si usas otro nombre, cambia la variable `BASE` en la celda de configuración del inicio de cada cuaderno.
2. Copia los datos del reto en `MyDrive/AgroCebada/raw/`.
3. Abre los cuadernos en Colab **en orden, del 01 al 07**, y ejecuta cada uno completo (*Entorno de ejecución → Ejecutar todas*). Basta con CPU. Cada cuaderno monta Drive y verifica que existan las salidas del anterior; los cuadernos 01, 04 y 05 instalan los paquetes que Colab no trae (`rasterio`, `pyogrio`, `owslib`).
4. Al terminar el cuaderno 07, revisa la verificación *«Las predicciones reproducen las entregadas al reto»*: compara las predicciones nuevas con `outputs/referencia/predicciones_finales_entregadas.csv` y debe aparecer como `PASS`.

| Cuaderno | Qué hace | Tiempo aproximado |
|---|---|---|
| 01 | Audita los archivos de entrada, las parcelas y los rásteres; mide la referencia de ubicación | 3–6 min |
| 02 | Limpia nubes y valores atípicos y suaviza cada índice satelital con un filtro de Whittaker robusto | 5–10 min |
| 03 | Detecta la temporada de cada parcela y calcula variables fenológicas, por etapa, de uniformidad e historial | 2–4 min |
| 04 | Extrae clima y terreno con ponderación exacta por área del polígono, por etapa del cultivo | 2–4 min |
| 05 | Añade suelo de SoilGrids, arma la tabla maestra, fija los pliegues de validación y mide las referencias oficiales | 2–5 min |
| 06 | Entrena y compara ocho modelos con ubicación en los mismos pliegues; escribe `src/agc_models.py` | 10–15 min |
| 07 | Modelos sin ubicación, ensamble, intervalos conformes, preguntas guía y predicciones finales | 10–15 min |

Cada cuaderno escribe en `qa/` un reporte (`qa/*_report.md`) con todas sus verificaciones (PASS, WARN o FAIL) y sus figuras en `qa/figures/`. Todo FAIL debe corregirse antes de pasar al siguiente cuaderno; los WARN están explicados en el propio reporte y no bloquean.

### En una computadora local

Se necesita Python 3.11 o posterior y Jupyter, porque los cuadernos usan comandos de Jupyter (`!pip`, `%%writefile`).

```bash
pip install -r requirements.txt jupyterlab
export AGC_BASE=/ruta/a/este/repositorio      # carpeta que contiene raw/, notebooks/, src/…
jupyter lab
```

Ejecuta los cuadernos en el mismo orden. Fuera de Colab, cada cuaderno toma la carpeta base de la variable de entorno `AGC_BASE`.

## Metodología en breve

1. **Series satelitales.** Para cada sensor, por separado, se descartan imágenes con nubosidad mayor a un umbral y se suaviza cada índice en una malla diaria con un filtro de Whittaker robusto. El umbral y la rigidez se eligieron ocultando tramos de 10 días de imágenes despejadas y minimizando el error de reconstrucción (PlanetScope: ≤ 70 %, λ = 100; Sentinel-2: ≤ 10 %, λ = 100; Landsat: ≤ 30 %, λ = 10 000).
2. **Variables.** La temporada de cada parcela se detecta en su curva de NDVI de PlanetScope (método de umbral de amplitud). Con esas fechas se resumen 22 índices de Sentinel-2, EVI, LAI y MSAVI de PlanetScope y VI6T de Landsat por etapa del cultivo. El clima (CHIRPS y CHIRTS-ERA5) y el terreno (INEGI CEM 4.0) se extraen con ponderación exacta por área del polígono; el suelo viene de SoilGrids 2.0, con agua disponible estimada por Saxton y Rawls (2006). En total hay 268 variables.
3. **Validación.** Antes de modelar se fijaron 10 repeticiones de validación cruzada estratificada de 5 pliegues y una validación secundaria con bloques espaciales. Todo paso que usa el rendimiento (selección de variables, hiperparámetros, codificación de municipio) ocurre dentro de cada pliegue.
4. **Modelos.** Media municipal, ridge, bosque aleatorio y LightGBM sobre residuos municipales, proceso gaussiano espacial, kriging de regresión y un proceso gaussiano jerárquico propio, con y sin variables; además, dos modelos sin ubicación y un ensamble por mínimos cuadrados no negativos.
5. **Incertidumbre.** Intervalos calibrados por predicción conforme sobre los errores estandarizados fuera de pliegue; el percentil 20 se reporta como rendimiento financiable y define tres niveles de riesgo.

## Archivo de predicciones

`outputs/predicciones_finales.csv` tiene una fila por parcela de predicción:

| Columna | Descripción |
|---|---|
| `ID_POLIGONO` | identificador de la parcela (AGC_001…AGC_197) |
| `Municipio`, `Estado` | ubicación administrativa |
| `RENDIMIENTO_PRED_T_HA` | **rendimiento predicho (t/ha); es el valor de la entrega** |
| `P10`, `P20`, `P80`, `P90` | percentiles del intervalo calibrado (t/ha); `P20` es el rendimiento financiable |
| `riesgo` | nivel de riesgo relativo (Bajo, Medio o Alto), por terciles de la caída hacia P20 |
| `RENDIMIENTO_SATELITAL_T_HA` | lo que predice un modelo sin información de ubicación (solo satélite, clima, suelo y terreno), como referencia |
| `dist_parcela_entrenamiento_km` | distancia a la parcela de entrenamiento más cercana |

## Reproducibilidad

- Todas las semillas aleatorias están fijas (`SEED = 42`) y los pliegues de validación se guardan en `models/cv_folds.json` y `models/cv_spatial.json`.
- Las versiones de los paquetes están en `requirements.txt`; el cuaderno 01 guarda el registro completo del entorno en `qa/entorno_pip_freeze.txt`. Si Colab cambia sus versiones, puede haber diferencias numéricas mínimas; la verificación final del cuaderno 07 las mide contra las predicciones entregadas.
- Ningún cuaderno modifica los archivos de `raw/`.

## Fuentes de datos

Además de los datos del reto, el flujo usa CHIRPS (Funk et al., 2015), CHIRTS-ERA5 (Climate Hazards Center, 2025), el Continuo de Elevaciones Mexicano 4.0 (INEGI) y SoilGrids 2.0 (Poggio et al., 2021). Las referencias completas de datos y métodos están en [`docs/sources.md`](docs/sources.md).
