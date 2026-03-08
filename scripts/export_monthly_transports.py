#!/usr/bin/env python3
"""
Export monthly Salt-mass and Freshwater transports for all ARCFRESH gates.

Output CSV layout mirrors the consortium spreadsheet "Ocean Gates" sheet:
  Separator: ;  (semicolon)
  Encoding:  UTF-8 with BOM
  Line endings: CRLF (Windows)
  Year ; Month ; Sm ; SmU ; Fw ; FwU ; ... (×35 gate-columns)

Salinity source (NO fallback / NO mixing between sources):
  - 2010–2023 → CCI SSS v5.5  (variable 'sss')
  - 2002–2009 → ISAS PSAL z0  (variable 'psal_isas_surface')

If the chosen source has no finite data for a gate → NaN (no fallback).

Uncertainty is propagated from CMEMS velocity errors only:
  σ_v⊥(i,t) = √((err_ugosa·u_loc)² + (err_vgosa·v_loc)²)

Consortium definitions & assumptions:
  ρ            = 1024 kg/m³
  S_ref        = 34.8 PSU  [10⁻³ kg/kg]
  Salt mass    = ρ · (S/1000) · v⊥ · H · dx                           [kg/s]
  Freshwater   = v⊥ · (1 − S/S_ref) · H · dx                         [m³/s → Sv]

Units in CSV (consortium spreadsheet):
  Sm, SmU  → kg/s        (kilogram per second)
  Fw, FwU  → Sv          (1 million m³ per second)

Positive transport = flow into the basin (Arctic side).

Usage:
    source .venv/bin/activate
    python scripts/export_monthly_transports.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# ── project imports ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "analysis"))

from utils import (                                      # noqa: E402
    load_gate,
    perpendicular_velocity,
    perpendicular_velocity_uncertainty,
    SVERDRUP,
)

warnings.filterwarnings("ignore", "Mean of empty slice")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
NC_DIR = Path("/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE")
OUTPUT_PATH = PROJECT_ROOT / "analysis" / "arcfresh_monthly_transports.csv"

DEPTH_CAP = 250.0   # m
S_REF     = 34.8     # PSU
RHO       = 1024.0   # kg/m³

# Period covered
YEAR_START = 2002
YEAR_END   = 2023

# Salinity split
CCI_START_YEAR = 2010   # 2010-01 .. 2023-12  → use 'sss'
ISAS_END_YEAR  = 2009   # 2002-01 .. 2009-12  → use 'psal_isas_surface'

# ── Gate → NetCDF file mapping ────────────────────────────────────────────
# gate_id : single-file name (without .nc) or 'YEARLY' for split files
GATE_FILES: dict[str, str | list[str]] = {
    "fram_strait":          "arcfresh_fram_strait_2002-2023",
    "bering_strait":        "arcfresh_bering_strait_2002-2023",
    "davis_strait":         "arcfresh_davis_strait_2002-2023",
    "barents_opening":      "arcfresh_barents_opening_2002-2023",
    "denmark_strait":       "arcfresh_denmark_strait_2002-2023",
    "norwegian_boundary":   "arcfresh_norwegian_boundary_2002-2023",
    "barents_sea_cao":      "arcfresh_barents_sea_cao_2002-2023",
    "barents_sea_kara_sea": "arcfresh_barents_sea_kara_sea_2002-2023",
    "kara_sea_cao":         "arcfresh_kara_sea_cao_2002-2023",
    "kara_sea_laptev_sea":  "arcfresh_kara_sea_laptev_sea_2002-2023",
    "laptev_sea_cao":       "arcfresh_laptev_sea_cao_2002-2023",
    "laptev_sea_ess":       "arcfresh_laptev_sea_ess_2002-2023",
    "ess_cao":              "YEARLY",   # split into yearly files 2002-2015
    "ess_beaufort_sea":     "arcfresh_ess_beaufort_sea_2002-2023",
    "beaufort_sea_cao":     "arcfresh_beaufort_sea_cao_2002-2023",
    "beaufort_sea_caa":     "arcfresh_beaufort_sea_caa_2002-2023",
    "caa_cao":              "arcfresh_caa_cao_2002-2023",
    "lancaster_sound":      "arcfresh_lancaster_sound_2002-2023",
    "jones_sound":          "arcfresh_jones_sound_2002-2023",
    "nares_strait":         "arcfresh_nares_strait_2002-2023",
}

# ── Spreadsheet column order (35 gate-slots) ─────────────────────────────
# Matches exactly the consortium spreadsheet "Ocean Gates" sheet.
# Each entry: (region, display_name, gate_id, sign_flip)
#   sign_flip = False  → keep original sign (flow INTO Arctic side)
#   sign_flip = True   → negate (same gate seen from opposite basin)
#
# Separator: ;  |  Line endings: CRLF  |  BOM UTF-8
# Cell A1 = "Ocean Gates"
#
COLUMN_ORDER: list[tuple[str, str, str, bool]] = [
    # ── Arctic Ocean (external boundaries)  — 5 gate-slots ──
    ("Arctic Ocean (external boundaries)", "Fram Strait",              "fram_strait",          False),
    ("Arctic Ocean (external boundaries)", "Bering Strait",            "bering_strait",        False),
    ("Arctic Ocean (external boundaries)", "Davies Strait",            "davis_strait",         False),
    ("Arctic Ocean (external boundaries)", "Barents Sea Opening",      "barents_opening",      False),
    ("Arctic Ocean (external boundaries)", "Bering Strait",            "bering_strait",        True ),   # duplicate in consortium
    # ── Barents Sea  — 3 gate-slots ──
    ("Barents Sea",                        "Barents Sea \u2013 CAO",   "barents_sea_cao",      False),
    ("Barents Sea",                        "Barents Sea \u2013 Kara Sea", "barents_sea_kara_sea", False),
    ("Barents Sea",                        "Barents Sea Opening",      "barents_opening",      True ),
    # ── Kara Sea  — 3 gate-slots ──
    ("Kara Sea",                           "Kara Sea \u2013 Barents Sea", "barents_sea_kara_sea", True ),
    ("Kara Sea",                           "Kara Sea - CAO",           "kara_sea_cao",         False),
    ("Kara Sea",                           "Kara Sea - Laptev Sea",    "kara_sea_laptev_sea",  False),
    # ── Laptev Sea  — 3 gate-slots ──
    ("Laptev Sea",                         "Laptev Sea - Kara Sea",    "kara_sea_laptev_sea",  True ),
    ("Laptev Sea",                         "Laptev Seas - CAO",        "laptev_sea_cao",       False),
    ("Laptev Sea",                         "Laptev Sea - ESS",         "laptev_sea_ess",       False),
    # ── East Siberian Seas (ESS)  — 3 gate-slots ──
    ("East Siberian Seas (ESS)",           "ESS - Laptev Sea",         "laptev_sea_ess",       True ),
    ("East Siberian Seas (ESS)",           "ESS - CAO",               "ess_cao",              False),
    ("East Siberian Seas (ESS)",           "ESS - Beaufort Sea",       "ess_beaufort_sea",     False),
    # ── Beaufort Sea  — 3 gate-slots ──
    ("Beaufort Sea",                       "Beaufort Sea - ESS",       "ess_beaufort_sea",     True ),
    ("Beaufort Sea",                       "Beaufort Sea - CAO",       "beaufort_sea_cao",     False),
    ("Beaufort Sea",                       "Beaufort Sea - CAA",       "beaufort_sea_caa",     False),
    # ── Canadian Arctic Archipelago (CAA)  — 5 gate-slots ──
    ("Canadian Arctic Archipelago (CAA)",  "CAA - Beaufort Sea",       "beaufort_sea_caa",     True ),
    ("Canadian Arctic Archipelago (CAA)",  "CAA - CAO",               "caa_cao",              False),
    ("Canadian Arctic Archipelago (CAA)",  "Lancaster Sound",          "lancaster_sound",      False),
    ("Canadian Arctic Archipelago (CAA)",  "Jones Sound",              "jones_sound",          False),
    ("Canadian Arctic Archipelago (CAA)",  "Nares Strait",             "nares_strait",         False),
    # ── Baffin Bay  — 4 gate-slots ──
    ("Baffin Bay",                         "Lancaster Sound",          "lancaster_sound",      True ),
    ("Baffin Bay",                         "Jones Sound",              "jones_sound",          True ),
    ("Baffin Bay",                         "Nares Strait",             "nares_strait",         True ),
    ("Baffin Bay",                         "Davies Strait",            "davis_strait",         True ),
    # ── Central Arctic Ocean (CAO)  — 6 gate-slots ──
    ("Central Arctic Ocean (CAO)",         "CAO - Barents Sea",        "barents_sea_cao",      True ),
    ("Central Arctic Ocean (CAO)",         "CAO - Kara Sea",           "kara_sea_cao",         True ),
    ("Central Arctic Ocean (CAO)",         "CAO - Laptev Sea",         "laptev_sea_cao",       True ),
    ("Central Arctic Ocean (CAO)",         "CAO - ESS",               "ess_cao",              True ),
    ("Central Arctic Ocean (CAO)",         "CAO - Beaufort Sea",       "beaufort_sea_cao",     True ),
    ("Central Arctic Ocean (CAO)",         "CAO - CAA",               "caa_cao",              True ),
    # ── Additional gates (not in Sara's consortium sheet) ──
    ("Additional",                         "Denmark Strait",           "denmark_strait",       False),
    ("Additional",                         "Norwegian Boundary",       "norwegian_boundary",   False),
]


# ═══════════════════════════════════════════════════════════════════════════
# PHYSICS HELPERS  (vectorised, daily → monthly)
# ═══════════════════════════════════════════════════════════════════════════

def _choose_salinity(ds, year: int):
    """Return the salinity array to use for a given year.

    - 2010+ → 'sss' (CCI v5.5)
    - 2002-2009 → 'psal_isas_surface' (ISAS)
    - If the chosen field is absent or all-NaN → return None
    """
    if year >= CCI_START_YEAR:
        var = "sss"
    else:
        var = "psal_isas_surface"

    if var not in ds:
        return None
    arr = ds[var].values
    if not np.isfinite(arr).any():
        return None
    return arr


def _compute_daily(ds, depth_cap, s_ref, rho):
    """Compute daily Sm, SmU, Fw, FwU for the full time axis of ds.

    Returns dict with arrays of shape (time,).
    Salinity is selected per-year (CCI 2010+ / ISAS 2002-2009).
    """
    v_perp = perpendicular_velocity(ds)                 # (point, time)
    sigma_vp = perpendicular_velocity_uncertainty(ds)    # (point, time)
    H = np.minimum(ds["depth"].values, depth_cap)        # (point,)
    dx = ds["dx"].values                                 # (point,)

    time = pd.to_datetime(ds["time"].values)
    n_time = len(time)
    n_pts = ds.sizes["point"]

    sm_daily  = np.full(n_time, np.nan)
    smu_daily = np.full(n_time, np.nan)
    fw_daily  = np.full(n_time, np.nan)
    fwu_daily = np.full(n_time, np.nan)

    # Pre-compute geometry weights: H(i) * dx(i)
    hdx = H * dx                                         # (point,)

    # Group time indices by year so we pick the right salinity source
    years = time.year
    unique_years = np.unique(years)

    for yr in unique_years:
        yr = int(yr)
        mask_yr = (years == yr)
        t_idx = np.where(mask_yr)[0]

        # Select salinity for this year range
        sal = _choose_salinity_for_year(ds, yr)
        if sal is None:
            # No salinity → Sm/Fw stay NaN for this year
            continue

        # sal shape: (point, time) — slice to this year
        sal_yr = sal[:, t_idx]                           # (point, n_yr)
        vp_yr  = v_perp[:, t_idx]                        # (point, n_yr)
        svp_yr = sigma_vp[:, t_idx]                      # (point, n_yr)

        # Salt mass: Sm(t) = Σᵢ ρ·(S/1000)·v⊥·H·dx
        integrand_sm = rho * (sal_yr / 1000.0) * vp_yr * hdx[:, None]
        sm_t = np.where(
            np.all(np.isnan(integrand_sm), axis=0),
            np.nan,
            np.nansum(integrand_sm, axis=0),
        )
        sm_daily[t_idx] = sm_t

        # SmU(t) = √(Σᵢ (ρ·S/1000·σ_v⊥·H·dx)²)
        terms_smu = rho * (sal_yr / 1000.0) * svp_yr * hdx[:, None]
        smu_daily[t_idx] = np.sqrt(np.nansum(terms_smu**2, axis=0))

        # Freshwater: Fw(t) = Σᵢ v⊥·(1−S/S_ref)·H·dx
        fw_factor = 1.0 - sal_yr / s_ref
        integrand_fw = vp_yr * fw_factor * hdx[:, None]
        fw_t = np.where(
            np.all(np.isnan(integrand_fw), axis=0),
            np.nan,
            np.nansum(integrand_fw, axis=0),
        )
        fw_daily[t_idx] = fw_t / SVERDRUP    # → Sv

        # FwU(t) = √(Σᵢ (σ_v⊥·|1−S/S_ref|·H·dx)²) / 1e6  → Sv
        terms_fwu = svp_yr * np.abs(fw_factor) * hdx[:, None]
        fwu_daily[t_idx] = np.sqrt(np.nansum(terms_fwu**2, axis=0)) / SVERDRUP

    return {
        "time": time,
        "Sm":  sm_daily,
        "SmU": smu_daily,
        "Fw":  fw_daily,
        "FwU": fwu_daily,
    }


def _choose_salinity_for_year(ds, year: int):
    """Return full (point, time) salinity array if the source for `year` exists."""
    if year >= CCI_START_YEAR:
        var = "sss"
    else:
        var = "psal_isas_surface"

    if var not in ds:
        return None
    arr = ds[var].values
    if not np.isfinite(arr).any():
        return None
    return arr


def _monthly_aggregate(daily: dict) -> pd.DataFrame:
    """Aggregate daily Sm/SmU/Fw/FwU to monthly.

    - Sm, Fw  → monthly mean
    - SmU, FwU → monthly RMS  (√(mean(σ²)))
    """
    df = pd.DataFrame({
        "Sm":  daily["Sm"],
        "SmU": daily["SmU"],
        "Fw":  daily["Fw"],
        "FwU": daily["FwU"],
    }, index=daily["time"])

    monthly = df.resample("MS").apply(
        lambda g: pd.Series({
            "Sm":  np.nanmean(g["Sm"])  if np.isfinite(g["Sm"]).any()  else np.nan,
            "SmU": np.sqrt(np.nanmean(g["SmU"]**2)) if np.isfinite(g["SmU"]).any() else np.nan,
            "Fw":  np.nanmean(g["Fw"])  if np.isfinite(g["Fw"]).any()  else np.nan,
            "FwU": np.sqrt(np.nanmean(g["FwU"]**2)) if np.isfinite(g["FwU"]).any() else np.nan,
        })
    )
    monthly.index.name = "date"
    return monthly.reset_index()


# ═══════════════════════════════════════════════════════════════════════════
# GATE LOADING  (handles ess_cao yearly split)
# ═══════════════════════════════════════════════════════════════════════════

def _load_gate_datasets(gate_id: str):
    """Yield (ds, label) for a gate. Handles yearly-split files for ess_cao."""
    spec = GATE_FILES[gate_id]
    if spec == "YEARLY":
        import glob
        pattern = str(NC_DIR / f"arcfresh_{gate_id}_*-*.nc")
        files = sorted(glob.glob(pattern))
        if not files:
            print(f"  ⚠️  No files found for {gate_id}")
            return
        for f in files:
            ds = load_gate(f)
            yield ds, Path(f).stem
            ds.close()
    else:
        path = NC_DIR / f"{spec}.nc"
        if not path.exists():
            print(f"  ⚠️  File not found: {path.name}")
            return
        ds = load_gate(path)
        yield ds, spec
        ds.close()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("ARCFRESH — Export Monthly Transports")
    print(f"  NC_DIR    : {NC_DIR}")
    print(f"  Output    : {OUTPUT_PATH}")
    print(f"  Period    : {YEAR_START}–{YEAR_END}")
    print(f"  Salinity  : ISAS ({YEAR_START}–{ISAS_END_YEAR}) / CCI ({CCI_START_YEAR}–{YEAR_END})")
    print(f"  ρ={RHO} kg/m³  |  S_ref={S_REF} PSU  |  depth_cap={DEPTH_CAP} m")
    print("=" * 72)

    # ── Build monthly index ───────────────────────────────────────────────
    date_range = pd.date_range(
        f"{YEAR_START}-01-01", f"{YEAR_END}-12-01", freq="MS"
    )
    index_df = pd.DataFrame({
        "Year":  date_range.year,
        "Month": date_range.month,
    })

    # ── Compute per gate ──────────────────────────────────────────────────
    # Cache: gate_id → monthly DataFrame (date, Sm, SmU, Fw, FwU)
    gate_cache: dict[str, pd.DataFrame] = {}

    unique_gates = sorted(set(gid for _, _, gid, _ in COLUMN_ORDER))
    for i, gate_id in enumerate(unique_gates, 1):
        print(f"\n[{i}/{len(unique_gates)}] Processing: {gate_id}")

        monthly_parts: list[pd.DataFrame] = []

        for ds, label in _load_gate_datasets(gate_id):
            print(f"  Loading {label} ... pts={ds.sizes['point']}, days={ds.sizes['time']}")
            daily = _compute_daily(ds, DEPTH_CAP, S_REF, RHO)
            monthly = _monthly_aggregate(daily)
            monthly_parts.append(monthly)

        if not monthly_parts:
            print(f"  → No data for {gate_id}")
            gate_cache[gate_id] = pd.DataFrame(columns=["date", "Sm", "SmU", "Fw", "FwU"])
            continue

        all_monthly = pd.concat(monthly_parts, ignore_index=True).sort_values("date")
        gate_cache[gate_id] = all_monthly
        n_valid_sm = int(np.isfinite(all_monthly["Sm"]).sum())
        n_valid_fw = int(np.isfinite(all_monthly["Fw"]).sum())
        print(f"  → {len(all_monthly)} months  (Sm valid: {n_valid_sm}, Fw valid: {n_valid_fw})")

    # ── Assemble wide CSV ─────────────────────────────────────────────────
    print("\n" + "─" * 72)
    print("Assembling CSV ...")

    result = index_df.copy()

    for region, gate_display, gate_id, flip in COLUMN_ORDER:
        prefix = f"{gate_display}"
        monthly = gate_cache.get(gate_id, pd.DataFrame())

        if monthly.empty or "date" not in monthly.columns:
            result[f"{prefix}_Sm"]  = np.nan
            result[f"{prefix}_SmU"] = np.nan
            result[f"{prefix}_Fw"]  = np.nan
            result[f"{prefix}_FwU"] = np.nan
            continue

        # Merge on Year+Month
        monthly = monthly.copy()
        monthly["Year"]  = monthly["date"].dt.year
        monthly["Month"] = monthly["date"].dt.month

        merged = index_df.merge(
            monthly[["Year", "Month", "Sm", "SmU", "Fw", "FwU"]],
            on=["Year", "Month"],
            how="left",
        )

        sign = -1.0 if flip else 1.0
        result[f"{prefix}_Sm"]  = merged["Sm"]  * sign
        result[f"{prefix}_SmU"] = merged["SmU"]          # uncertainty always positive
        result[f"{prefix}_Fw"]  = merged["Fw"]  * sign
        result[f"{prefix}_FwU"] = merged["FwU"]          # uncertainty always positive

    # ── Write CSV (consortium format: ; separator, BOM UTF-8, CRLF) ─────
    # Build multi-level header rows
    header_row1 = ["Ocean Gates", ""]   # A1 = "Ocean Gates"
    header_row2 = ["", ""]
    header_row3 = ["Year", "Month"]

    for region, gate_display, gate_id, flip in COLUMN_ORDER:
        header_row1.extend([region, "", "", ""])
        header_row2.extend([gate_display, "", "", ""])
        header_row3.extend(["Sm", "SmU", "Fw", "FwU"])

    # Data columns (skip Year, Month from result for body)
    data_cols = [c for c in result.columns if c not in ("Year", "Month")]

    SEP = ";"
    CRLF = "\r\n"

    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
        f.write(SEP.join(header_row1) + CRLF)
        f.write(SEP.join(header_row2) + CRLF)
        f.write(SEP.join(header_row3) + CRLF)

        for _, row in result.iterrows():
            vals = [str(int(row["Year"])), str(int(row["Month"]))]
            for col in data_cols:
                v = row[col]
                if pd.isna(v):
                    vals.append("")
                else:
                    vals.append(f"{v:.6g}")
            f.write(SEP.join(vals) + CRLF)

    n_rows = len(result)
    n_cols = len(data_cols) + 2
    print(f"\n✅ CSV written: {OUTPUT_PATH}")
    print(f"   {n_rows} rows × {n_cols} columns")
    print(f"   Header: 3 rows (Region / Gate / Variable)")
    print(f"   Sm, SmU → kg/s  |  Fw, FwU → Sv")
    print(f"   Positive = flow into basin (Arctic side)")


if __name__ == "__main__":
    main()
