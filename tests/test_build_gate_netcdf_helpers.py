from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "scripts" / "build_gate_netcdf.py"
SPEC = importlib.util.spec_from_file_location("build_gate_netcdf", MOD_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules["build_gate_netcdf"] = mod
SPEC.loader.exec_module(mod)


def test_quadrature_mean():
    arr = np.array([[1.0, 2.0, np.nan], [3.0, 4.0, 5.0]])
    out = mod._quadrature_mean(arr, axis=0)
    assert np.allclose(out[:2], np.array([np.sqrt(5.0), np.sqrt(10.0)]))
    assert np.isclose(out[2], 5.0)


def test_maybe_reverse_profile_detects_reversed_endpoints():
    gate_lon = np.array([0.0, 1.0, 2.0])
    gate_lat = np.array([0.0, 0.0, 0.0])

    src_lon = np.array([2.0, 1.0, 0.0])
    src_lat = np.array([0.0, 0.0, 0.0])
    prof = np.array([[10.0, 20.0, 30.0], [40.0, 50.0, 60.0]])

    out_lon, out_lat, out_prof, reversed_flag = mod.maybe_reverse_profile(
        src_lon, src_lat, prof, gate_lon, gate_lat
    )

    assert reversed_flag is True
    assert np.allclose(out_lon, np.array([0.0, 1.0, 2.0]))
    assert np.allclose(out_lat, np.array([0.0, 0.0, 0.0]))
    assert np.allclose(out_prof, np.array([[30.0, 20.0, 10.0], [60.0, 50.0, 40.0]]))


def test_load_cci_monthly_profiles_uses_day1_day15_mean_and_quadrature(tmp_path: Path):
    times = pd.to_datetime(["2010-01-15", "2010-02-01", "2010-02-15"])
    gate_lon = np.array([0.0, 1.0, 2.0])
    gate_lat = np.array([0.0, 0.0, 0.0])

    sss = np.array(
        [
            [30.0, 31.0, 32.0],
            [34.0, 35.0, np.nan],
            [36.0, 37.0, 38.0],
        ],
        dtype=np.float64,
    )
    serr = np.array(
        [
            [0.5, 0.5, 0.5],
            [1.0, 2.0, np.nan],
            [3.0, 4.0, 5.0],
        ],
        dtype=np.float64,
    )

    ds = xr.Dataset(
        data_vars={
            "sss": (("time", "nb_prof"), sss),
            "sss_random_error": (("time", "nb_prof"), serr),
            "longitude": (("nb_prof",), gate_lon),
            "latitude": (("nb_prof",), gate_lat),
            "date": (("time",), times.values),
        }
    )

    f = tmp_path / "test_cci.nc"
    ds.to_netcdf(f)

    sss_monthly, err_monthly, _stats = mod.load_cci_monthly_profiles(f, gate_lon, gate_lat)

    jan = sss_monthly[(2010, 1)]
    feb = sss_monthly[(2010, 2)]
    feb_err = err_monthly[(2010, 2)]

    assert np.allclose(jan, np.array([30.0, 31.0, 32.0], dtype=np.float32), equal_nan=True)
    assert np.allclose(feb, np.array([35.0, 36.0, 38.0], dtype=np.float32), equal_nan=True)

    expected_err = np.array([np.sqrt(5.0), np.sqrt(10.0), 5.0], dtype=np.float32)
    assert np.allclose(feb_err, expected_err, atol=1e-6, equal_nan=True)


def test_interp_profile_no_extrapolation_when_insufficient_points():
    src_lon = np.array([0.0, 1.0, 2.0])
    src_lat = np.array([0.0, 0.0, 0.0])
    gate_lon = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    gate_lat = np.zeros_like(gate_lon)

    profile = np.array([np.nan, 10.0, np.nan])
    out = mod._interp_profile_to_gate(src_lon, src_lat, profile, gate_lon, gate_lat)
    assert np.isnan(out).all()


def test_point_slices_for_spatial_split_handles_dateline_jump():
    lon = np.array([170.0, 171.0, 172.0, -179.0, -178.0, -177.0, -176.0], dtype=float)
    slices = mod._point_slices_for_spatial_split(lon, chunk_points=3)
    pairs = [(s.start, s.stop) for s in slices]
    assert pairs == [(0, 3), (3, 6), (6, 7)]


def test_choose_cmems_mode(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_estimate_gate_points",
        lambda _info: (np.zeros(20), np.zeros(20), np.zeros(20), np.array([0.0, 0.0, 20.0, 10.0])),
    )
    assert mod._choose_cmems_mode({}) == "single_request"

    monkeypatch.setattr(
        mod,
        "_estimate_gate_points",
        lambda _info: (np.zeros(500), np.zeros(500), np.zeros(500), np.array([0.0, 0.0, 110.0, 10.0])),
    )
    assert mod._choose_cmems_mode({}) == "chunked"

    monkeypatch.setattr(
        mod,
        "_estimate_gate_points",
        lambda _info: (np.zeros(50), np.zeros(50), np.zeros(50), np.array([0.0, 0.0, 330.0, 10.0])),
    )
    assert mod._choose_cmems_mode({}) == "chunked"


def test_sanitize_lon_bbox_clamps_to_cmems_domain():
    lo, hi = mod._sanitize_lon_bbox(134.8, 181.9)
    assert lo >= mod.CMEMS_LON_MIN
    assert hi <= mod.CMEMS_LON_MAX
    assert lo < hi
