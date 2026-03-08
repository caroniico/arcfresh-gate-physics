# 🤖 Copilot/AI Agent Instructions — ARCFRESH Gate Physics

> ⚠️ **READ GATE.md FIRST** — Every agent, every session.

## STEP 0: Read the GATE file
**Before doing ANYTHING, read:** `GATE.md`

## Project Focus
This is a **physics-only** repository for Arctic ocean transport analysis.
- NO Streamlit, NO API, NO web frontend
- Pure Python + Jupyter + NetCDF
- Core code: `analysis/utils.py`

## Reading Order
1. `GATE.md` — Project state and key info
2. `docs/01_PHYSICAL_ARCHITECTURE.md` — Physics rules
3. `docs/02_WORKFLOW_RAW_STACK.md` — Data pipeline
4. `docs/07_DATASETS_REFERENCE.md` — Dataset details
5. `analysis/utils.py` — The code

## Key Conventions
- **Sign**: v⊥ > 0 = into Arctic side
- **Projection**: Local per-point normals, NO theta
- **Constants**: S_ref=34.8, ρ=1025, depth_cap=250
- **No smoothing** beyond source data interpolation

## Python Environment
Use Python 3.11+ with: numpy, pandas, xarray, plotly, scipy, netCDF4, geopandas

## Data Locations
- NetCDF: `/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE/`
- Sources: `/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/`

## DO NOT
- Reintroduce theta or single-angle projection
- Use `fill_value='extrapolate'` for salinity
- Set FW=0 when SSS is NaN (use NaN)
- Modify sign convention without discussion
