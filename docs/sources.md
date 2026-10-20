# Fuentes de datos y referencias de métodos — Reto AgroCebada 2026
Actualizado 2026-10-05 (el cuaderno 05 vuelve a escribir este archivo al ejecutarse)

## Datos proporcionados por el reto
- Polígonos de las parcelas, área, rendimiento (t/ha, ciclo abril–octubre 2025) y CONJUNTO — Reto AgroCebada FIRA 2026.
- Índices de Sentinel-2 y Landsat 2022–2025 (conjunto Básico); índices de Planet 2025 (conjunto PRO) — Reto AgroCebada FIRA 2026.
- Precipitación mensual CHIRPS: Funk, C. et al. (2015). The climate hazards infrared precipitation with stations — a new environmental record for monitoring extremes. Scientific Data 2, 150066. https://doi.org/10.1038/sdata.2015.66
- Tmín/Tmáx mensual CHIRTS-ERA5: Climate Hazards Center (2025). CHIRTS-ERA5 Data Repository. UC Santa Barbara. https://doi.org/10.15780/G2F08J
- Elevación y pendiente: INEGI (2025). Continuo de Elevaciones Mexicano 4.0 (CEM 4.0). Aguascalientes, México.

## Datos públicos añadidos por el equipo
- SoilGrids 2.0 (ISRIC), 250 m, propiedades clay, sand, silt, soc, nitrogen, bdod, phh2o, cec, cfvo; profundidades 0-5cm, 5-15cm, 15-30cm; descargado el 2026-10-05 de https://maps.isric.org/mapserv?map=/map/<propiedad>.map (promedio por polígono ponderado por área de los mosaicos de SoilGrids).
  Poggio, L. et al. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL 7, 217–240. https://doi.org/10.5194/soil-7-217-2021

## Métodos
- Suavizador de Whittaker: Eilers, P. H. C. (2003). A perfect smoother. Analytical Chemistry 75(14), 3631–3636.
- Reponderación iterativa robusta para series de tiempo: Garcia, D. (2010). Robust smoothing of gridded data in one and higher dimensions with missing values. Computational Statistics & Data Analysis 54(4), 1167–1178.
- Fenología por umbral de amplitud (TIMESAT): Jönsson, P. y Eklundh, L. (2004). TIMESAT — a program for analyzing time-series of satellite sensor data. Computers & Geosciences 30, 833–845.
- Evapotranspiración de Hargreaves–Samani y radiación extraterrestre: Allen, R. G., Pereira, L. S., Raes, D. y Smith, M. (1998). Crop evapotranspiration. FAO Irrigation and Drainage Paper 56 (ecs. 21 y 52).
- Retención de agua en el suelo: Saxton, K. E. y Rawls, W. J. (2006). Soil water characteristic estimates by texture and organic matter for hydrologic solutions. Soil Science Society of America Journal 70, 1569–1578.
- Recorte de polígonos: Sutherland, I. E. y Hodgman, G. W. (1974). Reentrant polygon clipping. Communications of the ACM 17(1), 32–42.
