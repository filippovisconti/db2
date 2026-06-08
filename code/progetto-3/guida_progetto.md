# Progetto 3 / Filippo Visconti

% Read Operations

## Dati di partenza

| | |
| --- | --- |
| Durata osservazione | 24 ore = 86.400 s |
| Utilizzazione media CPU | U_cpu = 0.23 |
| Utilizzazione media RAID | U_raid = 0.19 |
| Numero di transazioni | X = 100.000 tx|

---

## Passo 1 — Calcolo delle Service Demand

La **service demand** $D_k$ è il tempo totale che una transazione media spende al centro k (attesa + servizio). Si ricava dalla **Legge dell'Utilizzazione**: $U_k = X · D_k   →   D_k = U_k / X$.

### 1.1 Throughput X

$$
X = N / T
$$

con N = numero di transazioni, ossia il numero di righe della traccia e T = 86.400 s. Facendo i conti, si ottiene che il throughput è pari a

$$
X = 1,157 \text{ tx/s}
$$

### 1.2 Service demand CPU

Il tempo CPU medio si potrebbe ricavare calcolando la media o mediana della colonna CPU Time, ottenendo

```python
D_cpu = df["CPU Time"].mean()=2.05 (unità tempo di CPU),
```

tuttavia l'unità di misura è ignota e calcolandola tramite l'utilizzazione e il throughput forniti dovrebbe essere pari a

```python
u_cpu / X * 1000=198.72 ms
```
Ne consegue che $1$ unita tempo di CPU corrisponde a
```python
 (u_cpu / X * 1000) / df['CPU Time'].mean() = 96.95 millisecondi
```

<!-- > **Verifica:** deve risultare D_cpu ≈ U_cpu / X = 0.23 / X. -->

### 1.3 Service demand RAID-0

Il tempo per visita al disco non è nella traccia, quindi usiamo la legge dell'utilizzazione con il dato fornito:

```python
D_disk = U_raid / X     [secondi]
```

utilizzando

```python
    U_raid    : 19%
e
    X         : 100.000 tx
```

otteniamo che

```python
D_disk             : 0.19/1.157 * 1000= 164.16 ms
```

Da qui si ricava anche il tempo medio di servizio per singola visita:

```python
mediana num visite : df['I/O on Disk'].mean() = 3
tempo di servizio  : D_disk / mediana num visite = 54.72 millisecondi/visita
```

Si evince che il disco non è particolarmente performante, in quanto sarebbe auspicabile un valore nell'intorno dei 10 ms.
