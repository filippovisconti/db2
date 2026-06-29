#!/usr/bin/env python3
import sys
from typing import Literal
import pandas as pd
from pandas import DataFrame
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def calcola_report_completo(
    df: pd.DataFrame,
    durata_ore: float,
    u_cpu_tot: float,
    u_raid_tot: float,
    n_clusters: int,
):
    T_sec = durata_ore * 3600
    N_tot = len(df)
    X_tot = N_tot / T_sec

    print("=== PASSO 0: Dati base ===")
    print(f"Throughput totale (X_tot): {X_tot:.4f} tx/s\n")

    # --- CLUSTERING ---
    features: list[str] = ["CPU Time", "I/O on Disk", "% Read Operations"]
    X_data: DataFrame = df[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_data)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["Cluster"] = kmeans.fit_predict(X_scaled) + 1

    # --- PASSO 1: CALCOLI PER CLASSE ---
    print("=" * 70)
    print("=== PASSO 1: Service Demand, Tempi e Job (Multiclasse) ===")
    print("=" * 70)

    somma_cpu_tot = df["CPU Time"].sum()
    somma_disk_tot = df["I/O on Disk"].sum()

    risultati_cluster: list[dict[str, float]] = []
    N_job_totali = 0.0

    for i in range(1, n_clusters + 1):
        # seleziono solo gli elementi del cluster in esame
        df_cluster = df[df["Cluster"] == i]

        # numero di transazioni nel cluster
        N_c = len(df_cluster)

        # throughput del cluster
        X_c = N_c / T_sec

        peso_cpu_c = df_cluster["CPU Time"].sum() / somma_cpu_tot
        peso_disk_c = df_cluster["I/O on Disk"].sum() / somma_disk_tot

        # utilizzazione cpu e disco per cluster calcolata proporzionalmente rispetto al totale
        U_cpu_c = u_cpu_tot * peso_cpu_c
        U_disk_c = u_raid_tot * peso_disk_c

        # service demand calcolata con la Service Demand Law
        D_cpu_c_ms = (U_cpu_c / X_c) * 1000 if X_c > 0 else 0
        D_disk_c_ms = (U_disk_c / X_c) * 1000 if X_c > 0 else 0

        # estraggo la percentuale di letture dal file relativo al singolo cluster
        read_pct_c = df_cluster["% Read Operations"].mean()

        R_cpu_c_ms = D_cpu_c_ms / (1 - u_cpu_tot)
        R_disk_c_ms = D_disk_c_ms / (1 - u_raid_tot)
        R_tot_c_ms = R_cpu_c_ms + R_disk_c_ms

        N_job_c = X_c * (R_tot_c_ms / 1000)
        N_job_totali += N_job_c

        risultati_cluster.append(
            {
                "Cluster": i,
                "N": N_c,
                "X_c": X_c,
                "D_cpu_c": D_cpu_c_ms,
                "D_disk_c": D_disk_c_ms,
                "read_pct": read_pct_c,
            }
        )

        print(f"CLUSTER {i} ({N_c} tx, {N_c / N_tot * 100:.1f}%):")
        print(f"  - Throughput (X_c) : {X_c:.4f} tx/s")
        print(
            f"  - Service Demand   : D_cpu = {D_cpu_c_ms:.2f} ms | D_disk = {D_disk_c_ms:.2f} ms"
        )
        print(f"  - % Read medio     : {read_pct_c:.1f}%")
        print(
            f"  - Tempi Risposta   : R_cpu = {R_cpu_c_ms:.2f} ms | R_disk = {R_disk_c_ms:.2f} ms | R_tot = {R_tot_c_ms:.2f} ms"
        )
        print(f"  - Job (Little)     : N_job = {N_job_c:.4f}\n")

    R_tot_globale_ms = (N_job_totali / X_tot) * 1000

    print("-" * 70)
    print("=== RISULTATI GLOBALI (Punto 2) ===")
    print(f"Numero medio di job nel sistema (N_tot) : {N_job_totali:.4f}")
    print(f"Tempo di risposta medio complessivo     : {R_tot_globale_ms:.2f} ms")
    print("-" * 70 + "\n")

    # --- PASSO 2: CARICO MASSIMO ---
    print("=" * 70)
    print("=== PASSO 2: Carico Massimo (Bottleneck <= 70%) ===")
    print("=" * 70)

    centro_max: Literal["CPU", "RAID-0"] = "CPU" if u_cpu_tot > u_raid_tot else "RAID-0"
    U_max: float = max(u_cpu_tot, u_raid_tot)

    k_scala = 0.70 / U_max
    X_max_tot = X_tot * k_scala

    print(f"Collo di bottiglia attuale : {centro_max} (U = {U_max * 100:.0f}%)")
    print(f"Fattore di scala (k)       : {k_scala:.4f}x")
    print(f"Throughput Max Totale      : {X_max_tot:.4f} tx/s\n")

    print(f"{'Cluster':<10} | {'X_c (tx/s)':<15} | {'X_c_max (tx/s)':<15}")
    print("-" * 45)
    for res in risultati_cluster:
        res["X_c_max"] = res["X_c"] * k_scala
        print(
            f"Cluster {res['Cluster']:<2} | {res['X_c']:<15.4f} | {res['X_c_max']:<15.4f}"
        )
    print("\n")

    # --- PASSO 3: RAID-1 MULTICLASSE ---
    print("=" * 70)
    print("=== PASSO 3: Passaggio a RAID-1 (Verifica Bottleneck <= 70%) ===")
    print("=" * 70)

    # L'utilizzo della CPU a X_max è stato scalato esattamente al 70% nel Passo 2
    u_cpu_max_fissa = 0.70

    N_dischi: int = 2
    while True:
        print(f"\n--- TEST CONFIGURAZIONE: N = {N_dischi} dischi ---")
        U_raid1_totale = 0

        for res in risultati_cluster:
            f_r: float = res["read_pct"] / 100
            f_w: float = 1 - f_r

            # D_disk per il singolo disco in RAID-1
            D_disk_c_raid1_ms: float = res["D_disk_c"] * 2 * (f_r / N_dischi + f_w)
            # Utilizzazione del cluster generata sul singolo disco
            U_c_raid1: float = res["X_c_max"] * (D_disk_c_raid1_ms / 1000)

            U_raid1_totale += U_c_raid1

            print(
                f"  Cluster {res['Cluster']}: D_RAID1 = {D_disk_c_raid1_ms:6.2f} ms | U_disco = {U_c_raid1 * 100:5.2f}%"
            )

        # Verifica del nuovo collo di bottiglia globale del sistema
        bottleneck_attuale: float = max(u_cpu_max_fissa, U_raid1_totale)
        nome_bottleneck = "CPU" if u_cpu_max_fissa >= U_raid1_totale else "RAID-1"

        print("-" * 40)
        print(
            f"  > Utilizzo CPU Totale    : {u_cpu_max_fissa * 100:.2f}% (costante dal Passo 2)"
        )
        print(f"  > Utilizzo RAID-1 Totale : {U_raid1_totale * 100:.2f}%")
        print(
            f"  > COLLO DI BOTTIGLIA     : {nome_bottleneck} al {bottleneck_attuale * 100:.2f}%"
        )

        if bottleneck_attuale <= 0.70:
            print(
                f"\n✅ SUCCESS: Trovata configurazione valida con N={N_dischi} dischi!"
            )
            print("Nessun centro di servizio supera la soglia del 70%.")
            break
        else:
            print(
                f"\n❌ FALLITO: Il {nome_bottleneck} supera il 70%. Necessario aumentare i dischi."
            )
            N_dischi += 1


def main() -> None:
    durata = 24  # ore
    u_cpu = 0.23
    u_raid = 0.19
    n_clusters = 5

    try:
        df: DataFrame = pd.read_csv("transactions.csv")
    except FileNotFoundError:
        print("Errore: file 'transactions.csv' non trovato.")
        sys.exit(1)

    calcola_report_completo(df, durata, u_cpu, u_raid, n_clusters)


if __name__ == "__main__":
    main()
