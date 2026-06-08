#!/usr/bin/env python3
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# Stampa delle statistiche di verifica
# ---------------------------------------------------------------------------


def stampa_statistiche(
    df: pd.DataFrame, throughput: float, u_cpu: float, u_raid: float
) -> None:

    N = len(df)
    X = throughput
    # Transaction ID,CPU Time,I/O on Disk
    # Service demand derivate dalla traccia
    D_cpu_ms = u_cpu / X * 1000
    mean_vis = df["I/O on Disk"].median()

    # D_disk dalla legge dell'utilizzazione
    D_disk_ms = u_raid / X * 1000
    S_disk_ms = D_disk_ms / mean_vis  # tempo di servizio per singola visita

    print(f"  Transazioni          : {N}")
    print(f"  Throughput (X)       : {X:.3f} tx/s")
    print()
    print("  CPU")
    print(
        f"    mediana cpu_time   : {df['CPU Time'].mean()=:.2f} (unita' tempo di CPU), ma secondo l'utilizzazione e il throughput forniti dovrebbe essere {u_cpu / X * 1000=:.2f} ms"
    )
    print(
        f"    fattore di scala   : 1 unita tempo di CPU corrisponde a {(u_cpu / X * 1000) / df['CPU Time'].mean()=:.2f}ms "
    )
    print(f"    D_cpu              : {D_cpu_ms:.2f} ms -- U_cpu / X")
    print(f"    U_cpu calcolata    : {u_cpu * 100:.0f}% -- D_cpu * X")
    print()
    print("  RAID")
    print(f"    mediana num visite : {mean_vis:.3f}")
    print(f"    D_disk             : {D_disk_ms:.2f} ms")
    print(f"    tempo di servizio  : {S_disk_ms:.2f} ms")
    print(f"    U_raid             : {u_raid * 100:.0f}%")
    print()
    print("  LETTURE")
    print(f"    media read_pct     : {df['% Read Operations'].mean():.1f} %")
    print(f"    media write_pct    : {100 - df['% Read Operations'].mean():.1f} %")
    print()
    print("  DISTRIBUZIONE CPU Time")
    print("    min / 25% / 50% / 75% / max")
    q = df["CPU Time"].quantile([0, 0.25, 0.50, 0.75, 1])
    print(
        f"    {q[0]:.1f} / {q[0.25]:.1f} / {q[0.50]:.1f} / {q[0.75]:.1f} / {q[1]:.1f}"
    )


def main():

    durata = 24  # ore
    u_cpu = 0.23
    u_raid = 0.19
    df = pd.read_csv("transactions.csv")
    n_transazioni = len(df)
    throughput = n_transazioni / (durata * 60 * 60)  # tx/s

    # Validazione
    for name, val, lo, hi in [
        ("u_cpu", u_cpu, 0.01, 0.99),
        ("u_raid", u_raid, 0.01, 0.99),
        ("throughput", throughput, 0.01, 1e6),
    ]:
        if not (lo <= val <= hi):
            print(f"Errore: {name}={val} fuori range [{lo}, {hi}]")
            sys.exit(1)
    print(
        f"  durata={durata}h  u_cpu={u_cpu}  u_raid={u_raid}"
        f"  X={throughput:.3f} tx/s  N={n_transazioni}\n"
    )

    stampa_statistiche(df, throughput, u_cpu, u_raid)


if __name__ == "__main__":
    main()
