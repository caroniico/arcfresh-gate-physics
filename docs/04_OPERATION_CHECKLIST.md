# Operational Checklist

## Prima di analizzare

- Verificare path `netcdf_new/` accessibile.
- Verificare che il gate scelto sia presente in `03_NETCDF_PRODUCTION_STATUS.md`.
- Aprire `gate_analysis.ipynb` e impostare:
  - `GATE_ID`
  - `DATE_START`, `DATE_END`
  - `CAP`, `S_REF`, `RHO`

## Durante analisi

- Usare sempre il metodo locale per-point (`v_perp` da normale locale).
- Controllare la cella Spatial Mapping (gate + normali + vettori velocità).
- Se SSS non disponibile, FW/Salt diventano parziali o NaN (atteso).

## Controlli qualità minimi

- `v_perp` shape = `(point, time)`
- `sigma_v_perp >= 0`
- `VT` non vuoto su periodo con dati CMEMS
- per FW/Salt: verificare coverage salinità (percentuale NaN)

## Confronto old/new

- Eseguire confronto su Fram e Davis con stesso metodo locale per-point su entrambi.
- Confrontare: mean/std/bias/%delta per VT/FW/Salt + coverage SSS.
