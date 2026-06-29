import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# 1. Carica i dati
file_path = "transactions.csv"
df = pd.read_csv(file_path)

# 2. Seleziona SOLO le colonne utili per il clustering (ignoriamo il Transaction ID)
features = ["CPU Time", "I/O on Disk", "% Read Operations"]
X = df[features]

# 3. Standardizza i dati (fondamentale!)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Calcola la dispersione per vari numeri di cluster (da 1 a 10)
wcss = []  # WCSS = Within-Cluster Sum of Square (simile all'OMSR)
k_range = range(1, 11)

print("Calcolo in corso... (con 100.000 righe potrebbe volerci qualche secondo)")
for k in k_range:
    # Inizializza l'algoritmo K-Means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
    kmeans.fit(X_scaled)
    # Salva il valore della dispersione
    wcss.append(kmeans.inertia_)

# 5. Crea il grafico del Metodo del Gomito
plt.figure(figsize=(10, 6))
plt.plot(k_range, wcss, marker="o", linestyle="-", color="blue")
plt.title("Metodo del Gomito per trovare il numero ottimale di Cluster")
plt.xlabel("Numero di Cluster (k)")
plt.ylabel("Dispersione (Inertia)")
plt.xticks(k_range)
plt.grid(True, linestyle="--", alpha=0.7)

plt.tight_layout()
plt.savefig("cluster.png", dpi=600)
