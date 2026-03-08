# 🤖 Copilot/AI Agent Instructions — ARCFRESH Gate Physics

> ⚠️ **CRITICAL: READ GATE.md FIRST** — Every agent, every session, every time.

---

## 🚨 STEP 0: READ THE GATE (MANDATORY!)

**Before doing ANYTHING, read the main GATE file:** `GATE.md`

The GATE.md file is your single source of truth containing:
- Complete architecture
- Current project state
- Known issues and gotchas
- Key constants and conventions
- Reading order for documentation

---

## 🔄 STEP 0b: MANDATORY GIT PULL (DO THIS FIRST!)

**ALWAYS execute these commands when starting ANY new session:**

```bash
cd /Users/nicolocaron/Documents/GitHub/arcfresh-gate-physics
git fetch origin
git pull origin $(git branch --show-current)
```

---

## 📚 STEP 1: Required Reading Order

| # | File | What You Learn |
|---|------|----------------|
| 1 | `GATE.md` | Project state, architecture, constants, rules |
| 2 | `docs/01_PHYSICAL_ARCHITECTURE.md` | All physics formulas |
| 3 | `docs/02_WORKFLOW_RAW_STACK.md` | Data pipeline |
| 4 | `docs/07_DATASETS_REFERENCE.md` | Dataset details (MANDATORY for data work) |
| 5 | `docs/08_DATASET_VARIABLES.md` | Variable schemas |
| 6 | `analysis/utils.py` | The code |

---

## 🎯 Project Focus

This is a **physics-only** repository for Arctic ocean transport analysis.
- **NO** Streamlit, NO API, NO web frontend
- Pure Python + Jupyter + NetCDF
- Core code: `analysis/utils.py`

---

## ⚡ Key Conventions

### Sign Convention
- `v⊥ > 0` = into Arctic side (inflow)
- `v⊥ < 0` = away from Arctic (outflow)
- Projection: **Local per-point normals**, NO theta

### Constants
| Constant | Value |
|----------|-------|
| S_ref | 34.8 PSU |
| ρ | 1025.0 kg/m³ |
| depth_cap | 250 m |
| ARCTIC_CENTER | (0°E, 90°N) |

### Python Environment
Use Python 3.11+ with: numpy, pandas, xarray, plotly, scipy, netCDF4, geopandas

---

## 🚫 DO NOT — BANNED PATTERNS

1. **Do NOT** reintroduce theta or single-angle projection
2. **Do NOT** use `fill_value='extrapolate'` for salinity or any variable
3. **Do NOT** set FW=0 when SSS is NaN (propagate NaN)
4. **Do NOT** modify sign convention without discussion
5. **Do NOT** reference any "old" NetCDF directory — it's redundant
6. **Do NOT** duplicate existing functions from utils.py
7. **Do NOT** use `python3` or `pip3` — use venv Python

---

## 📁 Data Locations

| What | Path |
|------|------|
| Gate NetCDF files | `/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE/` |
| Source data | `/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/` |
| Gate shapefiles | `/Users/nicolocaron/Documents/GitHub/ARCFRESH-DTU-NICO-and-AMALIE/gates/` |

---

## 📋 TASK PROTOCOL

**Before ANY task:**
1. Read `GATE.md` (mandatory)
2. Read `docs/01_PHYSICAL_ARCHITECTURE.md` if touching physics
3. Read `docs/07_DATASETS_REFERENCE.md` if touching data
4. Check existing code in `analysis/utils.py` before writing new functions

---

## ✅ Pre-Commit Checklist

Before EVERY commit:
- [ ] `git pull origin main`
- [ ] Run tests: `python -m pytest tests/ -v`
- [ ] Update `GATE.md` if project state changed
- [ ] Verify no theta/old references crept back in

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ARCFRESH GATE PHYSICS                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              analysis/utils.py                       │    │
│  │  Core physics engine (596 lines)                     │    │
│  │  local_into_arctic_unit_vectors()                    │    │
│  │  perpendicular_velocity() + uncertainty              │    │
│  │  volume_transport() + per_point + uncertainty        │    │
│  │  freshwater_transport() + per_point + uncertainty    │    │
│  │  salt_flux() + per_point + uncertainty               │    │
│  │  monthly_mean, annual_mean, monthly_climatology      │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │         analysis/gate_analysis.ipynb                 │    │
│  │  Interactive Plotly analysis (16 cells)               │    │
│  │  v⊥ profiles + timeseries                            │    │
│  │  VT profiles + timeseries                            │    │
│  │  SSS profiles (CCI + ISAS)                           │    │
│  │  FW transport + timeseries                           │    │
│  │  Salt flux + timeseries                              │    │
│  │  Spatial map with normals + velocity vectors         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          scripts/build_gate_netcdf.py                │    │
│  │  Build NetCDF from: shapefiles + CMEMS + CCI + ISAS │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER                        │    │
│  │  Gate NetCDF files (20 gates, 2002-2023)             │    │
│  │  Variables: ugos, vgos, err_*, sss, psal_isas,       │    │
│  │            depth, dx, x_km, lon, lat                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```
