# 🌊 ARCFRESH Gate Physics

> **Arctic Freshwater Transport** — Gate-based analysis of volume, freshwater, and salt transport across 20 Arctic Ocean gates using satellite-derived geostrophic velocities and surface salinity.

---

## 📋 What this repo does

This repository contains the **physics analysis pipeline** for computing ocean transports across Arctic gates:

1. **Build self-contained NetCDF** files per gate (one file = one gate, daily 2002–2023)
2. **Compute transports** using local per-point projection of geostrophic velocity
3. **Visualize** results with interactive Plotly plots

### Key innovation: Local per-point projection (no theta)

Instead of a single angle θ per gate, **each gate point** gets its own into-Arctic normal vector computed from the gate geometry at runtime:

```
v⊥(i,t) = ugos(i,t) · u_into_local(i) + vgos(i,t) · v_into_local(i)
```

- `v⊥ > 0` → inflow toward Arctic side
- No `theta` stored in NetCDF files
- Physics applied only at analysis time

---

## 📁 Repository Structure

```
analysis/
  utils.py               ← Core physics: projection, VT, FW, Salt (596 lines)
  gate_analysis.ipynb     ← Interactive Plotly notebook for any gate

scripts/
  build_gate_netcdf.py    ← Build raw NetCDF from shapefiles + CMEMS + CCI + ISAS

tests/
  test_analysis_utils_projection.py
  test_build_gate_netcdf_helpers.py

docs/                     ← Architecture, workflow, gate catalog, dataset specs
  01_PHYSICAL_ARCHITECTURE.md
  02_WORKFLOW_RAW_STACK.md
  03_NETCDF_PRODUCTION_STATUS.md
  04_OPERATION_CHECKLIST.md
  05_GATE_CATALOG_AND_PRODUCTION.md
  06_GATE_STATS_*.{md,csv}
  07_DATASETS_REFERENCE.md
  08_DATASET_VARIABLES.md
  09_GATES_CATALOG.md

reports/                  ← Audit and comparison reports
  GATE_DATASET_AUDIT_20260307.md
  OLD_NEW_LOCAL_METHOD_COMPARISON_20260307.md
```

---

## 🗺️ 20 Arctic Gates

| Region | Gates |
|--------|-------|
| **External boundaries** | Fram Strait, Bering Strait, Davis Strait, Barents Opening, Denmark Strait, Norwegian Boundary |
| **Canadian Arctic** | Nares Strait, Lancaster Sound, Jones Sound |
| **Barents Sea** | Barents Sea–CAO, Barents Sea–Kara Sea |
| **Kara Sea** | Kara Sea–CAO, Kara Sea–Laptev Sea |
| **Laptev Sea** | Laptev Sea–CAO, Laptev Sea–ESS |
| **East Siberian Seas** | ESS–CAO, ESS–Beaufort Sea |
| **Beaufort Sea** | Beaufort Sea–CAO, Beaufort Sea–CAA |
| **CAA** | CAA–CAO |

---

## 📊 Data Sources

| Variable | Source | Resolution |
|----------|--------|-----------|
| `ugos`, `vgos` | CMEMS L4 DUACS (SEALEVEL_GLO_PHY_L4_MY_008_047) | 0.125° daily |
| `err_ugosa`, `err_vgosa` | CMEMS L4 formal mapping error | 0.125° daily |
| `sss`, `sss_random_error` | ESA CCI SSS v5.5 | Semi-monthly → monthly, remapped |
| `psal_isas_surface` | ISAS PSAL climatology (z0 layer) | Monthly climatology, remapped |
| `depth` | GEBCO 2025 | 15 arc-sec |
| Gate geometry | Sara shapefiles | Native resolution |

---

## 🔬 Transport Formulas

With `H(i) = min(depth(i), 250m)` and `dx(i)` from gate geometry:

| Quantity | Formula | Units |
|----------|---------|-------|
| **Volume Transport** | `VT(t) = Σᵢ v⊥(i,t) · H(i) · dx(i) / 10⁶` | Sv |
| **Freshwater Transport** | `FW(t) = Σᵢ v⊥(i,t) · (1 - S(i,t)/S_ref) · H(i) · dx(i)` | m³/s |
| **Salt Flux** | `SF(t) = Σᵢ ρ · (S(i,t)/1000) · v⊥(i,t) · H(i) · dx(i)` | kg/s |

Constants: `S_ref = 34.8 PSU`, `ρ = 1025 kg/m³`, `depth_cap = 250 m`

---

## 🚀 Quick Start

```python
# In analysis/ directory
from utils import load_gate, perpendicular_velocity, volume_transport

ds = load_gate('path/to/arcfresh_fram_strait_2002-2023.nc')
ds = ds.sel(time=slice('2010', '2023'))

v_perp = perpendicular_velocity(ds)           # (point, time)
vt_sv, time = volume_transport(ds, depth_cap=250)  # (time,) in Sv
```

---

## 🔗 Related

- **Parent project**: [ARCFRESH-DTU-NICO-and-AMALIE](https://github.com/caroniico/ARCFRESH-DTU-NICO-and-AMALIE) — Full stack with Streamlit dashboard + API (parked)
- **Data provider**: [Copernicus Marine Service](https://marine.copernicus.eu/)
- **Gate shapefiles**: Provided by Sara (DTU Space)
