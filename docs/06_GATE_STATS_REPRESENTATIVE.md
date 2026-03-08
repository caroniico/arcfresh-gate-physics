# Gate Statistics (Representative File per Gate)

Source: `/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE`

| gate | file | n_points | n_time | gate_length_km | dx_min_m | dx_mean_m | dx_max_m | dx_std_m | size_mb | has_cci | has_isas |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| barents_opening | arcfresh_barents_opening_2002-2023.nc | 211 | 8035 | 830.0 | 2909.2 | 3960.6 | 8004.0 | 846.3 | 12.5 | 1 | 1 |
| barents_sea_cao | arcfresh_barents_sea_cao_2002-2023.nc | 493 | 8035 | 1153.4 | 1527.4 | 2351.1 | 8438.0 | 1407.2 | 21.6 | 0 | 0 |
| barents_sea_kara_sea | arcfresh_barents_sea_kara_sea_2002-2023.nc | 353 | 8035 | 1314.5 | 2043.5 | 3739.3 | 7377.4 | 1578.0 | 3.7 | 0 | 0 |
| beaufort_sea_caa | arcfresh_beaufort_sea_caa_2002-2023.nc | 179 | 8035 | 710.4 | 2161.5 | 3989.3 | 5178.7 | 928.3 | 4.2 | 0 | 0 |
| beaufort_sea_cao | arcfresh_beaufort_sea_cao_2002-2023.nc | 364 | 8035 | 1135.6 | 2779.3 | 3131.5 | 5141.8 | 363.7 | 22.9 | 0 | 0 |
| bering_strait | arcfresh_bering_strait_2002-2023.nc | 23 | 8035 | 125.1 | 5658.6 | 5687.0 | 5740.9 | 21.9 | 2.2 | 1 | 1 |
| caa_cao | arcfresh_caa_cao_2002-2023.nc | 291 | 8035 | 730.6 | 1763.5 | 2518.4 | 3397.4 | 371.3 | 14.9 | 0 | 0 |
| davis_strait | arcfresh_davis_strait_2002-2023.nc | 92 | 8035 | 479.6 | 5190.7 | 5272.3 | 5481.5 | 93.8 | 6.9 | 1 | 1 |
| denmark_strait | arcfresh_denmark_strait_2002-2023.nc | 95 | 8035 | 533.7 | 5594.8 | 5678.4 | 5837.9 | 65.9 | 8.4 | 1 | 1 |
| ess_beaufort_sea | arcfresh_ess_beaufort_sea_2002-2023.nc | 164 | 8035 | 636.8 | 2190.5 | 3921.4 | 7424.6 | 1358.6 | 7.7 | 0 | 0 |
| ess_cao | arcfresh_ess_cao_2004-2004.nc | 3971 | 366 | 11946.5 | 2039.7 | 3009.4 | 9670.4 | 356.9 | 8.8 | 0 | 0 |
| fram_strait | arcfresh_fram_strait_2002-2023.nc | 277 | 8035 | 732.1 | 1993.3 | 2651.6 | 3658.6 | 486.5 | 19.6 | 1 | 1 |
| jones_sound | arcfresh_jones_sound_2002-2023.nc | 24 | 8035 | 78.9 | 2923.6 | 3428.5 | 3766.8 | 230.7 | 0.7 | 0 | 0 |
| kara_sea_cao | arcfresh_kara_sea_cao_2002-2023.nc | 322 | 8035 | 728.9 | 1456.8 | 2269.9 | 8105.2 | 1576.8 | 17.9 | 0 | 0 |
| kara_sea_laptev_sea | arcfresh_kara_sea_laptev_sea_2002-2023.nc | 236 | 8035 | 594.9 | 1275.1 | 2530.1 | 6931.6 | 1268.1 | 4.0 | 0 | 0 |
| lancaster_sound | arcfresh_lancaster_sound_2002-2023.nc | 29 | 8035 | 106.2 | 3549.0 | 3788.8 | 3849.4 | 88.8 | 0.7 | 0 | 0 |
| laptev_sea_cao | arcfresh_laptev_sea_cao_2002-2023.nc | 433 | 8035 | 1101.4 | 2082.8 | 2548.8 | 2996.6 | 226.4 | 23.7 | 0 | 0 |
| laptev_sea_ess | arcfresh_laptev_sea_ess_2002-2023.nc | 192 | 8035 | 659.6 | 2048.7 | 3449.6 | 4346.5 | 569.2 | 4.7 | 0 | 0 |
| nares_strait | arcfresh_nares_strait_2002-2023.nc | 86 | 8035 | 153.0 | 1565.0 | 1819.5 | 5449.3 | 455.2 | 5.3 | 0 | 1 |
| norwegian_boundary | arcfresh_norwegian_boundary_2002-2023.nc | 173 | 8035 | 1050.4 | 5550.4 | 6106.6 | 6874.4 | 393.2 | 15.1 | 1 | 1 |

## Note

- `dx` NON è uguale per tutti i gate.
- `dx` non è nemmeno costante dentro ogni gate (varia lungo la geometria).
- Per `ess_cao` i file annuali hanno lo stesso `n_points` e la stessa statistica `dx`; cambia solo `n_time` (365/366).
