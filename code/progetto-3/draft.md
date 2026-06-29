# Progetto 3 / Filippo Visconti

% Read Operations

## Dati di partenza

| | |
| --- | --- |
| Durata osservazione | 24 ore = 86.400 s |
| Utilizzazione media CPU | U_cpu = 0.23 |
| Utilizzazione media RAID 0 | U_raid = 0.19 |
| Numero di transazioni | X = 100.000 tx |

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
D_cpu = u_cpu / X * 1000=198.72 ms
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

### 1.4 Tabella riassuntiva

| Centro | Formula | Valore calcolato | Utilizzazione |
| --- | --- | --- | --- |
| CPU | `D_cpu = u_cpu / X * 1000=` | D_cpu = 198.72 ms | 23% |
| RAID-0 | `D_raid = U_raid / X * 1000 ` | D_disk = 164.16 ms | 19% |

---

## Passo 2 — Tempo di Risposta e Job Medi

### 2.1 Tempo di risposta per centro

Per un sistema a **coda aperta M/M/1**:

```python
R_k = D_k / (1 - U_k)     [secondi]
```

Applicato a ciascun centro:

```python
R_cpu  = D_cpu  / (1 - 0.23) =
R_disk = D_disk / (1 - 0.19) =
```

> R_k include sia il tempo di attesa in coda che il tempo di servizio. Il termine (1 - U_k) cattura l'effetto di congestione: più il centro è carico, più l'attesa cresce.

### 2.2 Tempo di risposta complessivo

Il sistema è in serie (tandem), quindi:

```python
R_tot = R_cpu + R_disk     [secondi]
```

### 2.3 Numero medio di job — Legge di Little

```python
N_job = X · R_tot
```

Scomponendo per centro:

```python
N_cpu  = X · R_cpu
N_disk = X · R_disk
N_job  = N_cpu + N_disk
```

### 2.4 Schema di calcolo

| Grandezza | Formula | CPU | RAID |
| --- | --- | --- | --- |
| D_k [ms] | vedi Passo 1 | ? | ? |
| U_k | fornita | 0.23 | 0.19 |
| R_k [ms] | D_k / (1 − U_k) | ? | ? |
| N_k [job] | X · R_k | ? | ? |

---

## Passo 3 — Carico Massimo con Bottleneck ≤ 70%

### 3.1 Identificazione del collo di bottiglia

Il collo di bottiglia è il centro con **service demand massima**:

```python
D_max = max(D_cpu, D_disk)
```

### 3.2 Throughput massimo

Imponendo U_bottleneck = 0.70:

```python
X_max = 0.70 / D_max     [tx/s]
```

### 3.3 Incremento proporzionale su tutte le classi

Se il workload corrente ha throughput X e si scala di un fattore k:

```python
k_max = X_max / X = 0.70 / U_bottleneck_attuale
```

> Esempio: se U_bottleneck = 0.23, allora k_max = 0.70 / 0.23 ≈ 3.04. Il sistema può reggere circa 3× il carico attuale.

Per ogni classe c con throughput X_c:

```python
X_c_max = k_max · X_c
```

---

## Passo 4 — Passaggio a RAID-1

### 4.1 Come cambia il modello

In RAID-1 ogni disco è una copia degli altri. L'effetto sul carico dipende dal tipo di operazione:

| Operazione | RAID-0 | RAID-1 (N dischi) |
| --- | --- | --- |
| Lettura | servita da 1 disco | distribuita su tutti N dischi → carico / N |
| Scrittura | 1 operazione | replicata su tutti N dischi → carico × N |

### 4.2 Service demand per disco in RAID-1

Sia `f_r = mean(read_pct) / 100` e `f_w = 1 - f_r`. Con N dischi:

```python
D_read_per_disk  = f_r · D_disk / N
D_write_per_disk = f_w · D_disk · N

D_disk_RAID1 = D_disk · (f_r/N + f_w·N)
```

> Con N=2 e f_r=0.70: D_disk_RAID1 = D_disk · (0.35 + 0.60) = 0.95 · D_disk. Le letture si alleggeriscono, le scritture si raddoppiano.

### 4.3 Verifica al throughput X_max

```python
U_RAID1 = X_max · D_disk_RAID1
```

- Se **U_RAID1 ≤ 0.70**: il sistema regge. Risposta: **SÌ**, sono necessari N dischi.
- Se **U_RAID1 > 0.70**: il sistema **non regge**. Occorre aumentare N.

### 4.4 Trovare il numero minimo di dischi

Si cerca il minimo intero N ≥ 2 tale che U_RAID1(N) ≤ 0.70. Si prova N = 2, 3, 4, … finché il vincolo è soddisfatto, oppure si risolve analiticamente:

```python
X_max · D_disk · (f_r/N + f_w·N) = 0.70
```

### 4.5 Tolleranza ai guasti

RAID-1 con N dischi tollera il guasto di N−1 dischi contemporaneamente. Per tollerare **almeno 1 guasto** è sufficiente N = 2. Se la verifica al passo 4.3 richiede N > 2, la tolleranza è automaticamente garantita.

## Appendice — Riferimento Formule

| Grandezza | Formula | Note |
| --- | --- | --- |
| X | N / T | N = tx nella traccia, T = 86.400 s |
| D_cpu | mean(cpu_time_ms) / 1000 | dalla traccia |
| D_disk (RAID-0) | U_raid / X | Legge dell'utilizzazione |
| S_disk | D_disk / mean(disk_visits) | tempo fisico per singola visita |
| R_k | D_k / (1 − U_k) | formula M/M/1 aperta |
| R_tot | Σ R_k | somma su tutti i centri |
| N_job | X · R_tot | Legge di Little |
| X_max | 0.70 / D_max | bottleneck ≤ 70% |
| k_max | X_max / X | fattore di scala massimo |
| D_disk_RAID1 | D_disk · (f_r/N + f_w·N) | N = numero dischi |
