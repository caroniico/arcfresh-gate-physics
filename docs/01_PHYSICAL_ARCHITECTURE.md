# Physical Architecture (Gate Analysis)

## 1. Coordinate e convenzioni di segno

- `ugos` (CMEMS): componente geostrofica est-ovest, **positiva verso Est**.
- `vgos` (CMEMS): componente geostrofica nord-sud, **positiva verso Nord**.
- I gate sono polilinee discrete (`point`), con geometria da shapefile.

## 2. Definizione fisica di v_perp (nuovo metodo)

Per ogni punto `i` del gate:

1. Si calcola la tangente locale `t(i)` dalla geometria del gate:
   - differenze centrali negli interni,
   - forward/backward agli estremi,
   - correzione metrica su longitudine: `dlon * cos(lat)`.
2. Si costruisce la normale locale `n(i) = (-t_y, t_x)`.
3. Si orienta `n(i)` verso lato Artico con vettore verso `(0E, 90N)`.
4. Si applica un controllo di continuità per evitare flip spurii tra punti adiacenti.

Formula finale:

`v_perp(i,t) = ugos(i,t) * u_into_local(i) + vgos(i,t) * v_into_local(i)`

Interpretazione:

- `v_perp > 0`: flusso verso lato Artico (inflow)
- `v_perp < 0`: flusso opposto (outflow)

## 3. Quantità integrate

Con `H(i) = min(depth(i), depth_cap)` e `dx(i)`:

- Volume Transport:
  - `VT(t) = Σ_i [v_perp(i,t) * H(i) * dx(i)] / 1e6`  (Sv)
- Freshwater Transport:
  - `FW(t) = Σ_i [v_perp(i,t) * (1 - S(i,t)/S_ref) * H(i) * dx(i)]` (m3/s)
- Salt Flux:
  - `SF(t) = Σ_i [rho * (S(i,t)/1000) * v_perp(i,t) * H(i) * dx(i)]` (kg/s)

## 4. Uncertainty propagation

Con errori formali CMEMS `err_ugosa`, `err_vgosa`:

`σ_v_perp(i,t) = sqrt((err_ugosa(i,t)*u_into_local(i))^2 + (err_vgosa(i,t)*v_into_local(i))^2)`

Le incertezze su VT/FW/SF sono propagate dalla `σ_v_perp` sulle rispettive formule integrate.

## 5. Principi bloccati

- Nessun uso operativo di `theta` legacy nel nuovo workflow.
- Nessun vettore unico gate-level per il calcolo principale.
- Niente smoothing extra oltre al rimappo/interpolazione dei dataset sorgente.
