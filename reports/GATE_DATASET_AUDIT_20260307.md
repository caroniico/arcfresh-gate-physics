# Gate Dataset Audit — 2026-03-07

## Scope
- Project root: `/Users/nicolocaron/Documents/GitHub/ARCFRESH-DTU-NICO-and-AMALIE`
- Salinity sources: `/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/straits/netcdf`
- Index-map files: `/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/straits/*.nc`
- Time target for rebuilt gate DB: `2002-01-01` to `2023-12-31` (daily)

## Executive Summary
- The old gate NetCDF builder stored `theta` and sign/orientation metadata. This has now been removed in the new raw-stack contract.
- CCI SSS v5.5 is semi-monthly in source files (day 1 and day 15), with January 2010 starting on day 15 only.
- ISAS PSAL files are 3D monthly climatology; for the new DB only `PSAL[:, z0, :]` (surface layer, depth≈1 m) is used.
- `straits/*.nc` files are not physical fields; they are index maps (`index_lon_*`, `index_lat_*`) for CCI/ISAS profile grids.
- Legacy interpolation is mostly acceptable for raw stack creation (nearest-neighbor CMEMS + linear along-gate salinity remap), with clear room for future bilinear CMEMS upgrades.

## Dataset-by-Dataset Technical Inventory

### 1) CMEMS L4 (API)
- Product: `SEALEVEL_GLO_PHY_L4_MY_008_047`
- Dataset ID: `cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D`
- Variables used in gate DB:
  - `ugos` [m/s], `vgos` [m/s]
  - `err_ugosa` [m/s], `err_vgosa` [m/s]
- Native grid: `0.125°` (daily)
- Gate extraction method (legacy and kept for raw stack): nearest-neighbor on gridded product via KDTree.
- Time in gate DB: daily `2002-01-01` → `2023-12-31`.

### 2) CCI SSS v5.5 (surface salinity)
- Files: `*_SSS_CCIv5.5.nc` (7 gates)
- Dims: `time=335`, `nb_prof` gate-specific
- Variables:
  - `sss` [PSU]
  - `sss_random_error` [PSU]
  - `date`, `longitude`, `latitude`
- Temporal representation:
  - `date` contains real times
  - Day distribution: day 1 = 167, day 15 = 168
  - Range: `2010-01-15` → `2023-12-15`
- New contract mapping:
  - Monthly profile = `nanmean(day1, day15)` by `(year, month)`
  - Monthly random error = `sqrt(mean(err^2))` by `(year, month)`
  - Expanded to daily CMEMS timeline.

#### CCI per-gate coverage/range
| Gate file | n_prof | Valid % (`sss`) | `sss` range PSU | `sss_random_error` range PSU |
|---|---:|---:|---:|---:|
| `barents_sea_opening_S3_pass_481_SSS_CCIv5.5.nc` | 76 | 89.1 | 27.898–40.361 | 0.0746–0.9334 |
| `bering_strait_TPJ_pass_076_SSS_CCIv5.5.nc` | 11 | 14.5 | 29.603–34.658 | 0.3132–0.9105 |
| `davis_strait_SSS_CCIv5.5.nc` | 45 | 45.2 | 21.127–37.038 | 0.1491–1.5669 |
| `denmark_strait_TPJ_pass_246_SSS_CCIv5.5.nc` | 47 | 72.4 | 28.475–38.206 | 0.1286–1.2884 |
| `fram_strait_S3_pass_481_SSS_CCIv5.5.nc` | 120 | 33.8 | 30.293–40.242 | 0.1125–1.3664 |
| `nares_strait_SSS_CCIv5.5.nc` | 28 | 0.0 | NaN | NaN |
| `norwegian_sea_boundary_TPJ_pass_220_SSS_CCIv5.5.nc` | 87 | 89.8 | 31.456–36.135 | 0.0666–0.8992 |

### 3) ISAS PSAL climatology (surface only used)
- Files: `*_CLIM_ISAS_PSAL.nc` (7 gates)
- Dims: `time=12`, `z=187`, `nb_prof` gate-specific
- Variables:
  - `PSAL(time,z,nb_prof)` [PSU]
  - `depth(z)` [m], `date`, `longitude`, `latitude`
- Depth grid: `1 m` → `5500 m` (187 levels)
- New contract mapping:
  - Use only first depth layer (`z0`, depth≈1 m)
  - Spatial remap to canonical gate
  - Monthly climatology by month number (1..12)
  - Expanded to daily CMEMS timeline by day month.

#### ISAS PSAL per-gate surface stats (`PSAL[:, z0, :]`)
| Gate file | n_prof | Valid % surface | Surface range PSU | Surface mean PSU |
|---|---:|---:|---:|---:|
| `barents_sea_opening_S3_pass_481_CLIM_ISAS_PSAL.nc` | 56 | 100.0 | 33.354–34.957 | 34.563 |
| `bering_strait_TPJ_pass_076_CLIM_ISAS_PSAL.nc` | 6 | 100.0 | 29.910–32.294 | 31.246 |
| `davis_strait_CLIM_ISAS_PSAL.nc` | 24 | 100.0 | 29.809–33.382 | 32.297 |
| `denmark_strait_TPJ_pass_246_CLIM_ISAS_PSAL.nc` | 25 | 100.0 | 31.509–34.891 | 33.949 |
| `fram_strait_S3_pass_481_CLIM_ISAS_PSAL.nc` | 70 | 98.6 | 30.549–34.778 | 33.515 |
| `nares_strait_CLIM_ISAS_PSAL.nc` | 18 | 100.0 | 29.560–31.057 | 30.360 |
| `norwegian_sea_boundary_TPJ_pass_220_CLIM_ISAS_PSAL.nc` | 52 | 98.1 | 32.121–35.117 | 34.671 |

### 4) ISAS TEMP climatology (audited, not included in new raw stack)
- Files: `*_CLIM_ISAS_TEMP.nc` (7 gates)
- Same shape as PSAL (`time=12`, `z=187`, `nb_prof`)
- Variable: `TEMP` [°C]
- Used only for audit; excluded from new NetCDF contract by design.

### 5) GEBCO 2025
- File: `/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/GEBCO_06_Feb_2026_c91df93f54b8/gebco_2025_n90.0_s55.0_w0.0_e360.0.nc`
- Dims: `lat=8400`, `lon=86400`
- Variable: `elevation` [m] (negative ocean depth)
- Gate DB uses positive ocean depth (`depth = max(-elevation, 0)`).

### 6) `straits/*.nc` index maps (important distinction)
- Files (7):
  - `barents_sea_opening_S3_pass_481.nc`, `bering_strait_TPJ_pass_076.nc`, `davis_strait.nc`, `denmark_strait_TPJ_pass_246.nc`, `fram_strait_S3_pass_481.nc`, `nares_strait.nc`, `norwegian_sea_boundary_TPJ_pass_220.nc`
- Variables:
  - `index_lon_isas`, `index_lat_isas`
  - `index_lon_cci`, `index_lat_cci`
- Meaning: integer index vectors for profile-grid mapping, not measured salinity or velocity fields.

## Shapefile Gate vs Salinity Gate-like NetCDF Reconciliation
- Canonical geometry comes from gate shapefile (`gates/*.shp`) sampled on CMEMS native-like spacing.
- CCI/ISAS files provide separate profile coordinate vectors (`longitude`,`latitude`) on the same physical transect but different sampling and sometimes opposite ordering.
- Reconciliation workflow used in new builder:
  1. Build canonical gate from shapefile.
  2. Compare source profile endpoints to gate endpoints.
  3. Reverse source profile order if reversed endpoint pairing is closer.
  4. Remap source profile values onto canonical gate using linear interpolation in normalized along-gate distance (km-based), no extrapolation.

## Legacy Method Audit (Old Pipeline)

### A) CMEMS extraction
- Legacy approach: nearest-neighbor KDTree from L4 grid to gate points.
- Assessment: acceptable for raw-stack generation and reproducibility; preserves source values without introducing smoothing.
- Better alternative (future, optional): bilinear interpolation on CMEMS grid for smoother spatial continuity and reduced quantization at coarse grid transitions.

### B) CCI interpolation
- Legacy/new approach: linear interpolation along normalized gate distance built in km-space.
- Assessment: good and physically coherent for profile-to-profile remap.
- Correct behavior retained: no extrapolation (`NaN` outside support), monthly day1/day15 combined via `nanmean`.

### C) Known old weakness not reused in new gate DB
- Some old export scripts computed along-gate distance in degree space (`sqrt(dlon^2 + dlat^2)`) in salinity helpers.
- Risk: distorted spatial weighting at high latitude.
- Status: new builder uses km-scaled distance consistently for remap.

## Legacy Gate NetCDF (Pre-Rebuild) Snapshot
- Existing files under `data/netcdf/arcfresh_*_2002-2023.nc` were audited.
- All 20 include `theta` (legacy), and 6 include CCI salinity variables.
- New contract removes `theta` and orientation/sign metadata entirely.

## Rebuild Contract Checklist (Implemented)
- Output naming unchanged: `data/netcdf/arcfresh_{gate_id}_2002-2023.nc`
- Removed variables: `theta`
- Removed global attrs: orientation/sign/formula attrs (`into_arctic_*`, `sign_convention`, transport formula attrs)
- Added/kept raw stack variables:
  - `ugos`, `vgos`, `err_ugosa`, `err_vgosa`, `depth`, `dx`, `longitude`, `latitude`, `x_km`, `time`
  - `sss`, `sss_random_error`, `psal_isas_surface`
- For gates without salinity source file: salinity variables remain present and NaN-filled, with flags `has_cci`, `has_isas`.

## Notes on Reproducibility
- CMEMS policy set to API-only strict (no fallback to old gate NetCDF files).
- If API/network/credentials fail during runtime, rebuild is expected to fail for affected gates rather than fallback silently.

