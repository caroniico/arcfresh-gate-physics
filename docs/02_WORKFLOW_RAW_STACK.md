# Workflow Raw Stack (Shapefile + CMEMS + CCI + ISAS)

## 1. Geometria canonica del gate

- Origine canonica: shapefile gate (Sara).
- Coordinate canoniche per output NetCDF:
  - `longitude(point)`
  - `latitude(point)`
  - `x_km(point)`
  - `dx(point)`

## 2. Velocità CMEMS L4

- Sorgente: CMEMS API (DUACS L4 daily).
- Variabili: `ugos`, `vgos`, `err_ugosa`, `err_vgosa`.
- Rimappo su gate: sampling/interpolazione su punti gate.
- Nessuna formula fisica salvata nel NetCDF raw: solo stack dati.

## 3. Salinità CCI (surface)

- Sorgente CCI v5.5 nei file strait-specific.
- Aggregazione mensile: media di giorno 1 e 15 (`nanmean`).
- Errore random: media in quadratura (`sqrt(mean(err^2))`).
- Rimappo spaziale: lineare lungo distanza normalizzata (km-based), no extrapolation.
- Espansione temporale: da mensile a daily axis del gate.

## 4. Salinità ISAS (surface)

- Sorgente ISAS climatology.
- Uso solo layer superficiale: `PSAL[:, z0, :]`.
- Rimappo spaziale come CCI.
- Espansione temporale: mapping mese→giorni su asse daily.

## 5. Contratto NetCDF raw target

Variabili principali:

- `ugos`, `vgos`, `err_ugosa`, `err_vgosa`
- `depth`, `dx`
- `sss`, `sss_random_error`
- `psal_isas_surface`
- coordinate: `time`, `point`, `longitude`, `latitude`, `x_km`

Vincoli:

- niente `theta`
- niente attributi fisici/sign-convention salvati nel file
- fisica applicata solo in fase analisi (`analysis/utils.py`, notebook, app)
