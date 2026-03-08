# NetCDF Production Status (Current Snapshot)

Sorgente controllata: `/Users/nicolocaron/Desktop/ARCFRESH/NETCDF CODE`

- File trovati: **33**
- Gate unici trovati: **20**
- Gate target del builder: **20**

> Nota: alcuni gate sono spezzati nel tempo (es. `ess_cao_YYYY-YYYY.nc`) quindi il numero file è maggiore del numero gate unici.

## Gate presenti

- barents_opening
- barents_sea_cao
- barents_sea_kara_sea
- beaufort_sea_caa
- beaufort_sea_cao
- bering_strait
- caa_cao
- davis_strait
- denmark_strait
- ess_beaufort_sea
- ess_cao
- fram_strait
- jones_sound
- kara_sea_cao
- kara_sea_laptev_sea
- lancaster_sound
- laptev_sea_cao
- laptev_sea_ess
- nares_strait
- norwegian_boundary

## Gate mancanti (rispetto ai 20 target)

- Nessuno (20/20 completati)

## Copertura temporale

- Standard target: `2002-01-01 -> 2023-12-31`
- Alcuni gate molto grandi usano split per anno/chunk per robustezza di build.
