#!/usr/bin/env python3
"""
Build raw ARCFRESH gate NetCDF database (2002-2023).

Target contract (raw stack only):
- CMEMS L4 daily: ugos, vgos, err_ugosa, err_vgosa
- GEBCO: depth
- Gate geometry: longitude, latitude, x_km, dx
- Salinity:
    sss               (CCI SSS v5.5 monthly mean of day 1 + day 15, mapped to daily)
    sss_random_error  (CCI random error quadrature monthly mean, mapped to daily)
    psal_isas_surface (ISAS PSAL first layer climatology, mapped to daily by month)

NO theta, NO sign/orientation physics metadata, NO transport formulas.

Usage:
    source .venv/bin/activate
    python scripts/build_gate_netcdf.py
    python scripts/build_gate_netcdf.py fram_strait bering_strait --force
    python scripts/build_gate_netcdf.py ess_cao --split-time-files --split-years 1 --force
    python scripts/build_gate_netcdf.py ess_cao --output-dir "/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE" --split-time-files --split-years 1 --force
"""

from __future__ import annotations

import gc
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("build_nc")

# =============================================================================
# CONFIG
# =============================================================================
TIME_START = "2002-01-01"
TIME_END = "2023-12-31"
GEBCO_PATH = Path(
    "/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/"
    "GEBCO_06_Feb_2026_c91df93f54b8/gebco_2025_n90.0_s55.0_w0.0_e360.0.nc"
)
SALINITY_ROOT = Path("/Users/nicolocaron/Desktop/ARCFRESH/DATA SOURCES/straits")
SALINITY_NC_DIR = SALINITY_ROOT / "netcdf"
OUTPUT_DIR = PROJECT_ROOT / "data" / "netcdf"

# Chunk size for huge gates
CHUNK_YEARS = 4
SPATIAL_CHUNK_POINTS = 500
SPATIAL_SPLIT_POINTS_THRESHOLD = 3000
GLOBAL_LON_SPAN_THRESHOLD_DEG = 300.0

# Include adt/sla for CMEMSL4Service internals, even if not exported
CMEMS_VARIABLES = ["adt", "sla", "ugos", "vgos", "err_ugosa", "err_vgosa"]
CMEMS_DATASET_ID = "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D"
CMEMS_DATASET_VERSION = "202411"
CMEMS_LON_MIN = -179.9375
CMEMS_LON_MAX = 179.9375

# =============================================================================
# GATES
# =============================================================================
GATES = {
    # External boundaries
    "fram_strait": {
        "display": "Fram Strait",
        "shapefile": "gates/fram_strait_S3_pass_481.shp",
        "region": "Arctic Ocean (external boundaries)",
        "sss_cci": "fram_strait_S3_pass_481_SSS_CCIv5.5.nc",
        "isas_psal": "fram_strait_S3_pass_481_CLIM_ISAS_PSAL.nc",
    },
    "bering_strait": {
        "display": "Bering Strait",
        "shapefile": "gates/bering_strait_TPJ_pass_076.shp",
        "region": "Arctic Ocean (external boundaries)",
        "sss_cci": "bering_strait_TPJ_pass_076_SSS_CCIv5.5.nc",
        "isas_psal": "bering_strait_TPJ_pass_076_CLIM_ISAS_PSAL.nc",
    },
    "davis_strait": {
        "display": "Davis Strait",
        "shapefile": "gates/davis_strait.shp",
        "region": "Arctic Ocean (external boundaries)",
        "sss_cci": "davis_strait_SSS_CCIv5.5.nc",
        "isas_psal": "davis_strait_CLIM_ISAS_PSAL.nc",
    },
    "barents_opening": {
        "display": "Barents Sea Opening",
        "shapefile": "gates/barents_sea_opening_S3_pass_481.shp",
        "region": "Arctic Ocean (external boundaries)",
        "sss_cci": "barents_sea_opening_S3_pass_481_SSS_CCIv5.5.nc",
        "isas_psal": "barents_sea_opening_S3_pass_481_CLIM_ISAS_PSAL.nc",
    },
    "denmark_strait": {
        "display": "Denmark Strait",
        "shapefile": "gates/denmark_strait_TPJ_pass_246.shp",
        "region": "Arctic Ocean (external boundaries)",
        "sss_cci": "denmark_strait_TPJ_pass_246_SSS_CCIv5.5.nc",
        "isas_psal": "denmark_strait_TPJ_pass_246_CLIM_ISAS_PSAL.nc",
    },
    "norwegian_boundary": {
        "display": "Norwegian Sea Boundary",
        "shapefile": "gates/norwegian_sea_boundary_TPJ_pass_220.shp",
        "region": "Arctic Ocean (external boundaries)",
        "sss_cci": "norwegian_sea_boundary_TPJ_pass_220_SSS_CCIv5.5.nc",
        "isas_psal": "norwegian_sea_boundary_TPJ_pass_220_CLIM_ISAS_PSAL.nc",
    },
    "nares_strait": {
        "display": "Nares Strait",
        "shapefile": "gates/nares_strait.shp",
        "region": "Canadian Arctic Archipelago (CAA)",
        "sss_cci": "nares_strait_SSS_CCIv5.5.nc",
        "isas_psal": "nares_strait_CLIM_ISAS_PSAL.nc",
    },
    "lancaster_sound": {
        "display": "Lancaster Sound",
        "shapefile": "gates/lancaster_sound.shp",
        "region": "Canadian Arctic Archipelago (CAA)",
    },
    "jones_sound": {
        "display": "Jones Sound",
        "shapefile": "gates/jones_sound.shp",
        "region": "Canadian Arctic Archipelago (CAA)",
    },
    # Internal gates
    "barents_sea_cao": {
        "display": "Barents Sea - CAO",
        "shapefile": "gates/barents_sea-central_arctic_ocean.shp",
        "region": "Barents Sea",
    },
    "barents_sea_kara_sea": {
        "display": "Barents Sea - Kara Sea",
        "shapefile": "gates/barents_sea-kara_sea.shp",
        "region": "Barents Sea",
    },
    "kara_sea_cao": {
        "display": "Kara Sea - CAO",
        "shapefile": "gates/kara_sea-central_arctic_ocean.shp",
        "region": "Kara Sea",
    },
    "kara_sea_laptev_sea": {
        "display": "Kara Sea - Laptev Sea",
        "shapefile": "gates/kara_sea-laptev_sea.shp",
        "region": "Kara Sea",
    },
    "laptev_sea_cao": {
        "display": "Laptev Sea - CAO",
        "shapefile": "gates/laptev_sea-central_arctic_ocean.shp",
        "region": "Laptev Sea",
    },
    "laptev_sea_ess": {
        "display": "Laptev Sea - ESS",
        "shapefile": "gates/laptev_sea-east_siberian_seas.shp",
        "region": "Laptev Sea",
    },
    "ess_cao": {
        "display": "ESS - CAO",
        "shapefile": "gates/east_siberian_sea-central_arctic_ocean.shp",
        "region": "East Siberian Seas (ESS)",
    },
    "ess_beaufort_sea": {
        "display": "ESS - Beaufort Sea",
        "shapefile": "gates/east_siberian_sea-beaufort_sea.shp",
        "region": "East Siberian Seas (ESS)",
    },
    "beaufort_sea_cao": {
        "display": "Beaufort Sea - CAO",
        "shapefile": "gates/beaufort_sea-central_arctic_ocean.shp",
        "region": "Beaufort Sea",
    },
    "beaufort_sea_caa": {
        "display": "Beaufort Sea - CAA",
        "shapefile": "gates/beaufort_sea-canadian_arctic_archipelago.shp",
        "region": "Beaufort Sea",
    },
    "caa_cao": {
        "display": "CAA - CAO",
        "shapefile": "gates/canadian_arctic_archipelago-central_arctic_ocean.shp",
        "region": "Canadian Arctic Archipelago (CAA)",
    },
}


# =============================================================================
# GEOMETRY HELPERS
# =============================================================================
def compute_x_km(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Cumulative along-gate distance in km using lat-scaled planar approximation."""
    x_km = np.zeros(len(lon), dtype=np.float64)
    for i in range(1, len(lon)):
        dlat = (lat[i] - lat[i - 1]) * 111.0
        mean_lat = (lat[i] + lat[i - 1]) / 2.0
        dlon = (lon[i] - lon[i - 1]) * 111.0 * np.cos(np.radians(mean_lat))
        x_km[i] = x_km[i - 1] + np.hypot(dlat, dlon)
    return x_km


def compute_segment_widths(x_km: np.ndarray) -> np.ndarray:
    """Per-point segment widths in metres via central differences."""
    n = len(x_km)
    dx = np.zeros(n, dtype=np.float64)
    for i in range(n):
        if i == 0:
            dx[i] = (x_km[1] - x_km[0]) * 1000.0
        elif i == n - 1:
            dx[i] = (x_km[i] - x_km[i - 1]) * 1000.0
        else:
            dx[i] = (x_km[i + 1] - x_km[i - 1]) * 500.0
    return np.abs(dx)


def _endpoint_pair_cost(
    src_lon: np.ndarray,
    src_lat: np.ndarray,
    gate_lon: np.ndarray,
    gate_lat: np.ndarray,
    reverse_src: bool,
) -> float:
    """Compare endpoint alignment cost between salinity profile and canonical gate."""
    if reverse_src:
        s0_lon, s0_lat = src_lon[-1], src_lat[-1]
        s1_lon, s1_lat = src_lon[0], src_lat[0]
    else:
        s0_lon, s0_lat = src_lon[0], src_lat[0]
        s1_lon, s1_lat = src_lon[-1], src_lat[-1]

    g0_lon, g0_lat = gate_lon[0], gate_lat[0]
    g1_lon, g1_lat = gate_lon[-1], gate_lat[-1]

    mean_lat = np.radians((s0_lat + s1_lat + g0_lat + g1_lat) / 4.0)
    cos_lat = np.cos(mean_lat)

    def dkm(lon_a: float, lat_a: float, lon_b: float, lat_b: float) -> float:
        dx = (lon_b - lon_a) * 111.0 * cos_lat
        dy = (lat_b - lat_a) * 111.0
        return float(np.hypot(dx, dy))

    return dkm(s0_lon, s0_lat, g0_lon, g0_lat) + dkm(s1_lon, s1_lat, g1_lon, g1_lat)


def maybe_reverse_profile(
    src_lon: np.ndarray,
    src_lat: np.ndarray,
    profile_2d: np.ndarray,
    gate_lon: np.ndarray,
    gate_lat: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """
    Auto-orient source profiles to canonical gate direction using endpoint costs.

    profile_2d shape: (n_time_or_month, n_prof)
    """
    if len(src_lon) < 2 or len(gate_lon) < 2:
        return src_lon, src_lat, profile_2d, False

    keep_cost = _endpoint_pair_cost(src_lon, src_lat, gate_lon, gate_lat, reverse_src=False)
    rev_cost = _endpoint_pair_cost(src_lon, src_lat, gate_lon, gate_lat, reverse_src=True)

    if rev_cost + 1e-9 < keep_cost:
        return src_lon[::-1], src_lat[::-1], profile_2d[:, ::-1], True
    return src_lon, src_lat, profile_2d, False


def _interp_profile_to_gate(
    src_lon: np.ndarray,
    src_lat: np.ndarray,
    profile: np.ndarray,
    gate_lon: np.ndarray,
    gate_lat: np.ndarray,
) -> np.ndarray:
    """Linear interpolation along normalized gate distance, no extrapolation."""
    from scipy.interpolate import interp1d

    src_x = compute_x_km(src_lon, src_lat)
    gate_x = compute_x_km(gate_lon, gate_lat)

    if src_x[-1] <= 0:
        src_norm = np.linspace(0.0, 1.0, len(src_x))
    else:
        src_norm = src_x / src_x[-1]

    if gate_x[-1] <= 0:
        gate_norm = np.linspace(0.0, 1.0, len(gate_x))
    else:
        gate_norm = gate_x / gate_x[-1]

    valid = np.isfinite(profile)
    if np.count_nonzero(valid) < 2:
        return np.full(len(gate_lon), np.nan, dtype=np.float32)

    f = interp1d(
        src_norm[valid],
        profile[valid],
        kind="linear",
        bounds_error=False,
        fill_value=np.nan,
    )
    out = f(gate_norm)
    return out.astype(np.float32)


# =============================================================================
# SALINITY LOADERS
# =============================================================================
def _nanmean_2d(arr: np.ndarray, axis: int) -> np.ndarray:
    """NaN-mean that stays NaN on all-NaN slices."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        with np.errstate(invalid="ignore", divide="ignore"):
            out = np.nanmean(arr, axis=axis)
    return out


def _quadrature_mean(arr: np.ndarray, axis: int) -> np.ndarray:
    """sqrt(mean(sigma^2)) with NaN handling."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        with np.errstate(invalid="ignore", divide="ignore"):
            out = np.sqrt(np.nanmean(arr ** 2, axis=axis))
    return out


def load_cci_monthly_profiles(
    cci_file: Path,
    gate_lon: np.ndarray,
    gate_lat: np.ndarray,
) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], np.ndarray], dict]:
    """
    Load CCI SSS and return monthly profiles mapped to canonical gate grid.

    Output dicts keyed by (year, month):
    - sss_monthly[(y,m)] = (n_points,)
    - sss_err_monthly[(y,m)] = (n_points,)
    """
    ds = xr.open_dataset(cci_file)
    try:
        sss = ds["sss"].values.astype(np.float64)  # (time, nb_prof)
        sss_err = ds["sss_random_error"].values.astype(np.float64)
        dates = pd.to_datetime(ds["date"].values)
        lon = ds["longitude"].values.astype(np.float64)
        lat = ds["latitude"].values.astype(np.float64)
    finally:
        ds.close()

    lon, lat, sss, reversed_flag = maybe_reverse_profile(lon, lat, sss, gate_lon, gate_lat)
    _, _, sss_err, _ = maybe_reverse_profile(lon, lat, sss_err, gate_lon, gate_lat)

    # Build year-month groups (CCI has day 1 and day 15 per month)
    month_groups: dict[tuple[int, int], list[int]] = {}
    for idx, ts in enumerate(dates):
        key = (int(ts.year), int(ts.month))
        month_groups.setdefault(key, []).append(idx)

    sss_monthly: dict[tuple[int, int], np.ndarray] = {}
    err_monthly: dict[tuple[int, int], np.ndarray] = {}

    for key, idxs in month_groups.items():
        prof_mean = _nanmean_2d(sss[idxs, :], axis=0)
        err_quad = _quadrature_mean(sss_err[idxs, :], axis=0)

        sss_monthly[key] = _interp_profile_to_gate(lon, lat, prof_mean, gate_lon, gate_lat)
        err_monthly[key] = _interp_profile_to_gate(lon, lat, err_quad, gate_lon, gate_lat)

    stats = {
        "valid_pct_raw": float(np.isfinite(sss).sum() / sss.size * 100.0),
        "time_start": str(dates.min().date()),
        "time_end": str(dates.max().date()),
        "n_prof": int(len(lon)),
        "n_time": int(len(dates)),
        "reversed_to_match_gate": int(reversed_flag),
    }
    return sss_monthly, err_monthly, stats


def load_isas_surface_monthly_profiles(
    isas_file: Path,
    gate_lon: np.ndarray,
    gate_lat: np.ndarray,
) -> tuple[dict[int, np.ndarray], dict]:
    """
    Load ISAS PSAL and return monthly climatology profiles (surface layer only).

    Output dict keyed by month integer 1..12:
    - psal_surface_monthly[m] = (n_points,)
    """
    ds = xr.open_dataset(isas_file)
    try:
        psal = ds["PSAL"].values.astype(np.float64)  # (time, z, nb_prof)
        dates = pd.to_datetime(ds["date"].values)
        lon = ds["longitude"].values.astype(np.float64)
        lat = ds["latitude"].values.astype(np.float64)
        depth = ds["depth"].values.astype(np.float64)
    finally:
        ds.close()

    surface = psal[:, 0, :]  # first layer ~1m
    lon, lat, surface, reversed_flag = maybe_reverse_profile(lon, lat, surface, gate_lon, gate_lat)

    month_groups: dict[int, list[int]] = {}
    for idx, ts in enumerate(dates):
        month_groups.setdefault(int(ts.month), []).append(idx)

    psal_monthly: dict[int, np.ndarray] = {}
    for m, idxs in month_groups.items():
        prof = _nanmean_2d(surface[idxs, :], axis=0)
        psal_monthly[m] = _interp_profile_to_gate(lon, lat, prof, gate_lon, gate_lat)

    stats = {
        "valid_pct_surface_raw": float(np.isfinite(surface).sum() / surface.size * 100.0),
        "surface_depth_m": float(depth[0]),
        "n_prof": int(len(lon)),
        "n_time": int(len(dates)),
        "reversed_to_match_gate": int(reversed_flag),
    }
    return psal_monthly, stats


def expand_cci_to_daily(
    sss_monthly: dict[tuple[int, int], np.ndarray],
    err_monthly: dict[tuple[int, int], np.ndarray],
    daily_time: pd.DatetimeIndex,
    n_points: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Expand monthly CCI profiles to daily arrays on CMEMS time axis."""
    sss_daily = np.full((n_points, len(daily_time)), np.nan, dtype=np.float32)
    err_daily = np.full((n_points, len(daily_time)), np.nan, dtype=np.float32)

    by_month = pd.PeriodIndex(daily_time, freq="M")
    for period in by_month.unique():
        key = (period.year, period.month)
        if key not in sss_monthly:
            continue
        idx = np.where(by_month == period)[0]
        sss_daily[:, idx] = sss_monthly[key][:, None]
        err_daily[:, idx] = err_monthly[key][:, None]

    return sss_daily, err_daily


def expand_isas_surface_to_daily(
    psal_monthly: dict[int, np.ndarray],
    daily_time: pd.DatetimeIndex,
    n_points: int,
) -> np.ndarray:
    """Expand monthly climatological ISAS surface profiles to daily arrays."""
    out = np.full((n_points, len(daily_time)), np.nan, dtype=np.float32)
    months = daily_time.month
    for m in range(1, 13):
        if m not in psal_monthly:
            continue
        idx = np.where(months == m)[0]
        out[:, idx] = psal_monthly[m][:, None]
    return out


# =============================================================================
# CMEMS EXTRACTION
# =============================================================================
def _estimate_gate_points(gate_info: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build gate points once to estimate complexity and bbox."""
    from src.services.cmems_l4_service import (
        _build_gate_points,
        _compute_cmems_native_resolution_km,
        _compute_x_km,
        _load_gate_gdf,
    )

    shp_path = str(PROJECT_ROOT / gate_info["shapefile"])
    gate_gdf = _load_gate_gdf(shp_path)
    bounds = gate_gdf.total_bounds
    mean_lat = (bounds[1] + bounds[3]) / 2.0
    res_km = _compute_cmems_native_resolution_km(mean_lat)
    lon, lat = _build_gate_points(gate_gdf, n_pts=None, min_spacing_km=res_km)
    x_km = _compute_x_km(lon, lat)
    return lon, lat, x_km, bounds


def _time_ranges_by_year_chunks(chunk_years: int = CHUNK_YEARS) -> list[tuple[str, str]]:
    year_start = int(TIME_START[:4])
    year_end = int(TIME_END[:4])
    ranges: list[tuple[str, str]] = []
    y = year_start
    while y <= year_end:
        y2 = min(y + chunk_years - 1, year_end)
        ranges.append((f"{y}-01-01", f"{y2}-12-31"))
        y = y2 + 1
    return ranges


def _point_slices_for_spatial_split(gate_lon: np.ndarray, chunk_points: int) -> list[slice]:
    """
    Build contiguous point slices and split on dateline-like jumps.

    This prevents local slices from spanning ~360° in longitude.
    """
    n = len(gate_lon)
    if n == 0:
        return []

    jump_idx = np.where(np.abs(np.diff(gate_lon)) > 180.0)[0]
    boundaries = [0] + [int(i + 1) for i in jump_idx] + [n]

    slices: list[slice] = []
    for b0, b1 in zip(boundaries[:-1], boundaries[1:]):
        i = b0
        while i < b1:
            j = min(i + chunk_points, b1)
            slices.append(slice(i, j))
            i = j
    return slices


def _sanitize_lon_bbox(lon_min: float, lon_max: float) -> tuple[float, float]:
    """
    Clamp longitude bounds to CMEMS domain and prevent accidental wrap requests.

    Copernicus CMEMS L4 longitude domain is approximately [-179.9375, 179.9375].
    """
    lon_min_c = max(float(lon_min), CMEMS_LON_MIN)
    lon_max_c = min(float(lon_max), CMEMS_LON_MAX)
    if lon_min_c >= lon_max_c:
        mid = float(np.clip((lon_min_c + lon_max_c) * 0.5, CMEMS_LON_MIN + 0.25, CMEMS_LON_MAX - 0.25))
        lon_min_c = mid - 0.25
        lon_max_c = mid + 0.25
    return lon_min_c, lon_max_c


def _choose_cmems_mode(gate_info: dict) -> str:
    lon, _lat, _x, bounds = _estimate_gate_points(gate_info)
    lon_span = float(bounds[2] - bounds[0] + 4.0)
    n_pts = int(len(lon))

    if lon_span > 100.0 or n_pts > 2000:
        mode = "chunked"
    else:
        mode = "single_request"

    logger.info("  Gate complexity check: %d pts, lon_span=%.1f° -> %s", n_pts, lon_span, mode)
    return mode


def fetch_cmems_single(gate_info: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DatetimeIndex]:
    """
    Fetch CMEMS with direct subset extraction (API-only, no cache dependency).

    This avoids extra DOT/slope processing in load_gate_data and is faster for
    raw-stack export.
    """
    from scipy.spatial import cKDTree

    from src.services.cmems_l4_service import (
        CMEMSL4Service,
        _build_gate_points,
        _compute_cmems_native_resolution_km,
        _compute_x_km,
        _load_gate_gdf,
    )

    shp_path = str(PROJECT_ROOT / gate_info["shapefile"])
    gate_gdf = _load_gate_gdf(shp_path)
    bounds = gate_gdf.total_bounds
    mean_lat = (bounds[1] + bounds[3]) / 2.0
    res_km = _compute_cmems_native_resolution_km(mean_lat)
    gate_lon, gate_lat = _build_gate_points(gate_gdf, n_pts=None, min_spacing_km=res_km)
    x_km = _compute_x_km(gate_lon, gate_lat).astype(np.float64)
    dx = compute_segment_widths(x_km).astype(np.float32)

    lon_min, lon_max = _sanitize_lon_bbox(bounds[0] - 2.0, bounds[2] + 2.0)
    lat_min = bounds[1] - 2.0
    lat_max = bounds[3] + 2.0

    service = CMEMSL4Service()
    ds = service._download_subset(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
        time_start=TIME_START,
        time_end=TIME_END,
        variables=CMEMS_VARIABLES,
        dataset_id=CMEMS_DATASET_ID,
        dataset_version=CMEMS_DATASET_VERSION,
        disable_progress_bar=False,
    )
    if ds is None:
        raise RuntimeError("CMEMS single-request subset returned None")

    lons = ds["longitude"].values if "longitude" in ds.coords else ds["lon"].values
    lats = ds["latitude"].values if "latitude" in ds.coords else ds["lat"].values
    time_pd = pd.to_datetime(ds["time"].values)

    lon2d, lat2d = np.meshgrid(lons, lats)
    tree = cKDTree(np.column_stack([lon2d.ravel(), lat2d.ravel()]))
    _, idx_flat = tree.query(np.column_stack([gate_lon, gate_lat]), k=1)
    lat_idx = idx_flat // len(lons)
    lon_idx = idx_flat % len(lons)

    n_pts = len(gate_lon)
    n_t = len(time_pd)

    def extract(var_name: str) -> np.ndarray:
        if var_name not in ds.data_vars:
            return np.full((n_pts, n_t), np.nan, dtype=np.float32)
        var = ds[var_name]
        lat_dim = "latitude" if "latitude" in var.dims else "lat"
        lon_dim = "longitude" if "longitude" in var.dims else "lon"
        out = var.isel(
            {lat_dim: xr.DataArray(lat_idx, dims="point"), lon_dim: xr.DataArray(lon_idx, dims="point")}
        ).transpose("point", "time")
        return out.values.astype(np.float32)

    ugos = extract("ugos")
    vgos = extract("vgos")
    err_u = extract("err_ugosa")
    err_v = extract("err_vgosa")

    ds.close()
    del ds
    gc.collect()

    return ugos, vgos, err_u, err_v, gate_lon.astype(np.float64), gate_lat.astype(np.float64), dx, time_pd


def fetch_cmems_chunked(
    gate_info: dict,
    chunk_years: int = CHUNK_YEARS,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DatetimeIndex]:
    """Fetch CMEMS by year chunks for very large gates (API-only)."""
    from scipy.spatial import cKDTree

    from src.services.cmems_l4_service import (
        CMEMSL4Service,
        _build_gate_points,
        _compute_cmems_native_resolution_km,
        _compute_x_km,
        _load_gate_gdf,
    )

    shp_path = str(PROJECT_ROOT / gate_info["shapefile"])
    gate_gdf = _load_gate_gdf(shp_path)
    bounds = gate_gdf.total_bounds
    mean_lat = (bounds[1] + bounds[3]) / 2.0
    res_km = _compute_cmems_native_resolution_km(mean_lat)
    gate_lon, gate_lat = _build_gate_points(gate_gdf, n_pts=None, min_spacing_km=res_km)
    x_km = _compute_x_km(gate_lon, gate_lat).astype(np.float64)
    dx = compute_segment_widths(x_km).astype(np.float32)

    lon_min, lon_max = _sanitize_lon_bbox(bounds[0] - 2.0, bounds[2] + 2.0)
    lat_min = bounds[1] - 2.0
    lat_max = bounds[3] + 2.0

    service = CMEMSL4Service()

    ranges = _time_ranges_by_year_chunks(chunk_years=chunk_years)

    ugos_chunks: list[np.ndarray] = []
    vgos_chunks: list[np.ndarray] = []
    erru_chunks: list[np.ndarray] = []
    errv_chunks: list[np.ndarray] = []
    time_chunks: list[pd.DatetimeIndex] = []

    lat_idx = None
    lon_idx = None

    for ci, (t_start, t_end) in enumerate(ranges, start=1):
        logger.info("  CMEMS chunk %d/%d: %s -> %s", ci, len(ranges), t_start, t_end)
        ds = service._download_subset(
            lon_min=lon_min,
            lon_max=lon_max,
            lat_min=lat_min,
            lat_max=lat_max,
            time_start=t_start,
            time_end=t_end,
            variables=CMEMS_VARIABLES,
            dataset_id=CMEMS_DATASET_ID,
            dataset_version=CMEMS_DATASET_VERSION,
            disable_progress_bar=False,
        )

        if ds is None:
            raise RuntimeError(f"CMEMS chunk returned None: {t_start} -> {t_end}")

        lons = ds["longitude"].values if "longitude" in ds.coords else ds["lon"].values
        lats = ds["latitude"].values if "latitude" in ds.coords else ds["lat"].values
        times = pd.to_datetime(ds["time"].values)

        if lat_idx is None or lon_idx is None:
            lon2d, lat2d = np.meshgrid(lons, lats)
            tree = cKDTree(np.column_stack([lon2d.ravel(), lat2d.ravel()]))
            _, idx_flat = tree.query(np.column_stack([gate_lon, gate_lat]), k=1)
            lat_idx = idx_flat // len(lons)
            lon_idx = idx_flat % len(lons)

        n_pts = len(gate_lon)
        n_t = len(times)

        def extract(var_name: str) -> np.ndarray:
            if var_name not in ds.data_vars:
                return np.full((n_pts, n_t), np.nan, dtype=np.float32)
            var = ds[var_name]
            lat_dim = "latitude" if "latitude" in var.dims else "lat"
            lon_dim = "longitude" if "longitude" in var.dims else "lon"
            out = var.isel(
                {lat_dim: xr.DataArray(lat_idx, dims="point"), lon_dim: xr.DataArray(lon_idx, dims="point")}
            ).transpose("point", "time")
            return out.values.astype(np.float32)

        ugos_chunks.append(extract("ugos"))
        vgos_chunks.append(extract("vgos"))
        erru_chunks.append(extract("err_ugosa"))
        errv_chunks.append(extract("err_vgosa"))
        time_chunks.append(times)

        ds.close()
        del ds
        gc.collect()

    ugos = np.concatenate(ugos_chunks, axis=1)
    vgos = np.concatenate(vgos_chunks, axis=1)
    err_u = np.concatenate(erru_chunks, axis=1)
    err_v = np.concatenate(errv_chunks, axis=1)
    time_pd = pd.to_datetime(np.concatenate([t.values for t in time_chunks]))

    return ugos, vgos, err_u, err_v, gate_lon, gate_lat, dx, time_pd


def fetch_cmems_spatial_split(gate_info: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, pd.DatetimeIndex]:
    """Fetch CMEMS by spatial and temporal chunks for near-global/very large gates."""
    from scipy.spatial import cKDTree

    from src.services.cmems_l4_service import (
        CMEMSL4Service,
        _build_gate_points,
        _compute_cmems_native_resolution_km,
        _compute_x_km,
        _load_gate_gdf,
    )

    shp_path = str(PROJECT_ROOT / gate_info["shapefile"])
    gate_gdf = _load_gate_gdf(shp_path)
    bounds = gate_gdf.total_bounds
    mean_lat = (bounds[1] + bounds[3]) / 2.0
    res_km = _compute_cmems_native_resolution_km(mean_lat)
    gate_lon, gate_lat = _build_gate_points(gate_gdf, n_pts=None, min_spacing_km=res_km)
    x_km = _compute_x_km(gate_lon, gate_lat).astype(np.float64)
    dx = compute_segment_widths(x_km).astype(np.float32)

    full_time = pd.date_range(TIME_START, TIME_END, freq="D")
    full_time_np = full_time.values.astype("datetime64[ns]")
    n_pts = len(gate_lon)
    n_t = len(full_time)

    ugos = np.full((n_pts, n_t), np.nan, dtype=np.float32)
    vgos = np.full((n_pts, n_t), np.nan, dtype=np.float32)
    err_u = np.full((n_pts, n_t), np.nan, dtype=np.float32)
    err_v = np.full((n_pts, n_t), np.nan, dtype=np.float32)

    service = CMEMSL4Service()
    time_ranges = _time_ranges_by_year_chunks()
    point_slices = _point_slices_for_spatial_split(gate_lon, SPATIAL_CHUNK_POINTS)

    logger.info(
        "  Spatial split mode: %d point-chunks (size<=%d), %d time-chunks (%dy)",
        len(point_slices),
        SPATIAL_CHUNK_POINTS,
        len(time_ranges),
        CHUNK_YEARS,
    )

    for si, sl in enumerate(point_slices, start=1):
        sub_lon = gate_lon[sl]
        sub_lat = gate_lat[sl]
        lon_min, lon_max = _sanitize_lon_bbox(np.min(sub_lon) - 2.0, np.max(sub_lon) + 2.0)
        lat_min = float(np.min(sub_lat) - 2.0)
        lat_max = float(np.max(sub_lat) + 2.0)

        logger.info(
            "  Spatial chunk %d/%d: points[%d:%d] bbox=[%.2f, %.2f]x[%.2f, %.2f]",
            si,
            len(point_slices),
            sl.start,
            sl.stop,
            lon_min,
            lon_max,
            lat_min,
            lat_max,
        )

        for ti, (t_start, t_end) in enumerate(time_ranges, start=1):
            logger.info(
                "    Time chunk %d/%d: %s -> %s",
                ti,
                len(time_ranges),
                t_start,
                t_end,
            )
            ds = service._download_subset(
                lon_min=lon_min,
                lon_max=lon_max,
                lat_min=lat_min,
                lat_max=lat_max,
                time_start=t_start,
                time_end=t_end,
                variables=CMEMS_VARIABLES,
                dataset_id=CMEMS_DATASET_ID,
                dataset_version=CMEMS_DATASET_VERSION,
                disable_progress_bar=False,
            )

            if ds is None:
                raise RuntimeError(
                    f"CMEMS spatial split chunk returned None: "
                    f"spatial={si}/{len(point_slices)} time={t_start}->{t_end}"
                )

            lons = ds["longitude"].values if "longitude" in ds.coords else ds["lon"].values
            lats = ds["latitude"].values if "latitude" in ds.coords else ds["lat"].values
            times = pd.to_datetime(ds["time"].values)
            times_np = times.values.astype("datetime64[ns]")
            tidx = np.searchsorted(full_time_np, times_np)

            if np.any(tidx >= n_t) or np.any(full_time_np[tidx] != times_np):
                ds.close()
                raise RuntimeError(
                    f"Unexpected CMEMS time alignment for chunk {t_start}->{t_end}"
                )

            lon2d, lat2d = np.meshgrid(lons, lats)
            tree = cKDTree(np.column_stack([lon2d.ravel(), lat2d.ravel()]))
            _, idx_flat = tree.query(np.column_stack([sub_lon, sub_lat]), k=1)
            lat_idx = idx_flat // len(lons)
            lon_idx = idx_flat % len(lons)
            n_sub = len(sub_lon)

            def extract(var_name: str) -> np.ndarray:
                if var_name not in ds.data_vars:
                    return np.full((n_sub, len(times)), np.nan, dtype=np.float32)
                arr = ds[var_name].values
                if ds[var_name].dims[0] == "time":
                    return arr[:, lat_idx, lon_idx].T.astype(np.float32)
                return arr[lat_idx, lon_idx, :].T.astype(np.float32)

            ugos[sl, tidx] = extract("ugos")
            vgos[sl, tidx] = extract("vgos")
            err_u[sl, tidx] = extract("err_ugosa")
            err_v[sl, tidx] = extract("err_vgosa")

            ds.close()
            del ds
            gc.collect()

    return ugos, vgos, err_u, err_v, gate_lon.astype(np.float64), gate_lat.astype(np.float64), dx, full_time


# =============================================================================
# BUILD
# =============================================================================
def build_gate_netcdf(gate_id: str, gate_info: dict) -> bool:
    """Build one gate NetCDF according to raw-stack contract."""
    t0 = time.time()
    display_name = gate_info["display"]
    logger.info("=" * 72)
    logger.info("🚀 %s [%s]", display_name.upper(), gate_id)
    logger.info("=" * 72)

    shp_path = PROJECT_ROOT / gate_info["shapefile"]
    if not shp_path.exists():
        logger.error("❌ Missing shapefile: %s", shp_path)
        return False

    # 1) CMEMS
    logger.info("📡 Loading CMEMS L4 (API-only, no fallback)...")
    cmems_mode = _choose_cmems_mode(gate_info)
    if cmems_mode == "chunked":
        lon_est, _lat_est, _x_est, bounds_est = _estimate_gate_points(gate_info)
        lon_span_est = float(bounds_est[2] - bounds_est[0] + 4.0)
        n_pts_est = int(len(lon_est))
        chunk_years = 1 if (lon_span_est >= GLOBAL_LON_SPAN_THRESHOLD_DEG or n_pts_est >= SPATIAL_SPLIT_POINTS_THRESHOLD) else CHUNK_YEARS
        ugos, vgos, err_u, err_v, gate_lon, gate_lat, dx, time_pd = fetch_cmems_chunked(
            gate_info,
            chunk_years=chunk_years,
        )
        cmems_mode = f"chunked_{chunk_years}y"
    else:
        ugos, vgos, err_u, err_v, gate_lon, gate_lat, dx, time_pd = fetch_cmems_single(gate_info)
        cmems_mode = "single_request"

    n_pts, n_time = ugos.shape
    x_km = compute_x_km(gate_lon, gate_lat).astype(np.float64)
    logger.info(
        "  CMEMS shape: %d pts x %d days (%s -> %s)",
        n_pts,
        n_time,
        time_pd.min().date(),
        time_pd.max().date(),
    )

    # 2) Bathymetry
    logger.info("🌊 Loading GEBCO depth...")
    from src.services.gebco_service import get_bathymetry_cache

    bathy_cache = get_bathymetry_cache()
    depth = bathy_cache.get_or_compute(
        gate_name=display_name,
        gate_lons=gate_lon,
        gate_lats=gate_lat,
        gebco_path=str(GEBCO_PATH),
        depth_cap=None,
    ).astype(np.float32)

    # 3) Salinity placeholders (always present in output)
    sss_daily = np.full((n_pts, n_time), np.nan, dtype=np.float32)
    sss_err_daily = np.full((n_pts, n_time), np.nan, dtype=np.float32)
    psal_surface_daily = np.full((n_pts, n_time), np.nan, dtype=np.float32)

    has_cci = 0
    has_isas = 0
    cci_stats = {}
    isas_stats = {}

    # 4) CCI
    cci_name = gate_info.get("sss_cci")
    if cci_name:
        cci_path = SALINITY_NC_DIR / cci_name
        if cci_path.exists():
            logger.info("🧂 Loading CCI SSS: %s", cci_name)
            cci_monthly, cci_err_monthly, cci_stats = load_cci_monthly_profiles(
                cci_path,
                gate_lon,
                gate_lat,
            )
            sss_daily, sss_err_daily = expand_cci_to_daily(
                cci_monthly,
                cci_err_monthly,
                time_pd,
                n_pts,
            )
            if np.isfinite(sss_daily).any():
                has_cci = 1
        else:
            logger.warning("  CCI file missing: %s", cci_path)

    # 5) ISAS surface
    isas_name = gate_info.get("isas_psal")
    if isas_name:
        isas_path = SALINITY_NC_DIR / isas_name
        if isas_path.exists():
            logger.info("🧂 Loading ISAS PSAL surface: %s", isas_name)
            isas_monthly, isas_stats = load_isas_surface_monthly_profiles(
                isas_path,
                gate_lon,
                gate_lat,
            )
            psal_surface_daily = expand_isas_surface_to_daily(isas_monthly, time_pd, n_pts)
            if np.isfinite(psal_surface_daily).any():
                has_isas = 1
        else:
            logger.warning("  ISAS file missing: %s", isas_path)

    logger.info(
        "  Salinity coverage -> CCI: %.1f%% | ISAS surface: %.1f%%",
        float(np.isfinite(sss_daily).sum() / sss_daily.size * 100.0),
        float(np.isfinite(psal_surface_daily).sum() / psal_surface_daily.size * 100.0),
    )

    # 6) Dataset
    ds = xr.Dataset(
        data_vars={
            "ugos": (
                ["point", "time"],
                ugos,
                {
                    "units": "m/s",
                    "long_name": "Eastward geostrophic velocity",
                    "source": "CMEMS L4 SEALEVEL_GLO_PHY_L4_MY_008_047",
                },
            ),
            "vgos": (
                ["point", "time"],
                vgos,
                {
                    "units": "m/s",
                    "long_name": "Northward geostrophic velocity",
                    "source": "CMEMS L4 SEALEVEL_GLO_PHY_L4_MY_008_047",
                },
            ),
            "err_ugosa": (
                ["point", "time"],
                err_u,
                {
                    "units": "m/s",
                    "long_name": "Formal mapping error on eastward geostrophic velocity",
                    "source": "CMEMS L4",
                },
            ),
            "err_vgosa": (
                ["point", "time"],
                err_v,
                {
                    "units": "m/s",
                    "long_name": "Formal mapping error on northward geostrophic velocity",
                    "source": "CMEMS L4",
                },
            ),
            "depth": (
                ["point"],
                depth,
                {
                    "units": "m",
                    "long_name": "Ocean depth (positive down, uncapped)",
                    "source": "GEBCO 2025",
                },
            ),
            "dx": (
                ["point"],
                dx.astype(np.float32),
                {
                    "units": "m",
                    "long_name": "Segment width along canonical gate",
                    "method": "central differences on x_km",
                },
            ),
            "sss": (
                ["point", "time"],
                sss_daily,
                {
                    "units": "PSU",
                    "long_name": "Sea surface salinity from CCI v5.5",
                    "source": "ESA CCI SSS v5.5; monthly(day1+day15 nanmean) remapped to daily CMEMS timeline",
                },
            ),
            "sss_random_error": (
                ["point", "time"],
                sss_err_daily,
                {
                    "units": "PSU",
                    "long_name": "Random error on sea surface salinity",
                    "source": "ESA CCI SSS v5.5 sss_random_error; monthly quadrature mean remapped to daily timeline",
                },
            ),
            "psal_isas_surface": (
                ["point", "time"],
                psal_surface_daily,
                {
                    "units": "PSU",
                    "long_name": "Surface practical salinity from ISAS climatology",
                    "source": "ISAS CLIM PSAL first depth layer (z0) remapped to daily CMEMS timeline by month",
                },
            ),
        },
        coords={
            "time": ("time", pd.to_datetime(time_pd).values),
            "longitude": ("point", gate_lon.astype(np.float64)),
            "latitude": ("point", gate_lat.astype(np.float64)),
            "x_km": ("point", x_km.astype(np.float64)),
        },
        attrs={
            "title": f"ARCFRESH Gate Raw Data Stack - {display_name}",
            "gate_id": gate_id,
            "gate_display_name": display_name,
            "region": gate_info["region"],
            "shapefile": gate_info["shapefile"],
            "time_start": str(time_pd.min().date()),
            "time_end": str(time_pd.max().date()),
            "n_points": int(n_pts),
            "n_timesteps": int(n_time),
            "gate_length_km": float(x_km[-1]),
            "processing_mode": cmems_mode,
            "raw_stack_only": 1,
            "has_cci": int(has_cci),
            "has_isas": int(has_isas),
            "velocity_source": "CMEMS L4 SEALEVEL_GLO_PHY_L4_MY_008_047 (daily, 0.125 deg)",
            "bathymetry_source": "GEBCO 2025 (15 arc-second)",
            "salinity_cci_source": gate_info.get("sss_cci", "N/A"),
            "salinity_isas_source": gate_info.get("isas_psal", "N/A"),
            "salinity_root_path": str(SALINITY_ROOT),
            "remap_method": "linear interpolation along normalized gate distance in km, no extrapolation",
            "created": datetime.now().isoformat(),
            "created_by": "scripts/build_gate_netcdf.py",
        },
    )

    # Keep brief salinity diagnostics in attrs
    if cci_stats:
        ds.attrs["cci_time_start"] = cci_stats.get("time_start", "")
        ds.attrs["cci_time_end"] = cci_stats.get("time_end", "")
        ds.attrs["cci_raw_valid_pct"] = float(cci_stats.get("valid_pct_raw", np.nan))
    if isas_stats:
        ds.attrs["isas_surface_depth_m"] = float(isas_stats.get("surface_depth_m", np.nan))
        ds.attrs["isas_surface_raw_valid_pct"] = float(isas_stats.get("valid_pct_surface_raw", np.nan))

    out_path = OUTPUT_DIR / f"arcfresh_{gate_id}_{TIME_START[:4]}-{TIME_END[:4]}.nc"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")

    encoding = {
        var: {"zlib": True, "complevel": 4}
        for var in ds.data_vars
    }

    if tmp_path.exists():
        tmp_path.unlink()
    ds.to_netcdf(tmp_path, mode="w", encoding=encoding)
    tmp_path.replace(out_path)
    size_mb = out_path.stat().st_size / 1e6
    logger.info(
        "✅ %s -> %s (%.1f MB) in %.1fs",
        display_name,
        out_path.name,
        size_mb,
        time.time() - t0,
    )

    ds.close()
    del ds
    gc.collect()
    return True


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    global TIME_START, TIME_END, OUTPUT_DIR
    total_t0 = time.time()
    args = sys.argv[1:]
    force = False
    split_time_files = False
    split_years = 1
    output_dir_override: Path | None = None
    requested: list[str] = []

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--force":
            force = True
        elif a == "--split-time-files":
            split_time_files = True
        elif a.startswith("--split-years="):
            split_years = int(a.split("=", 1)[1])
        elif a == "--split-years":
            if i + 1 >= len(args):
                logger.error("--split-years requires an integer value")
                sys.exit(2)
            split_years = int(args[i + 1])
            i += 1
        elif a.startswith("--output-dir="):
            output_dir_override = Path(a.split("=", 1)[1]).expanduser()
        elif a == "--output-dir":
            if i + 1 >= len(args):
                logger.error("--output-dir requires a path value")
                sys.exit(2)
            output_dir_override = Path(args[i + 1]).expanduser()
            i += 1
        elif a.startswith("--"):
            logger.warning("Unknown option ignored: %s", a)
        else:
            requested.append(a)
        i += 1

    if split_years < 1:
        logger.error("--split-years must be >= 1")
        sys.exit(2)

    if output_dir_override is not None:
        OUTPUT_DIR = output_dir_override

    if requested:
        gates_to_run = {}
        for gate_id in requested:
            if gate_id in GATES:
                gates_to_run[gate_id] = GATES[gate_id]
            else:
                logger.warning("⚠️ Unknown gate: %s", gate_id)
        if not gates_to_run:
            logger.error("No valid gates requested.")
            sys.exit(1)
    else:
        gates_to_run = GATES

    logger.info("=" * 72)
    logger.info("📦 ARCFRESH RAW NETCDF BUILDER")
    logger.info("   Time: %s -> %s", TIME_START, TIME_END)
    logger.info("   Gates: %d", len(gates_to_run))
    logger.info("   Output dir: %s", OUTPUT_DIR)
    logger.info("   Salinity dir: %s", SALINITY_NC_DIR)
    logger.info("   Split time files: %s (years per file: %d)", int(split_time_files), split_years)
    logger.info("=" * 72)

    results: dict[str, str] = {}

    for gate_id, gate_info in gates_to_run.items():
        if split_time_files:
            base_start = TIME_START
            base_end = TIME_END
            y0 = int(base_start[:4])
            y1 = int(base_end[:4])
            periods: list[tuple[str, str]] = []
            y = y0
            while y <= y1:
                y2 = min(y + split_years - 1, y1)
                periods.append((f"{y}-01-01", f"{y2}-12-31"))
                y = y2 + 1

            ok_chunks = 0
            skipped_chunks = 0
            failed_chunks = 0
            try:
                for p_start, p_end in periods:
                    TIME_START = p_start
                    TIME_END = p_end
                    out_path = OUTPUT_DIR / f"arcfresh_{gate_id}_{TIME_START[:4]}-{TIME_END[:4]}.nc"
                    if out_path.exists() and not force:
                        logger.info("⏭️  %s exists, skipping (use --force)", out_path.name)
                        skipped_chunks += 1
                        continue

                    try:
                        ok = build_gate_netcdf(gate_id, gate_info)
                        if ok:
                            ok_chunks += 1
                        else:
                            failed_chunks += 1
                    except Exception as exc:
                        logger.error("❌ %s failed for %s..%s: %s", gate_id, p_start, p_end, exc)
                        traceback.print_exc()
                        failed_chunks += 1
                    gc.collect()
            finally:
                TIME_START = base_start
                TIME_END = base_end

            if failed_chunks == 0 and ok_chunks > 0:
                results[gate_id] = f"OK_SPLIT ({ok_chunks}/{len(periods)} chunks)"
            elif failed_chunks == 0 and skipped_chunks == len(periods):
                results[gate_id] = "SKIPPED_EXISTS"
            else:
                results[gate_id] = f"FAILED_SPLIT (ok={ok_chunks}, failed={failed_chunks}, skipped={skipped_chunks})"
        else:
            out_path = OUTPUT_DIR / f"arcfresh_{gate_id}_{TIME_START[:4]}-{TIME_END[:4]}.nc"
            if out_path.exists() and not force:
                logger.info("⏭️  %s exists, skipping (use --force)", out_path.name)
                results[gate_id] = "SKIPPED_EXISTS"
                continue

            try:
                ok = build_gate_netcdf(gate_id, gate_info)
                results[gate_id] = "OK" if ok else "FAILED"
            except Exception as exc:
                logger.error("❌ %s failed: %s", gate_id, exc)
                traceback.print_exc()
                results[gate_id] = f"CRASH: {exc}"
        gc.collect()

    logger.info("")
    logger.info("=" * 72)
    logger.info("📊 SUMMARY")
    logger.info("=" * 72)
    ok_count = 0
    for gid, status in results.items():
        if status.startswith("OK"):
            ok_count += 1
        logger.info("  %-24s %s", gid, status)

    if OUTPUT_DIR.exists():
        total_size = sum(f.stat().st_size for f in OUTPUT_DIR.glob("arcfresh_*.nc"))
        logger.info("  Total output size: %.1f MB", total_size / 1e6)

    logger.info("  OK: %d/%d", ok_count, len(results))
    logger.info("  Total time: %.1fs", time.time() - total_t0)
    logger.info("=" * 72)


if __name__ == "__main__":
    main()
