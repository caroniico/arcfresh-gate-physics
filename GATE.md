# 🚪 GATE — ARCFRESH Gate Physics

> **Read this file FIRST, every session.**

## Project Identity
- **Name**: arcfresh-gate-physics
- **Purpose**: Physics-only analysis of Arctic ocean transports across 20 gates
- **Parent**: ARCFRESH-DTU-NICO-and-AMALIE (Streamlit/API — parked)

## Current State (2026-03-08)
- ✅ Local per-point projection implemented (no theta)
- ✅ 20/20 gate NetCDF files produced
- ✅ Plotly notebook for interactive analysis
- ✅ Tests for projection + build helpers
- ✅ Full dataset audit + old/new comparison (delta 0%)
- 🔴 NetCDF files NOT yet rebuilt with new builder (still contain old theta field)
- 🔴 Need to verify dx and all variables before rebuild

## Key Files
| File | What it does |
|------|-------------|
| `analysis/utils.py` | Core physics: local projection, VT, FW, Salt (596 lines) |
| `analysis/gate_analysis.ipynb` | Interactive Plotly notebook (17 cells) |
| `scripts/build_gate_netcdf.py` | Build raw NetCDF from shapefiles + CMEMS + CCI + ISAS |
| `docs/01_PHYSICAL_ARCHITECTURE.md` | Physics rules and formulas |
| `docs/02_WORKFLOW_RAW_STACK.md` | Data pipeline description |

## Constants
| Constant | Value | Where |
|----------|-------|-------|
| S_ref | 34.8 PSU | utils.py |
| ρ | 1025.0 kg/m³ | utils.py |
| depth_cap | 250 m | utils.py |
| ARCTIC_CENTER | (0°E, 90°N) | utils.py |

## Sign Convention
- `v⊥ > 0` → into Arctic side (inflow)
- `v⊥ < 0` → away from Arctic (outflow)
- Normal oriented toward (0°E, 90°N) at each point

## Data Locations (local machine)
- NetCDF files: `/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE/`
- Old NetCDF: `/Users/nicolocaron/Desktop/ARCFRESH/netcdf/`
- Source data: `/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/`
- Gate shapefiles: from parent repo `gates/` directory

## Known Issues
1. Density inconsistency: utils.py (1025) vs old transport_service.py (1027)
2. NetCDF files need rebuild with new builder
3. Some gates (ESS-CAO) are split into yearly files due to size

## Reading Order for Agents
1. This file (GATE.md)
2. `docs/01_PHYSICAL_ARCHITECTURE.md`
3. `docs/02_WORKFLOW_RAW_STACK.md`
4. `docs/07_DATASETS_REFERENCE.md`
5. `analysis/utils.py` (the code)
