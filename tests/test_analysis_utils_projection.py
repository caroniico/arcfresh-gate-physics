from __future__ import annotations

import numpy as np
import xarray as xr

from analysis import utils


def _base_ds(
    lon: np.ndarray,
    lat: np.ndarray,
    ugos_val: float = 1.0,
    vgos_val: float = 2.0,
) -> xr.Dataset:
    n_pts = len(lon)
    n_time = 3
    ugos = np.full((n_pts, n_time), ugos_val, dtype=float)
    vgos = np.full((n_pts, n_time), vgos_val, dtype=float)
    eu = np.full((n_pts, n_time), 0.1, dtype=float)
    ev = np.full((n_pts, n_time), 0.2, dtype=float)

    return xr.Dataset(
        data_vars={
            "ugos": (("point", "time"), ugos),
            "vgos": (("point", "time"), vgos),
            "err_ugosa": (("point", "time"), eu),
            "err_vgosa": (("point", "time"), ev),
            "depth": (("point",), np.full(n_pts, 100.0)),
            "dx": (("point",), np.full(n_pts, 1000.0)),
            "sss": (("point", "time"), np.full((n_pts, n_time), 34.0)),
            "longitude": (("point",), lon.astype(float)),
            "latitude": (("point",), lat.astype(float)),
        },
        coords={
            "time": (("time",), np.array(["2002-01-01", "2002-01-02", "2002-01-03"], dtype="datetime64[ns]")),
        },
    )


def test_local_normals_are_unit_and_arctic_oriented():
    lon = np.array([170.0, 171.0, 172.0, -179.0, -178.0, -177.0], dtype=float)
    lat = np.array([75.0, 75.1, 75.2, 75.3, 75.4, 75.5], dtype=float)
    ds = _base_ds(lon, lat)

    u_loc, v_loc = utils.local_into_arctic_unit_vectors(ds)
    norms = np.hypot(u_loc, v_loc)
    assert np.allclose(norms, 1.0, atol=1e-7)

    ax, ay = utils._to_arctic_unit_vectors(lon, lat)  # noqa: SLF001 (module-level helper test)
    dot = u_loc * ax + v_loc * ay
    assert np.all(dot >= -1e-10)


def test_perpendicular_velocity_uses_local_projection_not_explicit_vector():
    # Purely zonal gate (W->E): local normal should be northward.
    lon = np.array([-10.0, -5.0, 0.0, 5.0, 10.0], dtype=float)
    lat = np.array([70.0, 70.0, 70.0, 70.0, 70.0], dtype=float)
    ds = _base_ds(lon, lat, ugos_val=3.0, vgos_val=4.0)

    out = utils.perpendicular_velocity(ds, u_into=1.0, v_into=0.0)
    # Explicit vector must be ignored in the new workflow.
    assert np.allclose(out, ds["vgos"].values, atol=1e-10)


def test_perpendicular_velocity_uncertainty_uses_local_projection():
    lon = np.array([-10.0, -5.0, 0.0, 5.0, 10.0], dtype=float)
    lat = np.array([70.0, 70.0, 70.0, 70.0, 70.0], dtype=float)
    ds = _base_ds(lon, lat)

    sigma = utils.perpendicular_velocity_uncertainty(ds)
    assert np.all(sigma >= 0.0)
    assert np.allclose(sigma, ds["err_vgosa"].values, atol=1e-10)


def test_local_normals_no_sign_flips_on_smooth_gate():
    lon = np.linspace(-60.0, -20.0, 40)
    lat = 65.0 + 2.0 * np.sin(np.linspace(0.0, np.pi / 6.0, 40))
    ds = _base_ds(lon, lat)

    u_loc, v_loc = utils.local_into_arctic_unit_vectors(ds)
    dots = u_loc[1:] * u_loc[:-1] + v_loc[1:] * v_loc[:-1]
    assert np.all(dots > 0.0)
