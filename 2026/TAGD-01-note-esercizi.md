---
title: "TAGD-01-Esercizi"
author:
  - Filippo Visconti
template:
  - template.tex
---

# Esercizi

## Esercizio 2 del 28.03.2014


Si consideri una relazione con L=1.000.000 ennuple e fR​=100. Ricerca su un attributo "Mansione" con indice di profondità p=4.

1. **Campo selettivo (m1 = 100.000 valori diversi per Mansione)**:

   * Costo accesso sequenziale: L/fR​=10.000 accessi.
   * Costo accesso diretto: p+(L/m1​)=4+10=14 accessi.

2. **Campo poco selettivo (m2 = 20 valori diversi per Mansione)**:

   * Costo accesso sequenziale: L/fR​=10.000 accessi.
   * Costo accesso diretto: p+(L/m2​)=4+50.000=50.004 accessi. In questo secondo caso, l'accesso sequenziale è molto più efficiente dell'indice, poiché l'indice secondario richiederebbe un accesso al disco per quasi ogni record, senza poter sfruttare la lettura sequenziale dei blocchi.

L'analisi dell'efficienza nel recupero dei dati si basa sul confronto tra il costo della scansione lineare dell'intero file e l'utilizzo di una struttura ausiliaria (indice).

### Parametri fondamentali

* $L$: numero totale di record (ennuple) nella relazione.
* $f\_R$: fattore di blocco della relazione (numero di record per blocco).
* $p$: profondità dell'indice (numero di livelli dell'albero da attraversare).
* $m$: numero di valori distinti dell'attributo utilizzato per la ricerca.

### Formule di costo

1. **Costo Accesso Sequenziale ($C\_{seq}$)**: rappresenta il numero totale di blocchi che compongono il file. Si calcola dividendo il numero di record per il fattore di blocco: $$C\_{seq} = L / f\_R$$
2. **Selettività media**: indica il numero medio di record che possiedono lo stesso valore per l'attributo di ricerca: $$S = L / m$$
3. **Costo Accesso Diretto con Indice Secondario ($C\_{dir}$)**: è la somma dei blocchi letti per attraversare l'indice e dei blocchi letti per recuperare i record corrispondenti (assumendo, nel caso peggiore di un indice non clusterizzato, un accesso al disco per ogni record trovato): $$C\_{dir} = p + (L / m)$$

### Concetti di efficienza e selettività

* **Campo molto selettivo ($m$ elevato)**: quando l'attributo ha molti valori distinti, il numero di record restituiti ($L/m$) è piccolo. In questo caso, l'accesso tramite indice è estremamente vantaggioso rispetto alla scansione sequenziale.
* **Campo poco selettivo ($m$ ridotto)**: quando un valore è molto comune nella base di dati, il numero di record da recuperare può superare il numero totale di blocchi del file ($L/m > L/f\_R$).
* **Punto di break-even**: l'indice smette di essere conveniente quando il costo dei "salti" casuali sul disco per recuperare i singoli record sparsi supera il costo della lettura lineare e contigua di tutti i blocchi della tabella.

