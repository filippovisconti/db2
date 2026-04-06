---
title: "TAGD-01-formulario"
author:
  - Filippo Visconti
template:
  - template.tex
---

# Architettura e Componenti del DBMS

* **Gestore delle Interrogazioni**: Traduce query SQL in operazioni fisiche (scansione, accesso diretto, ordinamento).

* **Gestore dei Metodi d'Accesso**: Esegue letture "virtuali" interfacciandosi con il buffer.

* **Gestore del Buffer**: Intermediario che ottimizza le prestazioni tramite cache in RAM.

* **Gestore della Memoria Secondaria**: Interfaccia finale per la lettura/scrittura fisica.

# Memoria e Prestazioni Hardware

**Blocco (Disco) / Pagina (RAM)**: Unità di memorizzazione di lunghezza fissa (KB).

**Tempo di Accesso HDD**: $Tempo\ di\ posizionamento\ (4-15ms) + Latenza\ di\ rotazione\ (2-8ms) + Tempo\ di\ trasferimento\ (<1ms)$.

**Costo I/O**: Un accesso alla memoria secondaria è $\approx 10^4$ volte più lento della RAM.

**Località dei dati**: Principio per cui dati acceduti di recente o contigui (prefetching) hanno costi minori.

# Gestione del File System e Mapping

* **Mappatura Gerarchica**:

  * **OS**: Dischi reali $\rightarrow$ Extents $\rightarrow$ Dischi logici $\rightarrow$ OS-Files.
  * **DBMS**: Tablespaces $\rightarrow$ Segmenti $\rightarrow$ Relazioni.

* **Interazione DBMS-FS**:

  * **Livello Blocchi**: Controllo totale ma alta complessità.
  * **Livello File**: Semplice ma il DBMS perde visibilità sull'allocazione fisica.
  * **Soluzione Intermedia**: Approccio standard dove il DBMS gestisce l'organizzazione interna ai file.

# Buffer Management

**Direttorio del Buffer**: Tabella di controllo con _ID Blocco_, _Contatore di Pin_ (fissaggio) e _Dirty Bit_ (modifica).

**Operazioni**: `fix/pin` (richiesta), `unfix/unpin` (rilascio), `setDirty` (modifica), `force/flush` (scrittura sincrona).

**Politiche di Rimpiazzo**:

  * **Naive**: Sceglie la prima pagina libera.
  * **FIFO**: Sostituisce la pagina caricata da più tempo.
  * **LRU (Least Recently Used)**: Sostituisce la pagina inutilizzata da più tempo.
  * **Clock**: Scansione circolare efficiente.

**Protocolli**: **No-steal** (non espelle pagine con pin > 0); **Steal** (permette l'espulsione di pagine occupate).

# Organizzazione Fisica dei Record

* **Fattore di Blocco ($f$)**: Numero di record per blocco.
  * **Formula**: $f = \lfloor L_B / L_R \rfloor$ (dove $L_B$ è dimensione blocco e $L_R$ lunghezza record).

* **Organizzazione**: **Unspanned** (record intero nel blocco) o **Spanned** (record diviso tra blocchi).

* **Strutture Primarie**: **Heap** (disordinata, costo scansione $O(N)$), **Ordinata** (per pseudochiave), **Hash**.

* **Posizionamento SimpleDB (Record a lunghezza fissa)**:

  * **Flag di stato (slot $k$)**: $(RL+1) \times k$.
  * **Campo $F$ (slot $k$)**: $(RL+1) \times k + OFFSET(F) + 1$.

# File Hash e Hashing Estendibile

* **Costo Medio Accesso Hash**: $1 + Lunghezza\ media\ catene\ di\ overflow$.
* **Coefficiente di Riempimento**: $T / (F \times B)$.
* **Hashing Estendibile**: Usa una directory di dimensione $2^d$ (dove $d$ è la profondità globale) e blocchi con profondità locale.

# Indici e B-Tree

* **Indice Primario**: Su campo ordinato fisicamente (di solito scarso).

* **Indice Secondario**: Su campo non ordinato (sempre denso).

* **Formule Dimensioni Indice**:

  * $N_F$ (blocchi file) $= L / f$.
  * $f_I$ (fattore blocco indice) $= B / (K+P)$.
  * $N_D$ (blocchi indice denso) $= L / f_I$.
  * $N_S$ (blocchi indice scarso) $= N_F / f_I$.

* **B-Tree**: Albero bilanciato di ordine $P$. Nodi pieni tra 50% e 100%.
  * **B+ Tree**: Dati solo nelle foglie collegate in lista.

# Ottimizzazione e Join

* **Euristiche Algebriche**: "Push selections down" e "Push projections down".

* **Merge-Sort Esterno**:

  * Costo base: $2 \times N \times \log_2 N$.
  * Costo con $P$ buffer (se $P \geq \sqrt{N}$): $3 \times N$.

* **Costi Join ($B_1, B_2$ blocchi; $L_1$ record; $I_2$ profondità indice)**:

  * **Nested Loop (base)**: $B_1 + B_1 \times B_2$.
  * **Nested Loop (con $B$ buffer)**: $N_1 + (N_1/B \times N_2)$.
  * **Nested Loop con Indice**: $N_1 + L_1 \times (I_2 + 1)$.
  * **Merge Join (ordinato)**: $N_1 + N_2$.
  * **Hash Join**: $3 \times (B_1 + B_2)$.

# Strategie di Esecuzione

* **Pipelining**: Passaggio immediato dei record tra operatori (on-demand).
* **Materializzazione**: Scrittura dei risultati intermedi su disco.
* **Metodo di Shasha**: Algoritmo decisionale per la scelta della struttura primaria (Heap vs Cluster vs Hash) basato su dinamicità e tipo di ricerca.

