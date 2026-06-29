import pandas as pd
import matplotlib.pyplot as plt

# 1. Definisci il percorso del tuo file CSV
file_path = "transactions.csv"

# 2. Leggi i dati ignorando eventuali spazi extra
df = pd.read_csv(file_path)

# 3. Imposta la finestra dei grafici (1 riga, 3 colonne)
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# --- GRAFICO 1: Transaction ID vs CPU Time ---
axes[0].scatter(df["Transaction ID"], df["CPU Time"], color="blue", alpha=0.3, s=5)
axes[0].set_title("Andamento CPU Time")
axes[0].set_ylabel("CPU Time")
axes[0].grid(True, linestyle="--", alpha=0.6)

# --- GRAFICO 2: Transaction ID vs I/O on Disk ---
axes[1].scatter(df["Transaction ID"], df["I/O on Disk"], color="orange", alpha=0.3, s=5)
axes[1].set_title("Andamento I/O on Disk")
axes[1].set_ylabel("I/O on Disk")
axes[1].grid(True, linestyle="--", alpha=0.6)

# --- GRAFICO 3: Transaction ID vs % Read Operations ---
axes[2].scatter(
    df["Transaction ID"], df["% Read Operations"], color="green", alpha=0.3, s=5
)
axes[2].set_title("Andamento % Read Operations")
axes[2].set_xlabel(
    "Transaction ID"
)  # L'etichetta X serve solo sull'ultimo grafico in basso
axes[2].set_ylabel("% Read")
axes[2].grid(True, linestyle="--", alpha=0.6)
# 4. Ottimizza gli spazi e mostra/salva il risultato
plt.tight_layout()

# Scegli se visualizzare a schermo o salvare come immagine:
# plt.show()
plt.savefig("scatter_distribuzione.png", dpi=600)
