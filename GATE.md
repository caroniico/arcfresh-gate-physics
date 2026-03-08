# 🚪 GATE — ARCFRESH Gate Physics

> ⚠️ **STOP! READ THIS ENTIRE FILE BEFORE ANY ACTION**  
> 📅 Last Updated: 2026-03-08

---

## 🔒 MANDATORY CHECKLIST (DO BEFORE ANYTHING)

```
□ 1. Read this ENTIRE file (GATE.md)
□ 2. Run: git fetch && git pull origin $(git branch --show-current)
□ 3. Read docs/01_PHYSICAL_ARCHITECTURE.md
□ 4. Read docs/07_DATASETS_REFERENCE.md  ← MANDATORY if working on data/export
□ 5. Understand the key constants and sign conventions (below)
□ 6. Check current state (Section 3)
□ 7. Review known issues (Section 4)
□ 8. THEN and ONLY THEN proceed with your task
```

---

## 📐 SECTION 1: PROJECT IDENTITY

| Field | Value |
|-------|-------|
| **Project** | ARCFRESH Gate Physics |
| **Purpose** | Physics-only analysis of Arctic ocean transports across 20 gates |
| **Parent** | ARCFRESH-DTU-NICO-and-AMALIE (Streamlit/API — parked) |
| **Language** | Python 3.11+ (numpy, pandas, xarray, plotly, scipy, netCDF4, geopandas) |
| **Focus** | Pure Python + Jupyter + NetCDF — NO Streamlit, NO API, NO web frontend |

---

## 🏗️ SECTION 2: ARCHITECTURE

### 2.1 Directory Structure

```
arcfresh-gate-physics/
├── GATE.md                         ← 🚨 YOU ARE HERE - READ FIRST!
├── README.md                       ← Project overview with quick start
├── .github/
│   └── copilot-instructions.md     ← Points to this GATE.md
│
├── analysis/                       # ⭐ CORE CODE
│   ├── utils.py                    # Physics: local projection, VT, FW, Salt (596 lines)
│   └── gate_analysis.ipynb         # Interactive Plotly notebook
│
├── scripts/                        # Build/export tools
│   └── build_gate_netcdf.py        # Build raw NetCDF from shapefiles + CMEMS + CCI + ISAS
│
├── tests/                          # Unit tests
│   ├── test_analysis_utils_projection.py
│   └── test_build_gate_netcdf_helpers.py
│
├── docs/                           # 📚 Documentation (12 files)
│   ├── 01_PHYSICAL_ARCHITECTURE.md # Physics rules and formulas
│   ├── 02_WORKFLOW_RAW_STACK.md    # Data pipeline description
│   ├── 03_NETCDF_PRODUCTION_STATUS.md
│   ├── 04_OPERATION_CHECKLIST.md
│   ├── 05_GATE_CATALOG_AND_PRODUCTION.md
│   ├── 06_GATE_STATS_*.md/csv
│   ├── 07_DATASETS_REFERENCE.md    # ⚠️ MANDATORY for data work
│   ├── 08_DATASET_VARIABLES.md     # Complete variable schemas
│   └── 09_GATES_CATALOG.md         # Gate positions and satellite passes
│
└── reports/                        # Audit and verification reports
    ├── GATE_DATASET_AUDIT_20260307.md
    └── OLD_NEW_LOCAL_METHOD_COMPARISON_20260307.md
```

### 2.2 Key Files

| File | Lines | What it does |
|------|-------|-------------|
| `analysis/utils.py` | 596 | Core physics engine: `local_into_arctic_unit_vectors()`, `perpendicular_velocity()`, `volume_transport()`, `freshwater_transport()`, `salt_flux()` + per_point + uncertainty variants |
| `analysis/gate_analysis.ipynb` | ~16 cells | Interactive Plotly analysis: v⊥, VT, SSS, FW, Salt — 4×3 monthly profiles + timeseries + spatial map |
| `scripts/build_gate_netcdf.py` | ~400 | Build raw gate NetCDF from shapefiles + CMEMS L4 + CCI SSS + ISAS PSAL |
| `docs/01_PHYSICAL_ARCHITECTURE.md` | — | All physics formulas and rules |
| `docs/07_DATASETS_REFERENCE.md` | — | Mandatory reading for data work |

### 2.3 Physics Constants

| Constant | Value | Where |
|----------|-------|-------|
| S_ref | 34.8 PSU | utils.py |
| ρ | 1025.0 kg/m³ | utils.py |
| depth_cap | 250 m | utils.py |
| ARCTIC_CENTER | (0°E, 90°N) | utils.py |
| SVERDRUP | 10⁶ m³/s | utils.py |

### 2.4 Sign Convention

- `v⊥ > 0` → into Arctic side (inflow)
- `v⊥ < 0` → away from Arctic (outflow)
- Normal oriented toward (0°E, 90°N) at each point
- `v⊥(i,t) = ugos(i,t)·u_into_local(i) + vgos(i,t)·v_into_local(i)`
- **No theta** field is used — projection is purely local per-point

### 2.5 Dataset Variables in Gate NetCDF

| Variable | Source | Temporal | Spatial |
|---|---|---|---|
| `ugos`, `vgos` | CMEMS L4 DUACS | Daily | 0.125° remapped to gate points |
| `err_ugosa`, `err_vgosa` | CMEMS L4 formal error | Daily | 0.125° remapped |
| `sss`, `sss_random_error` | ESA CCI SSS v5.5 | Monthly→daily | remapped along gate |
| `psal_isas_surface` | ISAS climatology (z0) | Monthly clim→daily | remapped along gate |
| `depth` | GEBCO 2025 | Static | gate points |
| `dx`, `x_km`, `longitude`, `latitude` | Gate geometry | Static | gate points |

---

## 📊 SECTION 3: CURRENT STATE

### 3.1 What Works ✅
- Local per-point projection (no theta)
- 20/20 gate NetCDF files exist
- Plotly notebook for interactive analysis (v⊥, VT, SSS, FW, Salt)
- Spatial mapping with local normals and velocity vectors
- Tests for projection + build helpers
- Full dataset audit + old/new comparison verified (delta = 0)

### 3.2 Verified ✅
- OLD and NEW NetCDF datasets are functionally identical
- 9 gates are bit-identical (same variables)
- 10 gates differ only in: OLD has `theta` (removed), NEW adds `psal_isas_surface`, `sss`, `sss_random_error`
- 3 gates show x_km noise at ~10⁻¹⁴ level (floating-point, zero impact)
- **OLD dataset is REDUNDANT — all analysis should use NEW only**

### 3.3 In Progress 🔄
- NetCDF rebuild with updated builder (no theta output)

### 3.4 Known Issues ⚠️
1. Density inconsistency: utils.py (1025) vs old transport_service.py (1027)
2. ESS-CAO gate split into yearly files due to size
3. Nares Strait: 0% CCI SSS coverage (all ice) → no FWT/SF

---

## ⚠️ SECTION 4: RULES AND GOTCHAS

### 4.1 BANNED Patterns 🚫
```python
# 🚫 BANNED — NEVER use extrapolation
interp_func = interp1d(x, y, fill_value='extrapolate')

# ✅ CORRECT
interp_func = interp1d(x, y, bounds_error=False, fill_value=np.nan)
```

### 4.2 Do NOT
- Reintroduce theta or single-angle projection
- Use `fill_value='extrapolate'` for any variable
- Set FW=0 when SSS is NaN (use NaN to propagate)
- Modify sign convention without discussion
- Duplicate existing functions in utils.py
- Reference OLD NetCDF directory (it's redundant)

### 4.3 Data Locations (local machine)

| What | Path |
|------|------|
| Gate NetCDF files | `/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE/` |
| Source data | `/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/` |
| Gate shapefiles | `/Users/nicolocaron/Documents/GitHub/ARCFRESH-DTU-NICO-and-AMALIE/gates/` |

---

## 📚 SECTION 5: READING ORDER FOR AGENTS

| # | File | What You Learn |
|---|------|----------------|
| 1 | `GATE.md` | Project state, architecture, constants, rules |
| 2 | `docs/01_PHYSICAL_ARCHITECTURE.md` | All physics formulas |
| 3 | `docs/02_WORKFLOW_RAW_STACK.md` | Data pipeline (shapefiles → NetCDF) |
| 4 | `docs/07_DATASETS_REFERENCE.md` | Dataset details, CCI SSS handling, NaN policy |
| 5 | `docs/08_DATASET_VARIABLES.md` | Variable schemas for all datasets |
| 6 | `analysis/utils.py` | The actual code |

---

## ✅ SECTION 6: PRE-COMMIT CHECKLIST

Before EVERY commit:
- [ ] Run `git pull origin main` first
- [ ] Run tests: `python -m pytest tests/ -v`
- [ ] Update this GATE.md if state changed
- [ ] Check no old/theta references crept in

---

**🔚 END OF GATE.md - PROCEED WITH TASK**
