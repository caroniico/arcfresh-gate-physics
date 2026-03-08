# 📦 Dataset Reference — ARCFRESH Export Pipeline

> ⚠️ **AGENTI: LEGGI QUESTO FILE PRIMA DI TOCCARE QUALSIASI DATO.**
> Contiene la provenienza esatta di ogni dato usato nell'export, le costanti fisiche,
> la struttura dei file CCI SSS, i bug noti e quelli fixati. Non chiedere — leggi qui.
>
> Ultimo aggiornamento: **2026-02-25** (export pipeline v2 — nanmean fix applicato, tutti i 6 gate esportati)

---

## 🗺️ Provenienza di ogni dato nell'export (`scripts/export_all_gates.py`)

| Dato | Sorgente | Dove si trova | Formato |
|------|----------|--------------|---------|
| **Gate geometry** | Shapefiles nel repo | `gates/*.shp` | Vettoriale (linea) |
| **Velocità u, v** | CMEMS L4 `SEALEVEL_GLO_PHY_L4_MY_008_047` | API Copernicus → cache `data/cache/intelligent/cache_l1_raw.pkl` | xarray lazy |
| **Salinità SSS** | ESA CCI SSS v5.5 (file locali) | `/Users/nicolocaron/Desktop/ARCFRESH/straits/netcdf/` | NetCDF |
| **Batimetria** | GEBCO 2025 (file locale) | `/Users/nicolocaron/Desktop/ARCFRESH/GEBCO_*/gebco_2025_*.nc` | NetCDF → cache `data/cache/bathymetry/` |
| **Costanti fisiche** | Hardcoded nello script | `scripts/export_all_gates.py` linee 53-58 | Python |
| **FW transport** | Calcolato (non scaricato) | Prodotto da `export_gate()` | numpy array |
| **Salt flux** | Calcolato (non scaricato) | Prodotto da `export_gate()` | numpy array |

---

## 1. Velocità — CMEMS L4 (v_perp)

| Campo | Valore |
|-------|--------|
| **Source** | Copernicus Marine Service |
| **Product** | `SEALEVEL_GLO_PHY_L4_MY_008_047` |
| **Dataset ID** | `cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D` |
| **Variabili usate** | `ugos` (u geostrofica), `vgos` (v geostrofica) |
| **Risoluzione** | 0.125° (~14 km) **giornaliera** |
| **Copertura temporale** | 2010-01-01 → 2023-12-31 (5113 giorni) |
| **Come si usa** | Shapefile gate → adaptive sampling `n_points` lungo transetta → `v_perp` = proiezione sulla normale al gate |
| **Cache** | `data/cache/intelligent/cache_l1_raw.pkl` (lazy xarray, ~902KB indice) |
| **Codice** | `src/services/cmems_l4_service.py` → `load_gate_data()` |

### 1a. n_points per gate (adaptive sampling)

| Gate | n_points | Lunghezza gate |
|------|----------|---------------|
| Fram Strait | 277 | 732 km |
| Denmark Strait | 95 | 534 km |
| Davis Strait | — | — |
| Bering Strait | — | — |
| Barents Opening | — | — |
| Norwegian Boundary | 173 | 1050 km |

---

---

## 2. Salinità superficiale — ESA CCI SSS v5.5

| Campo | Valore |
|-------|--------|
| **Source** | ESA Ocean Colour CCI / CATDS |
| **Dataset** | ESA CCI SSS v5.5 |
| **Tipo** | Along-track (profili satellite, NON griglia regolare) |
| **Variabili** | `sss` (salinità [PSU]), `sss_random_error`, `date`, `longitude`, `latitude` |
| **Frequenza temporale** | **2 timestamp per mese**: giorno 1 e giorno 15 di ogni mese |
| **Struttura time** | `time` = indice 0,1,2... (senza unità!); `date` = "days since 2010-01-15" → **USA `date`** |
| **Copertura temporale** | 2010-01-15 → 2023-12-15 → **335 timestamp** (167 mesi × 2, eccetto 2010-01 che ha solo il 15) |
| **Profili spaziali** | Bering: 11 profili; Davis: 45 profili; Fram: 120 profili |
| **NaN** | Dove c'è ghiaccio marino → SSS = NaN (non si estrapolano!) |
| **File path** | `/Users/nicolocaron/Desktop/ARCFRESH/straits/netcdf/` |

### 2a. File per gate

| Gate | File NetCDF | n_prof | % valid | Mesi all-NaN |
|------|-------------|--------|---------|--------------|
| Bering | `bering_strait_TPJ_pass_076_SSS_CCIv5.5.nc` | 11 | 14.5% | 125/335 |
| Davis | `davis_strait_SSS_CCIv5.5.nc` | 45 | 45.2% | 77/335 |
| Fram | `fram_strait_S3_pass_481_SSS_CCIv5.5.nc` | 120 | 33.8% | 0/335 (ma ~66% dei punti NaN in inverno per ghiaccio) |
| Barents | `barents_sea_opening_S3_pass_481_SSS_CCIv5.5.nc` | — | — | — |
| Denmark | `denmark_strait_TPJ_pass_246_SSS_CCIv5.5.nc` | — | — | — |
| Norwegian | `norwegian_sea_boundary_TPJ_pass_220_SSS_CCIv5.5.nc` | 87 | 89.8% | — |
| Nares | `nares_strait_SSS_CCIv5.5.nc` | — | **0.0%** | 335/335 → **GATE SKIPPATO** |

### 2b. Come si leggono le date (IMPORTANTE)

```python
import netCDF4 as nc
import pandas as pd

ds = nc.Dataset("...SSS_CCIv5.5.nc")
# NON usare ds['time'] — non ha unità, è solo un indice 0,1,2...
# USARE ds['date'] = "days since 2010-01-15"
origin = pd.Timestamp("2010-01-15")
date_vals = ds.variables['date'][:]
real_dates = [origin + pd.Timedelta(days=int(d)) for d in date_vals]
```

Oppure con xarray (funziona perché 'date' ha attributo units):
```python
import xarray as xr
ds = xr.open_dataset("...SSS_CCIv5.5.nc")
dates = pd.to_datetime(ds['date'].values)  # ← usa 'date', NON 'time'
```

### 2c. Come si gestiscono i 2 timestamp mensili ✅ FIXATO 2026-02-25

Ogni mese ha **2 osservazioni**: giorno 1 e giorno 15.

**Comportamento CORRETTO (attuale)** in `interpolate_sss_cci()` (`scripts/export_all_gates.py`):

```python
# Colleziona tutti gli indici per (year, month) — può essere 1 o 2
cci_lookup = {}
for idx, t in enumerate(cci_time):
    key = (t.year, t.month)
    if key not in cci_lookup:
        cci_lookup[key] = []
    cci_lookup[key].append(idx)

# Per ogni mese di velocità: media nanmean dei profili disponibili (giorno 1 + giorno 15)
cci_indices = cci_lookup.get((yr, mo))
month_profiles = cci_sss[cci_indices, :]   # (1 o 2, n_prof)
sss_profile = np.nanmean(month_profiles, axis=0)  # (n_prof,) — media reale
```

> ⚠️ **Bug vecchio (PRE 2026-02-25)**: il dict veniva costruito con `cci_lookup[(yr,mo)] = idx`
> (sovrascrivendo), quindi si usava sempre il giorno 15 e si perdeva il giorno 1. **Ora fixato.**

### 2d. Relazione gate shapefile ↔ CCI SSS

**Stessa transetta fisica**, diversa risoluzione spaziale:

| Gate | Shapefile (velocità) | CCI SSS n_prof | Lon range |
|------|---------------------|----------------|-----------|
| Bering | `bering_strait_TPJ_pass_076.shp` (29 vertici) | 11 profili | -169.75 → -167.01° |
| Davis | `davis_strait.shp` (106 vertici) | 45 profili | -64.40 → -52.98° |
| Fram | `fram_strait_S3_pass_481.shp` (150 vertici) | 120 profili | -14.36 → +14.89° |

`interp1d` in `interpolate_sss_cci()` serve **solo per re-gridding spaziale** (da n_prof CCI a n_points velocità),
**non per estrapolazione**. `fill_value=np.nan` → nessun valore inventato fuori dal range dei profili validi.

### 2e. Come si gestiscono i NaN SSS nel calcolo FW

```python
valid = ~np.isnan(s) & ~np.isnan(v)
if np.sum(valid) >= 2:
    fw[t] = np.nansum(v[valid] * (1.0 - s[valid] / S_REF) * H_profile[valid] * dx[valid])
# else: fw[t] rimane NaN — NON viene messo a 0
```

| Situazione | Risultato FW |
|---|---|
| SSS valida ovunque | FW normale (integrale completo) |
| SSS NaN parziale (ghiaccio su un lato) | FW calcolato solo sui punti validi (integrale parziale — possibile sottostima) |
| SSS NaN ovunque (mese invernale Bering) | FW = `NaN` — dati mancanti, non zero |

> ⚠️ **Il vecchio codice metteva FW=0 quando SSS era NaN. Era SBAGLIATO. Ora è NaN.**

---

## 3. Batimetria — GEBCO 2025

| Campo | Valore |
|-------|--------|
| **Source** | GEBCO (General Bathymetric Chart of the Oceans) 2025 |
| **File locale** | `/Users/nicolocaron/Desktop/ARCFRESH/GEBCO_06_Feb_2026_c91df93f54b8/gebco_2025_n90.0_s55.0_w0.0_e360.0.nc` |
| **Variabile** | `elevation` [m, negativo = profondità] |
| **Risoluzione** | ~460 m |
| **Cache** | `data/cache/bathymetry/{gate}_bathymetry.pkl` — **non ricalcolare mai** |
| **depth_cap** | 250 m — la batimetria viene cappata: `H = min(depth, 250)` |
| **Codice** | `src/services/gebco_service.py` → `GEBCOBathymetryCache` |

---

## 4. Costanti fisiche (hardcoded in `scripts/export_all_gates.py`)

| Costante | Valore | Linea script | Note |
|----------|--------|-------------|------|
| **ρ** | 1025.0 kg/m³ | 58 | Costante ovunque — NO densità variabile |
| **S_ref** | 34.8 PSU | 57 | Salinità di riferimento per FW transport |
| **depth_cap** | 250 m | 56 | Profondità massima integrazione |
| **TIME_START** | 2010-01-01 | 53 | Inizio serie temporale |
| **TIME_END** | 2023-12-31 | 54 | Fine serie temporale → 5113 giorni |

### Formule di calcolo

```
# Freshwater transport [m³/s → convertito in mSv diviso 1e3]
FW[t] = Σ_i  v_perp[i,t] × (1 - S[i,t] / S_ref) × H[i] × Δx[i]

# Salt flux [kg/s → convertito in Gg/s diviso 1e9]
SF[t] = Σ_i  ρ × (S[i,t] / 1000) × v_perp[i,t] × H[i] × Δx[i]
```

Solo dove sia `v_perp` che `SSS` sono **non-NaN**. Nessun valore inventato.

---

## 5. Gate shapefiles

Posizione: `gates/` nella root del progetto.
CRS originale: EPSG:3413 (Polar Stereographic) → convertiti in EPSG:4326 per i calcoli.

| Gate ID | File shapefile | n_vertici | CCI SSS disponibile |
|---------|---------------|-----------|---------------------|
| `fram_strait` | `fram_strait_S3_pass_481.shp` | 150 | ✅ |
| `denmark_strait` | `denmark_strait_TPJ_pass_246.shp` | — | ✅ |
| `davis_strait` | `davis_strait.shp` | 106 | ✅ |
| `bering_strait` | `bering_strait_TPJ_pass_076.shp` | 29 | ✅ |
| `barents_opening` | `barents_sea_opening_S3_pass_481.shp` | — | ✅ |
| `norwegian_boundary` | `norwegian_sea_boundary_TPJ_pass_220.shp` | — | ✅ |
| `nares_strait` | `nares_strait.shp` | — | ❌ (0% valid — skippato) |

---

## 6. Export output (ultimo run: 2026-02-25 20:38-20:46)

ZIP generati da `scripts/export_all_gates.py` → root del progetto:

| File ZIP | SSS mean | FW mean | Salt Flux mean | Valid days |
|----------|----------|---------|---------------|------------|
| `arcfresh_fram_strait_2010-2023_20260225.zip` | 34.61 PSU | -9.46 mSv | 0.090 Gg/s | 5113/5113 |
| `arcfresh_denmark_strait_2010-2023_20260225.zip` | — | — | — | — |
| `arcfresh_davis_strait_2010-2023_20260225.zip` | — | — | — | — |
| `arcfresh_bering_strait_2010-2023_20260225.zip` | — | — | — | — |
| `arcfresh_barents_opening_2010-2023_20260225.zip` | — | — | — | — |
| `arcfresh_norwegian_boundary_2010-2023_20260225.zip` | 34.78 PSU | -0.61 mSv | 0.122 Gg/s | 5113/5113 |

Ogni ZIP contiene: **4 CSV + 9 PNG + README.txt** (~5 MB).

---

## 7. Changelog / Bug fix

| Data | Fix | Dettaglio |
|------|-----|-----------|
| 2026-02-25 | ✅ `nanmean` dei 2 timestamp mensili CCI | `cci_lookup` ora raccoglie lista di indici per (yr,mo) e fa `nanmean` prima dell'interpolazione — non si perde più il giorno 1 |
| 2026-02-25 | ✅ FW=NaN (non 0) quando SSS mancante | Il vecchio codice metteva `fw=0` quando tutti i punti SSS erano NaN — ora rimane NaN |
| 2026-02-25 | ✅ Rimosso tutto il codice ISAS (fallback) | Nessun fallback, nessuna estrapolazione, nessun fill_value='extrapolate' |
| 2026-02-25 | ✅ ρ=1025 costante | Rimossa la variabile `dos` (density) — ρ costante ovunque |
