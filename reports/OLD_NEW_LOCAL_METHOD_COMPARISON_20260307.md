# Old vs New Gate NetCDF Comparison (Local Per-Point Method)

- Generated: 2026-03-07
- Period: 2002-01-01 to 2023-12-31
- Method: same **new local per-point projection** on both old and new files
- Gates: Fram Strait, Davis Strait

## fram_strait
- Common timesteps: 8035

| metric | old_mean | new_mean | old_std | new_std | bias_abs | delta_pct_vs_old | valid_n |
|---|---:|---:|---:|---:|---:|---:|---:|
| VT [Sv] | -1.69575 | -1.69575 | 0.805905 | 0.805905 | 0 | 0 | 8035 |
| FW [m3/s] | -9540.68 | -9540.68 | 34487.4 | 34487.4 | 0 | 0 | 5113 |
| Salt [kg/s] | 4.32015e+07 | 4.32015e+07 | 3.02572e+07 | 3.02572e+07 | 0 | 0 | 5113 |
| SSS [PSU] | 34.6086 | 34.6086 | 0.93568 | 0.93568 | 0 | 0 | 503250 |
| SSS coverage [%] | 22.6109 | 22.6109 | nan | nan | 0 | 0 | 2225695 |

## davis_strait
- Common timesteps: 8035

| metric | old_mean | new_mean | old_std | new_std | bias_abs | delta_pct_vs_old | valid_n |
|---|---:|---:|---:|---:|---:|---:|---:|
| VT [Sv] | -1.08747 | -1.08747 | 0.930729 | 0.930729 | 0 | 0 | 8035 |
| FW [m3/s] | -67377.8 | -67377.8 | 120179 | 120179 | 0 | 0 | 4096 |
| Salt [kg/s] | -1.29354e+07 | -1.29354e+07 | 3.28719e+07 | 3.28719e+07 | 0 | 0 | 4096 |
| SSS [PSU] | 31.9411 | 31.9411 | 1.36534 | 1.36534 | 0 | 0 | 217307 |
| SSS coverage [%] | 29.3968 | 29.3968 | nan | nan | 0 | 0 | 739220 |

