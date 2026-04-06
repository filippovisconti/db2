---
title: "TAGD-01-ai"
author:
  - Filippo Visconti
template:
  - template.tex
---

# Organizzazione fisica e gestione delle interrogazioni

L'architettura di un sistema di gestione di basi di dati (DBMS) è strutturata per gestire il flusso delle informazioni partendo dalle richieste ad alto livello fino alla memorizzazione fisica dei dati. Il processo ha inizio con il **Gestore delle interrogazioni**, che riceve istruzioni espresse in linguaggio SQL. Questo componente ha il compito di tradurre le query in operazioni eseguibili come la scansione delle tabelle, l'accesso diretto ai record o l'ordinamento dei dati. Una volta definito il piano d'azione, la richiesta passa al **Gestore dei metodi d'accesso**, il quale opera attraverso quella che viene definita lettura "virtuale". Questo livello a sua volta interagisce con il **Gestore del buffer**, che funge da intermediario per ottimizzare le prestazioni eseguendo letture fisiche attraverso il **Gestore della memoria secondaria**. Quest'ultimo è l'interfaccia finale che comunica direttamente con i dispositivi di **memoria secondaria**, dove i dati risiedono stabilmente.

La distinzione tra **memoria principale** e **memoria secondaria** è fondamentale per comprendere le prestazioni di un database. I programmi possono fare riferimento [esclusivamente]{.underline} a dati presenti nella memoria _principale_. Tuttavia, le basi di dati devono [necessariamente]{.underline} risiedere nella memoria _secondaria_ per due ragioni critiche: le dimensioni e la persistenza dei dati. Di conseguenza, ogni dato memorizzato su disco deve essere trasferito nella memoria principale per poter essere elaborato.

I dispositivi di memoria secondaria sono organizzati fisicamente in **blocchi** di lunghezza fissa, solitamente nell'ordine di alcuni KB. Specularmente, nella memoria centrale viene allocata un'area della stessa dimensione chiamata **pagina**. Le operazioni fondamentali sui dispositivi si limitano alla lettura di un blocco dal disco verso una pagina e alla scrittura di una pagina su un blocco del disco. Nella pratica tecnica, i termini "blocco" e "pagina" sono spesso usati come sinonimi. Il sistema operativo assegna un numero univoco a ogni blocco del disco, garantendo che ogni unità di memorizzazione abbia un indirizzo univoco all'interno del sistema di elaborazione.

Le prestazioni di un disco tradizionale (meccanico a rotazione) sono determinate da tre fattori temporali:

1. **Tempo di posizionamento della testina (seek time)**: il tempo necessario per muovere la testina sulla traccia corretta, mediamente compreso tra 4ms e 15ms.
2. **Tempo di latenza (rotational delay)**: il tempo necessario affinché il settore corretto ruoti sotto la testina, variabile tra 2ms e 8ms in base alla velocità di rotazione (da 4K a 15K giri al minuto).
3. **Tempo di trasferimento di un blocco**: il tempo effettivo di passaggio dei dati, che rappresenta solo una frazione di millisecondo data la velocità di trasferimento tra 100 e 600MB/s.

==Complessivamente, un accesso richiede mediamente non meno di qualche millisecondo.==

==Il costo di un accesso alla memoria secondaria è di quattro o più ordini di grandezza superiore rispetto alle operazioni in memoria centrale==: parliamo di millisecondi contro decimi o centesimi di microsecondo. Per questo motivo, ==nelle applicazioni definite "I/O bound", il costo totale dipende== quasi esclusivamente ==dal numero di accessi al disco==. È importante notare che leggere un singolo bit o un intero blocco ha lo **stesso** costo temporale. Inoltre, l'_accesso a blocchi contigui è meno oneroso_, specialmente se il disco esegue il _prefetching_, ovvero la lettura anticipata di intere tracce memorizzate in una cache interna.

Le **Unità a Stato Solido (SSD)** introducono caratteristiche differenti: essendo prive di parti meccaniche, **offrono un accesso diretto a costo uniforme**, risultando molto più veloci dei dischi tradizionali per gli accessi casuali. Tuttavia, il loro costo per gigabyte è ancora superiore e le prestazioni in scrittura tendono a peggiorare nel tempo poiché il **numero di riscritture è limitato** e il sistema deve distribuire i dati in posizioni diverse per preservare l'integrità delle celle. Nonostante la velocità superiore, l'accesso a un SSD resta comunque di vari ordini di grandezza più lento della RAM (decine o centinaia di microsecondi contro decimi o centesimi di microsecondo).

Il **File System** del sistema operativo gestisce la memoria secondaria tipicamente su due livelli:

* **Livello basso**: fornisce primitive per agire sui blocchi (leggi/scrivi un blocco in una pagina, alloca/dealloca blocchi contigui).
* **Livello alto**: gestisce i file come sequenze di caratteri o oggetti dotati di nome, struttura e una posizione corrente, offrendo primitive come il posizionamento (_seek_) e la lettura/scrittura in posizioni specifiche.

Un DBMS può interagire con il file system in diversi modi:

* **A livello di blocchi**: garantisce un controllo completo sul posizionamento fisico, permettendo di distribuire oggetti su più dispositivi. Lo svantaggio è l'estrema complessità amministrativa e la necessità di avere dischi dedicati esclusivamente al DBMS.
* **A livello di file**: è più **semplice** da realizzare (un file per ogni tabella), **ma il DBMS perde la visibilità sulla reale allocazione dei blocchi** e sul buffer, con un impatto negativo sulle prestazioni.
* **Soluzione intermedia**: è l'==approccio più frequente==. Il DBMS usa il file system in modo limitato per creare/eliminare file e gestire flussi di blocchi, ma mantiene il controllo diretto sull'organizzazione interna, decidendo come i record sono distribuiti nei blocchi e quale sia la struttura interna ai blocchi stessi.

Nella mappatura standard delle relazioni sui dischi, il DBMS gestisce lo spazio allocato come un unico grande contenitore virtuale di memoria secondaria. Vengono creati file di grandi dimensioni che possono ospitare l'intera base di dati o diverse relazioni. È possibile che un singolo file contenga dati di più relazioni o, viceversa, che le ennuple di una singola relazione siano distribuite su file diversi. All'interno di questo spazio, il DBMS costruisce le strutture fisiche necessarie. Sebbene non sia una regola assoluta, spesso ogni blocco è dedicato esclusivamente alle ennuple di un'unica relazione.

La gerarchia di mappatura segue un percorso articolato che collega il software all'hardware:

1. Dal lato del **sistema operativo**, si parte dai dischi reali, suddivisi in _extents_ che formano i dischi logici, i quali vengono infine visti come file del sistema operativo (OS-files).
2. Dal lato del **database system**, i file vengono organizzati in _tablespaces_, suddivisi in segmenti che contengono le effettive relazioni. Questa complessa interazione permette di astrarre la struttura logica delle tabelle dalla loro frammentazione fisica sui dispositivi di memorizzazione.

## La gestione del buffer e le metafore del lavoro d'ufficio

Per comprendere il funzionamento del buffer, è utile ricorrere a una metafora lavorativa. Si immagini che la **memoria secondaria** sia un grande classificatore di documenti situato in un'altra stanza. Per poter lavorare su un documento, esso deve essere necessariamente spostato sulla scrivania, che rappresenta la **memoria principale (RAM)**. Se un impiegato deve occuparsi di più argomenti contemporaneamente, terrà diverse cartelline sulla scrivania. Tuttavia, lo spazio sulla scrivania è limitato; a un certo punto la superficie si riempie e non è più possibile aggiungere nuovi documenti. In questa situazione, è necessario scegliere una cartellina da "rimettere a posto" nel classificatore per liberare spazio.

La scelta di quale documento rimuovere dalla scrivania segue delle **euristiche**. Idealmente, si vorrebbe eliminare il documento che non servirà nel prossimo futuro. Poiché non è possibile prevedere il futuro, si assume che il documento non utilizzato da più tempo sia quello meno probabile da richiedere a breve. Una metafora alternativa è quella dell'**armadio**: quando si ripone un vestito, lo si inserisce all'estremità destra dell'asta. In questo modo, le cose usate più di recente si accumulano a destra, mentre i vestiti non utilizzati (come i giubbetti estivi a fine inverno) finiscono progressivamente verso l'estremità sinistra. Se serve spazio per un nuovo acquisto, si dismette il vestito che si trova all'estremità sinistra, ovvero quello non utilizzato da più tempo.

## Dettagli tecnici del Buffer Management

Il **Buffer** è un'area di memoria centrale preallocata e gestita direttamente dal DBMS, condivisa tra tutte le transazioni attive. È organizzato in **pagine**, le cui dimensioni sono pari o multiple di quelle dei blocchi della memoria secondaria, tipicamente comprese tra $1KB$ e $100KB$. È fondamentale distinguere il buffer del DBMS dalla cache del disco, che è una memoria interna al dispositivo hardware gestita dal controller del disco stesso.

Lo scopo primario del buffer manager è ridurre il numero di accessi alla memoria secondaria, data l'enorme differenza di velocità tra RAM e disco. In fase di lettura, se la pagina richiesta è già presente nel buffer, l'accesso fisico viene evitato. In fase di scrittura, il gestore può decidere di differire l'operazione fisica sul disco, accumulando le modifiche in memoria (salvo restrizioni legate alla gestione dell'affidabilità). Questo sistema sfrutta il principio della **località dei dati**: esiste un'alta probabilità di riutilizzare dati che sono stati acceduti di recente.

Per gestire questa struttura, il DBMS mantiene un **direttorio** (una tabella di controllo) che per ogni pagina memorizza:

1. Un identificatore fisico del blocco (nome del file e numero del blocco o indirizzo fisico).
2. Un **contatore di pin**: un intero che indica quanti programmi o transazioni stanno attualmente utilizzando quella pagina. Una pagina con contatore maggiore di zero è "fissata" e non può essere rimossa.
3. Un **dirty bit** (booleano): indica se la pagina è "sporca", ovvero se è stata modificata in memoria ma non ancora riportata su disco.

## L'interfaccia del Buffer Manager

Le operazioni fondamentali offerte dal buffer manager sono:

* **pin**: richiesta di un blocco. Se il blocco non è nel buffer, viene eseguita una lettura fisica. Il sistema restituisce l'indirizzo della pagina e incrementa il contatore di pin.
* **setDirty**: comunica che la pagina è stata modificata.
* **unpin**: comunica che il programma ha terminato l'uso della pagina, permettendo al gestore di decrementare il contatore.
* **flush**: forza il trasferimento sincrono di una pagina sporca sulla memoria secondaria.

Durante l'esecuzione di una `fix`, il gestore cerca la pagina nel buffer. Se non la trova, deve cercare una pagina "libera" (con contatore a zero). Se la pagina scelta per il rimpiazzo è "sporca", deve prima salvarla su disco. Se non ci sono pagine con contatore a zero, il sistema può seguire due politiche:

* **No-steal**: l'operazione viene posta in attesa finché una pagina non viene liberata.
* **Steal**: viene selezionata una "vittima" anche tra le pagine occupate, scrivendone i dati su disco se sporca (questo approccio è più complesso e spesso evitato nelle implementazioni semplificate).

Le scritture su disco possono quindi essere **sincrone** (richieste esplicite di flush) o **asincrone** (decise dal gestore per liberare spazio o per ottimizzare le prestazioni del dispositivo sfruttando i tempi morti).

## Strategie di rimpiazzo

Quando è necessario caricare un nuovo blocco e il buffer è pieno di pagine non utilizzate, bisogna scegliere quale sacrificare. Le strategie principali sono:

* **Naive**: sceglie la prima pagina libera incontrata nella scansione.
* **FIFO (First-In-First-Out)**: sostituisce la pagina che è stata caricata da più tempo.
* **LRU (Least Recently Used)**: sostituisce la pagina che è stata utilizzata meno di recente. È la strategia che meglio approssima la previsione del futuro basandosi sul passato.
* **Clock**: esegue una scansione circolare partendo dalla posizione successiva all'ultimo rimpiazzo, offrendo un'approssimazione efficiente della LRU.

## Organizzazione dei record nei blocchi

Un file è ==composto logicamente da **record**== (ennuple) ma è ==organizzato fisicamente in **blocchi**.== Poiché le dimensioni di questi due elementi sono solitamente diverse, è necessario gestire la loro mappatura. I record possono essere a **lunghezza fissa** o **variabile**. I blocchi possono essere **omogenei** (record di una sola relazione) o **eterogenei** (record di relazioni diverse, utile per ottimizzare i join fisici).

Se un record è interamente contenuto in un blocco, si parla di organizzazione **unspanned**. Se un record può essere diviso tra più blocchi, si parla di **spanned**. In caso di record a lunghezza fissa $L_R$ e blocchi di dimensione $L_B$, il ==**fattore di blocco**== (numero di record per blocco) è calcolato come: ==$f = \lfloor L_B / L_R \rfloor$==.

L'organizzazione interna di una pagina prevede solitamente un **dizionario di pagina** e una **parte utile**. Una struttura comune prevede due stack che crescono in direzioni opposte: uno stack per il dizionario (puntatori alle ennuple $*t1, *t2, \dots$) e uno stack per i dati effettivi ($t1, t2, \dots$). Questo permette di gestire record di lunghezza variabile. La pagina include anche informazioni di controllo della struttura fisica e del file system, oltre a un bit di parità per il controllo degli errori.

## Strutture fisiche e file disordinati

Le strutture fisiche si dividono in:

* **Primarie**: definiscono come i record sono organizzati nel file.
* **Secondarie**: strutture ausiliarie (come gli indici) per velocizzare l'accesso.

Le tipologie principali sono:

* sequenziali,
* calcolate (Hash),
*  o ad albero.

> Tra le sequenziali, la più semplice è la **struttura disordinata** (chiamata anche file seriale, ==heap== o "entry sequenced"). In questa organizzazione, non esiste un ordine logico: i nuovi record vengono inseriti solitamente in coda o occupando i "vuoti" lasciati da cancellazioni precedenti.

Le operazioni su un file disordinato includono la scansione (`beforeFirst`, `next`), la lettura di campi (`getInt`, `getString`) e l'aggiornamento (`setInt`, `insert`, `delete`). ==L'implementazione della `next` verifica se nel blocco corrente ci sono altri record; in caso negativo, passa al primo record del blocco successivo==. Il costo di ricerca e inserimento in un file disordinato è **lineare** rispetto al numero di blocchi del file, rendendolo inefficiente per basi di dati di grandi dimensioni senza l'ausilio di indici secondari. Sebbene l'inserimento potrebbe sembrare $O(1)$ scrivendo in coda, ==la necessità di verificare vincoli di integrità== (come l'unicità della chiave) ==richiede comunque una scansione completa==, riportando il costo a $O(N)$.

# Strutture ordinate

In un sistema di gestione di basi di dati, l'organizzazione fisica dei record può seguire criteri logico-matematici precisi per ottimizzare il reperimento delle informazioni. Una delle modalità fondamentali è la **struttura ordinata**, in cui ogni record, ovvero ogni ennupla della relazione, occupa una posizione fisica specifica determinata dal valore di un particolare campo. Questo campo viene definito **pseudochiave**, poiché funge da criterio di ordinamento ma non è necessariamente una chiave primaria in senso logico.

L'adozione di una struttura ordinata comporta sfide significative per quanto riguarda la manutenzione della coerenza durante le operazioni di modifica. Gli **aggiornamenti** richiedono spesso interventi strutturali pesanti: l'inserimento di un nuovo record non può avvenire semplicemente in coda al file (come in una struttura heap), ma deve rispettare la posizione prevista dal criterio di ordinamento. Ad esempio, inserendo il record "66 Bruni Marco" in una tabella ordinata per cognome, il sistema deve individuare la posizione corretta (tra Bianchi e Neri) e traslare fisicamente tutti i record successivi per creare lo spazio necessario. Lo stesso problema si presenta con campi a lunghezza variabile quando un valore viene aggiornato con una stringa più lunga della precedente, causando uno slittamento dei record contigui.

Per gestire queste inefficienze, si adottano diverse strategie, spesso combinate tra loro:

* **Riorganizzazione immediata**: il file viene riscritto istantaneamente per mantenere l'ordine perfetto, operazione molto costosa in termini di I/O.
* **Spazio inizialmente ridondante**: si lasciano spazi vuoti (_padding_) all'interno dei blocchi per ospitare futuri inserimenti senza causare slittamenti immediati.
* **Inserimenti in coda o in blocchi di overflow**: i nuovi record vengono temporaneamente memorizzati in un'area separata e collegati alla posizione corretta tramite puntatori.
* **Riorganizzazioni periodiche**: il sistema esegue ciclicamente una manutenzione globale del file per ricompattare i dati ed eliminare le aree di overflow.

Sebbene le strutture ordinate permettano teoricamente l'uso della **ricerca binaria**, la loro applicazione pratica nei DBMS è limitata. La difficoltà risiede nella struttura fisica dei file: come si individua esattamente la "metà" di un file memorizzato su disco per poi procedere ricorsivamente? Per tale ragione, nelle basi di dati relazionali, queste strutture vengono utilizzate quasi esclusivamente in combinazione con gli indici, dando vita ai file **ISAM** (_Indexed Sequential Access Method_) o a file ordinati dotati di un indice primario. Restano comunque strumenti preziosi quando è necessario fornire risultati già ordinati all'utente o come fase preparatoria per operazioni costose come il merge-join.

# File Hash
Una tecnica radicalmente differente per l'accesso efficiente ai dati è rappresentata dai **File Hash**. Questa organizzazione mira a fornire un accesso diretto o associativo basato sul valore di un campo di ricerca. Questa tecnica traspone sul disco i concetti delle **tavole hash** utilizzate nella memoria centrale.

==L'obiettivo di una tavola hash è l'accesso diretto a un record tramite il valore di una chiave.== Se lo spazio dei possibili valori della chiave è paragonabile al numero di record effettivi (ad esempio, 1000 studenti con matricole da 1 a 1000), è possibile utilizzare un semplice array dove l'indice corrisponde alla chiave. Tuttavia, quando i possibili valori sono molto più numerosi di quelli utilizzati (ad esempio, 40 studenti con matricole a 6 cifre, che generano un milione di combinazioni potenziali), l'uso di un array diretto causerebbe un enorme spreco di memoria.

La soluzione consiste nell'utilizzare una **funzione hash**, che associa a ogni valore della chiave un "indirizzo" in uno spazio di dimensione contenuta, paragonabile al numero di record da memorizzare. Poiché lo spazio delle chiavi è vasto e quello degli indirizzi è limitato, la funzione [non]{.underline} può essere iniettiva, rendendo inevitabili le **collisioni** (ovvero quando chiavi diverse corrispondono allo stesso indirizzo). Una buona funzione hash deve distribuire i valori in modo casuale e uniforme per minimizzare tali eventi. Un esempio didattico è la funzione modulo: $K \pmod{n}$, dove $n$ è la dimensione della tavola.

Analizziamo un esercizio numerico con 8 record dotati delle seguenti chiavi: 240772, 240810, 449726, 447004, 453900, 281425, 281267, 405154. Utilizzando una tavola hash con 10 posizioni e la funzione $K \pmod{10}$, la distribuzione risulta:

* Posizione 0: ospita 240810, ma collide con 453900.
* Posizione 2: ospita 240772.
* Posizione 4: ospita 447004, ma collide con 405154.
* Posizione 5: ospita 281425.
* Posizione 6: ospita 449726.
* Posizione 7: ospita 281267.

> Le chiavi 453900 e 405154 rimangono inizialmente "escluse" dalla tavola principale.

Per la **gestione delle collisioni**, si impiegano diverse tecniche:

1. **Posizioni successive disponibili**: si cerca il primo slot libero dopo quello calcolato.
2. **Tabella di overflow**: i record collidenti vengono inseriti in un'area separata gestita tramite liste collegate.
3. **Funzioni hash alternative**: si applica una seconda funzione in caso di collisione.

==Il "costo" di queste strutture viene valutato in termini di accessi medi.== In un esempio con 40 record e una tavola da 50 posizioni, si potrebbero avere 20 record senza collisioni, 5 gruppi di collisioni da 2 record, 2 gruppi da 3 e 1 gruppo da 4. Il numero medio di accessi si calcola come: $(28 \times 1 + 8 \times 2 + 3 \times 3 + 1 \times 4) / 40 = 1,425$. Sebbene le collisioni siano quasi sempre presenti, la probabilità di collisioni multiple decresce rapidamente al crescere della loro numerosità, mantenendo la molteplicità media molto bassa.

Il concetto si estende al **File Hash** organizzato per blocchi. Qui, ogni "indirizzo" della funzione hash punta a un intero blocco che può contenere più record (fattore di blocco $F$). Lo spazio degli indirizzi si riduce: se $F = 10$, per 50 posizioni totali si possono usare solo 5 blocchi (funzione $\pmod{5}$ invece di $\pmod{50}$). Le collisioni che eccedono la capacità del blocco (_overflow_) sono tipicamente gestite tramite il collegamento di nuovi blocchi.

Il confronto tra file hash normale e file hash organizato in blocchi mostra che quest'ultimo è più efficiente. Con 40 record:

* File hash (50 posizioni): 12 record in overflow, costo medio 1,425.
	* File hash (5 blocchi da 10): solo 2 record in overflow, costo medio 1,05.
		* Questa efficienza superiore deriva dal fatto che il blocco funge da "ammortizzatore" per le collisioni locali.

Le stime statistiche confermano che all'aumentare del fattore di blocco $F$, la lunghezza media delle catene di overflow e il costo di accesso diminuiscono drasticamente, anche con coefficienti di riempimento elevati. Ad esempio, con un riempimento del $90\%$ ($T/(F \times B) = 0.9$):

* Se $F = 1$, il costo è $5,495$.
* Se $F = 10$, il costo scende a $1,345$.

> Il file hash è l'==organizzazione più efficiente per l'accesso puntuale==, con un costo medio vicino all'unità. Tuttavia, ==non è adatto a ricerche per intervalli e tende a degradare se lo spazio diventa saturo==. Per ovviare alla rigidità delle dimensioni, si ricorre a tecniche di **hashing dinamico**, come l'hashing estendibile o lineare, che permettono al file di adattarsi alla variazione del numero di record nel tempo.

## Analisi delle collisioni e organizzazione delle strutture di accesso

L'efficienza di un file hash è strettamente legata alla gestione delle collisioni e alla lunghezza delle catene di overflow. La stima della lunghezza media di queste catene varia in funzione di quattro parametri fondamentali: il numero totale di record esistenti ($T$), il numero di blocchi allocati ($B$), il fattore di blocco ($F$) e il coefficiente di riempimento, definito dal rapporto $T/(F \times B)$. All'aumentare del coefficiente di riempimento, la probabilità di collisione cresce, influenzando direttamente il costo di accesso.

Dalle analisi statistiche emerge che, mantenendo un coefficiente di riempimento costante, un fattore di blocco $F$ più elevato riduce drasticamente la lunghezza media delle catene di overflow. In generale, un file hash ben progettato mantiene un costo medio di poco superiore all'unità. Sebbene il caso peggiore teorico sia estremamente costoso, la sua probabilità statistica è talmente bassa da poter essere ignorata nelle applicazioni reali.

## Hashing estendibile

L'hashing _estendibile_ supera la rigidità delle strutture statiche poiché il ==numero di blocchi (o bucket) **non** è predefinito==. Questa tecnica utilizza una [directory dei blocchi che può variare di dimensione]{.underline}, sebbene solitamente cresca in modo lento. Il sistema si basa sulla rappresentazione binaria del valore di hash ottenuto dalla chiave.

Le caratteristiche tecniche prevedono:

* Una funzione hash che produce valori di $k$ bit (dove $k$ può essere un numero molto grande).
* Una directory composta da $2^d$ elementi, dove $d$ rappresenta la profondità globale dell'indice ($d \leq k$).
* Un numero di blocchi fisici generalmente inferiore a $2^d$, poiché più elementi della directory possono puntare allo stesso blocco fisico.
* Una profondità locale associata a ogni blocco, che indica il numero di bit iniziali comuni ai record contenuti o potenzialmente inseribili in quel blocco.

La dinamica di inserimento prevede che, se un blocco si satura, esso venga diviso in due. In questa circostanza, se la profondità locale del blocco è inferiore alla profondità globale, è sufficiente aggiornare i puntatori nella directory. Se invece la profondità locale è uguale alla profondità globale, il blocco è l'unico a essere riferito da quell'elemento della directory; per permettere la divisione, è necessario raddoppiare la dimensione della directory incrementando $d$ di una unità.

Si consideri un esempio con profondità globale $d=2$. La directory ha $2^2=4$ elementi (identificati dai bit $00, 01, 10, 11$). Se un blocco ha profondità locale $1$, significa che risponde a più voci della directory (ad esempio $00$ e $01$ puntano allo stesso blocco perché condividono il primo bit $0$). Se inseriamo un record il cui hash inizia con $01010 \dots$ e il blocco corrispondente (che contiene già record come $00000 \dots, 00100 \dots, 01000 \dots$) è pieno, il blocco viene diviso. I record vengono ridistribuiti: quelli che iniziano con $00$ restano nel blocco originale, quelli che iniziano con $01$ (incluso il nuovo record) passano a un nuovo blocco. Entrambi i blocchi avranno ora profondità locale $2$. Se si tentasse di dividere un blocco che ha già profondità locale $2$ (uguale alla globale), come quello contenente record che iniziano con $11$, la directory verrebbe raddoppiata portando la profondità globale a $3$ e la directory a $8$ elementi ($000, 001, \dots, 111$).

Il costo dell'hashing estendibile prevede un accesso aggiuntivo per la directory. Il costo di riferimento è dunque pari a due (directory più blocco), più le riorganizzazioni che, essendo rare, mantengono la media di poco superiore a due. Se la directory è frequentemente utilizzata e risiede nel buffer, il costo si avvicina all'unità.

# Indici di file e strutture di accesso

Le strutture fisiche si dividono in primarie (che determinano il posizionamento fisico dei record, come i file disordinati, ordinati o hash statici) e secondarie (elementi ausiliari per l'accesso efficiente). Un indice è una struttura ausiliaria che permette l'accesso ai record di un file $F$ basandosi sui valori di una pseudochiave (campo non necessariamente identificante).

Un indice $I$ è a sua volta un file composto da record a due campi: la chiave e l'indirizzo (del record o del blocco in $F$). L'indice è sempre ordinato secondo i valori della chiave. Si distinguono due tipologie principali:

* **Indice Primario**: definito su un campo che rispetta l'ordinamento fisico della memorizzazione del file (detto anche indice di cluster). ==Esiste al più un indice primario per file.==
* **Indice Secondario**: definito su un campo il cui ordinamento è diverso da quello di memorizzazione. Un file può avere molteplici indici secondari.

Un'ulteriore distinzione riguarda la copertura dei valori:

* **Indice Denso**: contiene un riferimento per ogni singolo valore della chiave presente nel file. Gli indici **secondari** devono **necessariamente essere densi**.
* **Indice Sparso**: contiene riferimenti solo per alcuni valori della chiave (solitamente uno per ogni blocco del file). Un indice primario è solitamente sparso per risparmiare spazio, ma può essere denso per velocizzare verifiche di esistenza senza accedere al file dati.

Negli indici densi si possono usare puntatori ai blocchi (più compatti) o puntatori ai record. Questi ultimi permettono di eseguire alcune operazioni (come conteggi o verifiche) direttamente sull'indice senza accedere al file principale. Se la pseudochiave non è identificante (più record con lo stesso valore), l'indice primario sparso può puntare solo ai blocchi con valori "nuovi", mentre l'indice secondario può gestire la duplicazione dei valori della chiave ripetendo la coppia (chiave, riferimento) o utilizzando un livello di indirezione con liste di puntatori.

## Dimensioni dell'indice

Sia $L$ il numero di record, $B$ la dimensione del blocco, $R$ la lunghezza del record, $K$ la lunghezza della chiave e $P$ la lunghezza dell'indirizzo. Si definiscono le seguenti formule:

* Fattore di blocco del file: $B/R$
* Numero di blocchi del file: $N_F = L / (B/R)$
* Fattore di blocco dell'indice: $B/(K+P)$
* Numero di blocchi per un indice denso: $N_D = L / (B/(K+P))$
* Numero di blocchi per un indice sparso: $N_S = N_F / (B/(K+P))$

Considerando un esempio con $L = 1.000.000$, $B = 4KB$, $R = 100B$, $K = 4B$ e $P = 4B$, otteniamo:

* Fattore di blocco $B/R = 40$ record per blocco.
* Numero di blocchi $N_F = 1.000.000 / 40 = 25.000$ blocchi.
* Fattore di blocco dell'indice $B/(K+P) = 4000 / 8 = 500$ record indice per blocco.
* $N_D = 1.000.000 / 500 = 2.000$ blocchi.
* $N_S = 25.000 / 500 = 50$ blocchi.

L'indice sparso risulta significativamente più piccolo ($50$ blocchi contro i $25.000$ del file), facilitando enormemente la ricerca. Gli indici garantiscono un accesso diretto efficiente (puntuale e per intervalli) e una scansione sequenziale ordinata. Tuttavia, rendono inefficienti le modifiche, gli inserimenti e le eliminazioni a causa della rigidità dell'ordinamento. Per mitigare questi problemi si utilizzano blocchi di overflow, marcature per l'eliminazione (_tombstones_), riempimento parziale o riorganizzazioni periodiche.

## Indici multilivello e B-tree

Poiché gli indici sono file ordinati, è possibile costruire indici sugli indici per evitare scansioni sequenziali tra i blocchi dell'indice stesso. Questo crea una struttura multilivello dove l'indice di livello superiore è sempre primario e sparso rispetto a quello inferiore. Il processo prosegue fino a ottenere un livello composto da un solo blocco (la radice).

Il numero di blocchi al livello $j$ è dato da: $N_j = N_{j-1} / (B/(K+P))$.
Il numero di blocchi a cui un blocco fa riferimento è detto _fan-out_. 
Negli indici multilivello la profondità è solitamente ridotta (tra 3 e 5). 

>Con un fan-out di $500$, un indice denso di $2.000$ blocchi richiede solo 3 livelli ($N_1=2000, N_2=4, N_3=1$), mentre uno sparso di $50$ blocchi ne richiede solo 2 ($N_1=50, N_2=1$).

I DBMS moderni utilizzano strutture più sofisticate come i **B-tree** per gestire l'elevata dinamicità. Un B-tree è un albero di ricerca bilanciato in cui ogni nodo corrisponde a un blocco. Caratteristiche principali:

* Mantenimento del perfetto bilanciamento (foglie allo stesso livello).
* Riempimento parziale dei nodi (mediamente $70\%$, con un minimo garantito del $50\%$).
* In un albero di ordine $P$, ogni nodo ha fino a $P$ figli e $P-1$ etichette ordinate.
* L'i-esimo sottoalbero contiene chiavi $K$ tali che $K_{i-1} \leq K < K_i$.

Negli inserimenti, se una foglia è piena, avviene uno **split** (divisione del nodo) che può propagarsi verso l'alto fino alla radice. Le eliminazioni possono causare un **merge** (fusione di nodi) se il riempimento scende sotto la soglia.

Si distinguono due varianti:

1. **B+ tree**: ==Tutte le chiavi e i riferimenti ai dati compaiono nelle foglie==. Le **foglie** sono **collegate** tra loro in una lista per ottimizzare le ricerche su intervalli. I nodi intermedi contengono solo chiavi per guidare la ricerca. È la struttura più usata nei DBMS.
2. **B tree**: ==Le chiavi e i riferimenti ai dati possono trovarsi **anche** nei nodi intermedi== e non vengono ripetuti nelle foglie.

Il costo di ricerca in queste strutture è pari alla profondità dell'albero. Grazie alla bufferizzazione della radice e dei primi livelli, il costo reale di un accesso diretto scende spesso a soli $2$ o $3$ accessi fisici.

# Esecuzione delle interrogazioni

L'esecuzione e l'ottimizzazione delle interrogazioni sono affidate al **Query Processor**, o Ottimizzatore. La necessità di questo modulo deriva dal concetto di ==indipendenza dei dati==: le interrogazioni SQL descrivono insiemi di ennuple con pochissima proceduralità, lasciando al sistema il compito di scegliere la migliore strategia realizzativa tra diverse alternative possibili. Il **processo di esecuzione** si articola in fasi **sequenziali**:

1. **Analisi lessicale, sintattica e semantica**: trasforma il codice SQL in un'espressione algebrica, verificando la correttezza rispetto allo schema contenuto nel **Catalogo**.
2. **Ottimizzazione algebrica**: applica trasformazioni all'espressione algebrica per renderla più efficiente.
3. **Ottimizzazione basata sui costi**: trasforma l'espressione algebrica ottimizzata in un **piano di accesso** (o piano di esecuzione), consultando le strutture fisiche e i profili delle relazioni memorizzati nel Catalogo.

Il **Catalogo** contiene i cosiddetti "Profili" delle relazioni, ovvero informazioni quantitative aggiornate periodicamente (tramite comandi come `update statistics`). Tali profili includono la cardinalità di ciascuna relazione, le dimensioni delle ennuple e dei singoli valori, il numero di valori distinti degli attributi e i valori minimi e massimi. Questi dati sono fondamentali nella fase finale dell'ottimizzazione per stimare i costi delle operazioni e le dimensioni dei risultati intermedi.

## Dall'SQL all'algebra e ottimizzazione euristica

Un'interrogazione SQL viene semplificata nei suoi componenti fondamentali: il prodotto cartesiano (clausola `FROM`), la selezione (clausola `WHERE`) e la proiezione (clausola `SELECT`). 

Ad esempio, la query: `SELECT A , E FROM R1, R3, R2 WHERE C=D AND B=20 AND F=G AND I>2` può essere tradotta nel predicato algebrico: $\pi_{AE}(\sigma_{C=D \wedge B=20 \wedge F=G \wedge I>2}((R1 \bowtie R2) \bowtie R3))$

Le interrogazioni vengono rappresentate graficamente tramite **alberi**, dove le foglie sono i dati (relazioni o file) e i nodi intermedi sono gli operatori (prima algebrici, poi operatori di accesso effettivi). L'ottimizzazione algebrica utilizza euristiche basate sulla nozione di equivalenza: due espressioni sono equivalenti se producono lo stesso risultato per ogni istanza della base di dati. Il ==DBMS cerca l'espressione equivalente meno costosa== seguendo l'euristica fondamentale di eseguire selezioni e proiezioni il prima possibile per ridurre le dimensioni dei risultati intermedi. Questo concetto è noto come "==push selections down==" e "push projections down".

Le regole specifiche per l'ottimizzazione algebrica includono:

* Decomporre le selezioni congiuntive in selezioni atomiche successive.
* ==Anticipare il più possibile le selezioni, specialmente le più selettive.==
* ==Combinare prodotti cartesiani e selezioni per formare join, riordinando se necessario gli operandi==.
* ==Anticipare le proiezioni==, anche introducendone di nuove, per limitare la dimensione dei record nei risultati intermedi (particolarmente utile se i risultati vengono materializzati).

## Esecuzione delle operazioni 

I DBMS offrono operatori fisici che implementano gli operatori algebrici. Gli operatori fondamentali sono la **scansione** e l'**accesso diretto**, seguiti da operazioni di livello più alto come l'_ordinamento_ e il _join_.

==La **Scansione** consiste nell'accesso sequenziale a una tabella.== Permette la lettura completa, la selezione su qualunque predicato, la proiezione (senza eliminazione di duplicati) e la gestione delle ennuple correnti (inserimento, modifica, eliminazione). I metodi offerti sono `open`, `next`, `read`, `modify`, `insert`, `delete` e `close`. ==Il **costo** è **lineare** rispetto al **numero di blocchi** del file==, ovvero $O(N)$.

==L\'**Accesso diretto** è possibile **solo** se supportato da strutture fisiche come indici o hash.== L'accesso basato su indice è utile per selezioni puntuali ($A_{i}=v$) o su intervallo ($v_{1} \leq A_{i} \leq v_{2}$), a patto che l'indice sia selettivo (ossia che il risultato contenga poche ennuple rispetto alla relazione di partenza). ==Il **costo** ha **due** componenti: la _profondità dell'indice_ (logaritmica) e l\'_accesso ai record effettivi_== (che dipende dalla selettività). 

In caso di **selezione congiuntiva** (AND) con più indici disponibili, il sistema può usare l'indice più selettivo e valutare l'altra condizione successivamente, oppure usare entrambi gli indici per ottenere liste di indirizzi ed eseguirne l'intersezione. Se gli indirizzi sono ai record, l'intersezione identifica esattamente i record cercati; se sono ai blocchi, identifica i blocchi potenzialmente utili. 

Per la **selezione disgiuntiva** (OR), **se entrambi i campi sono selettivi e indicizzati**, si esegue l'**unione** dei risultati; **se anche uno solo non è selettivo**, l'uso dell'indice è **inutile** e si preferisce la scansione sequenziale.

Il costo degli indici su campi _non chiave_ è composto dalla profondità dell'indice e il costo dell'accesso ai record:

* **Indice secondario**: i record sono sparpagliati, quindi potrebbe servire **un accesso per ogni record trovato**.
* **Indice primario**: i ==record sono fisicamente consecutivi==, quindi il **costo** è approssimativamente pari al **numero di record** trovati **diviso il fattore di blocco**.

L'**Accesso diretto basato su hash** è estremamente efficiente per interrogazioni puntuali, con un costo approssimabile a una costante, ma **non** per ricerche su intervallo. Per predicati congiuntivi e disgiuntivi, vale lo stesso discorso fatto per gli indici.

## Ordinamento e Merge-Sort esterno

L'ordinamento è un'operazione cruciale per produrre risultati ordinati (`ORDER BY`), eliminare duplicati (`DISTINCT`), preparare raggruppamenti (`GROUP BY`) o join. Poiché le basi di dati spesso superano la dimensione della memoria principale, si utilizza il **Merge-sort esterno**.

L'algoritmo tradizionale con tre buffer (due di input e uno di output) segue un approccio "bottom-up":

1. Si divide il file in porzioni che entrano in memoria.
2. Si ordina ogni porzione in memoria e la si scrive su disco (creazione dei _run_).
3. Si fondono (_merge_) le porzioni a coppie fino a ordinare l'intero file.

Il costo complessivo per un file di $N$ blocchi è circa $2 \times N \times \log_{2}N$ accessi al disco, poiché ogni passo di merge richiede di leggere e scrivere l'intero file.

==Se è disponibile molta memoria (molte pagine di buffer $P$), le prestazioni migliorano riducendo il **numero di passi** di merge==. Inizialmente si ordinano run composti da $P$ blocchi. Successivamente, si esegue un **merge a più vie**, fondendo contemporaneamente tante porzioni quante sono le pagine del buffer disponibili. Con $P$ buffer, è possibile ordinare un file in:

* Una passata se $P \geq N$.
* Due passate se $P^{2} \geq N$ (ovvero $P \geq \sqrt{N}$).
	* In questo caso ha un ==costo di $3 \times N$==.
	* Si legge il file, lo si scrive ordinato in run, si rilegge per il merge finale senza memorizzare il risultato intermedio.
* Tre passate se $P^{3} \geq N$. 

==In generale, con $i$ passate si può ordinare un file di $P^{i}$ blocchi. Il numero di passate necessario è il più piccolo intero $i$ per cui $P \geq \sqrt[i]{N}$.==

Ad esempio, per un file di $N=10.000.000$ di blocchi con un buffer di $10.000$ pagine ($100MB$), si potrebbero ordinare $10.000$ blocchi alla volta ottenendo $1000$ porzioni ordinate. Fondendo queste porzioni con un merge a $1000$ vie, l'ordinamento si completerebbe in un unico passo di merge (due passate totali). 

> In sintesi, ==se $P \geq \sqrt{N}$, l'operazione richiede $3 \times N$ accessi==.

> Vedere Esercizio 5 di [[26/02/2013]{.underline}](https://tagd.inf.uniroma3.it/compitiPDF/20130226bdIIsoluz.pdf)

# Algoritmi di Join

I sistemi di gestione di basi di dati (DBMS) sono progettati per tradurre le interrogazioni logiche in operazioni fisiche attraverso una gerarchia di operatori. Alla base di questa struttura si collocano gli operatori fondamentali di scansione e accesso diretto, seguiti dall'ordinamento. ==Al vertice della complessità computazionale si trova il join== ($R⋈S$), descritto come l'operatore più interessante, caratteristico e oneroso dell'algebra relazionale. Il costo di questa operazione è dominato dal tempo di calcolo e, soprattutto, dagli accessi alla memoria secondaria (I/O). Per ottimizzare il processo, l'ottimizzatore seleziona la metodologia fisica più adatta in base alle strutture di supporto (indici), alla dimensione dei buffer disponibili e alla selettività della query. Le tre strategie principali analizzate sono:

1. nested-loop join,
2. merge-join,
3. hash-join.

## Nested-loop Join

Il nested-loop join, o join a cicli annidati, rappresenta l'approccio più intuitivo e generale per l'esecuzione di un join. Il principio fondamentale consiste nell'esaminare tutte le coppie di ennuple dei due operandi per verificare la condizione di join. Il sistema distingue operativamente tra una "Tabella esterna" e una "Tabella interna". La procedura prevede l'esecuzione di una scansione della prima relazione: **per ogni ennupla identificata** (ad esempio, un record con valore del campo di join pari ad 'a'), **viene attivata una procedura di ricerca sulla tabella interna**, che può risolversi in una **scansione** completa o in un **accesso diretto** tramite indici.

### Nested-loop senza indice

==In assenza di indici, il join richiede la scansione sequenziale dei blocchi==. Poiché il costo del processamento in memoria centrale è trascurabile rispetto alla lettura dei blocchi dal disco, l'algoritmo opera a livello di blocco. In uno scenario minimale con soli due buffer a disposizione, il sistema carica un blocco della relazione esterna R1​ e lo confronta con ogni blocco della relazione interna R2​ caricato sequenzialmente. 
Per ogni blocco di $R_{1}$, l'intera relazione $R_{2}$ viene scansionata integralmente. Il ==costo totale== in termini di accessi alla memoria secondaria per relazioni composte da $B_{1}$ e $B_{2}$ blocchi ==è espresso dalla formula: $B_{1}+B_{1} \times B_{2}$==.

L'efficienza migliora drasticamente aumentando il numero di pagine di buffer $P$. Dedicando $B$ pagine di buffer alla relazione esterna $R_{1}$, il sistema può caricare contemporaneamente $B$ blocchi. Durante una singola scansione di $R_{2}$, ogni ennupla letta viene confrontata con tutte le ennuple degli $B$ blocchi di $R_{1}$ residenti in memoria, riducendo il numero di scansioni della tabella interna di un fattore $B$. ==Il costo ottimizzato è: $N_{1}+(N_{1}/B \times N_{2})$==.

Considerando un esempio numerico con $R_{1}$ composto da $N_{1}=1000$ blocchi, $R_{2}$ da $N_{2}=500$ blocchi e un buffer con $P=101$ pagine:

* Senza buffer grandi (leggendo un blocco alla volta): $1000+1000 \times 500 = 501.000$ accessi.
* Con buffer (dedicando $B=100$ pagine a $R_{1}$): $1000+(1000/100 \times 500) = 1000+10 \times 500 = 6000$ accessi.

### Nested-loop con indice

==Se la tabella interna dispone di un indice sul campo di join, la **scansione** sequenziale viene **sostituita da un accesso diretto**==. Per ogni ennupla della relazione esterna $R_{1}$, il sistema interroga l'indice di $R_{2}$. 

Il ==costo== dell'algoritmo base con $L_{1}$ ennuple in $R_{1}$ e un indice di profondità $I_{2}$ ==è: $N_{1}+L_{1} \times (I_{2}+1)$.== Se il buffer **mantiene stabilmente i livelli più alti dell'indice** (radice e primo livello intermedio), poiché utilizzati ripetutamente per ogni ricerca, il costo si riduce: $N_{1}+L_{1} \times (I_{2}-2+1)$.

## Merge-join e ottimizzazione dell'ordinamento

==Il merge-join sfrutta l'ordinamento fisico dei dati.== Se **entrambi** i file sono ordinati sul campo di join, il sistema esegue **due scansioni parallele** (scan sinistro e scan destro). I puntatori avanzano in modo coordinato confrontando i valori correnti: se un valore è inferiore all'altro, il relativo puntatore avanza; se sono uguali, viene prodotto il risultato del join.
I costi variano sensibilmente in base allo stato dei file:

* **File già fisicamente ordinati**: il ==costo è la somma dei blocchi==, $N_{1}+N_{2}$.
* **File disordinati (ordinamento a due passate)**: il ==costo è $3 \times (N_{1}+N_{2})$.== L'ottimizzazione consiste nell'eseguire la prima passata di ordinamento (creazione dei run) per entrambi i file e integrare la seconda passata (merge) direttamente con l'operazione di join.
* **File disordinati con indici**: il ==costo è circa $L_{1}+L_{2}$ più il costo della scansione delle foglie degli indici==.

## Hash-join e partizionamento in Bucket

==L'hash-join applica una funzione hash ai campi di join per distribuire i record in partizioni== chiamate _bucket_. L'obiettivo è distribuire i record in bucket tali che un record di R1​ possa accoppiarsi solo con record di R2​ appartenenti al bucket omologo (stesso valore hash). L'algoritmo prevede una fase di pre-processamento dove ogni file viene letto e distribuito in $P$ liste di blocchi. ==Quando un buffer è pieno, viene scritto su disco come blocco dell'opportuno bucket==.

> **Non è necessaria una struttura hash preesistente.**

Durante la scansione del primo file, le ennuple vengono indirizzate ai bucket in base al valore hash:

* I record (A 901) e (C 901) vengono indirizzati al Buffer 01 e scritti nel **Bucket 01**.
* I record (G 902), (M 909) e (Q 902) vengono indirizzati al **Bucket 02**.
* I record (B 903) e (P 903) finiscono nel **Bucket 03**.
* I record (D 904), (H 904), (L 907), (N 907) e (S 905) vengono indirizzati al **Bucket 04**.

Lo stesso processo viene applicato al secondo file (con chiavi come X901, Y910, Z911). Una volta completata la partizione, il sistema confronta solo i bucket omologhi. 

> Sfruttando i buffer, il **costo complessivo** è dato da **due passate di lettura e una di scrittura**: ==$3 \times (B_{1}+B_{2})$==. ==L'algoritmo è ottimale se le partizioni di **almeno** un file entrano **interamente** in memoria, condizione verificata se $P^{2} > \min(B_{1}, B_{2})$.==

## Confronto tra le strategie e criteri di scelta

L'ottimizzatore seleziona la strategia più efficiente basandosi sui profili delle relazioni:

* **Risultato piccolo (alta selettività)**: il **nested-loop con indice** è preferibile per il ridotto numero di accessi diretti.
* **Operandi grandi di dimensione simile**: si opta per il **merge-join**, poiché è _immune ai problemi di distribuzione non uniforme_ dei valori hash (skew) che potrebbero saturare i bucket nell'hash-join.
* **Operandi grandi di dimensioni diverse**: l'**hash-join** è superiore perché permette di _caricare interamente_ in memoria le porzioni della tabella più piccola, ottimizzando la fase finale di confronto.

# Il processo di esecuzione e ottimizzazione delle interrogazioni

Il ciclo di vita di un'interrogazione all'interno di un DBMS inizia con la ricezione di un comando in linguaggio SQL. Questo comando attraversa una serie di fasi trasformative coordinate dal processore delle interrogazioni, che interagisce costantemente con il _Catalogo_ del sistema. ==Il Catalogo funge da repository centrale contenente lo schema dei dati, le informazioni sulle strutture fisiche disponibili e i profili statistici delle relazioni==.

La prima fase consiste nell'**analisi lessicale, sintattica e semantica**. In questo stadio, la stringa SQL viene verificata rispetto alla grammatica del linguaggio e alla validità dei riferimenti agli oggetti del database (tabelle e colonne definiti nello schema). L'output di questa fase è un'espressione iniziale in algebra relazionale. Successivamente, avviene l'**ottimizzazione algebrica**, che applica trasformazioni logiche all'espressione (come l'anticipazione delle selezioni e delle proiezioni) per produrre un'espressione algebrica ottimizzata. L'ultima fase critica è l'**ottimizzazione basata sui costi**, dove il sistema consulta le statistiche e le strutture fisiche nel Catalogo per generare il **piano di accesso** definitivo, ovvero la sequenza di operazioni fisiche che il sistema eseguirà effettivamente.

## Ottimizzazione basata sui costi e alberi di decisione

L'ottimizzazione basata sui costi affronta il problema di come eseguire concretamente un'espressione algebrica. Si tratta di un problema articolato che richiede scelte strategiche su molteplici fronti:

* **Scelta delle operazioni elementari**: decidere se accedere ai dati tramite una scansione sequenziale dell'intero file o mediante un accesso diretto attraverso un indice.
* **Ordine delle operazioni**: in presenza di join multipli (ad esempio tra tre relazioni), determinare la sequenza temporale con cui accoppiare le tabelle.
* **Dettagli metodologici**: selezionare l'algoritmo specifico per ogni operatore (ad esempio, scegliere tra nested-loop, merge-scan o hash-join per un'operazione di join).
* **Gradi di libertà addizionali**: nelle architetture parallele e distribuite, l'ottimizzatore deve considerare anche la distribuzione dei dati tra i nodi e il parallelismo di esecuzione.

Per gestire questa complessità, l'==ottimizzatore costruisce un **albero di decisione** che rappresenta le varie alternative, definite piani di esecuzione==. Ciascun piano viene valutato assegnandogli un ==costo stimato basato sui profili statistici== del catalogo. L'obiettivo dell'ottimizzatore è individuare il piano con il costo minore, sebbene nella pratica tenda a trovare una "buona" soluzione piuttosto che quella matematicamente ottima, a causa dell'enorme spazio di ricerca.

## Strategie di esecuzione: Pipelining vs Materializzazione

Durante l'esecuzione di interrogazioni complesse rappresentate da sottoalberi, il DBMS può adottare ==due strategie== per la gestione dei risultati intermedi:

* **Pipelining**: le ennuple prodotte da un operatore vengono **passate immediatamente all'operatore superiore** a mano a mano che vengono generate (esecuzione "on-demand").

  * _Vantaggio_: riduce drasticamente i costi di I/O poiché i risultati intermedi non devono essere salvati su memoria secondaria.
  * _Svantaggio_: se un risultato intermedio deve essere riutilizzato più volte (come nel ciclo interno di un nested-loop join), è necessario ricalcolarlo ogni volta, aumentando il carico computazionale.

* **Materializzazione**: l'intero **risultato di un sottoalbero viene calcolato e memorizzato fisicamente su disco** prima di essere utilizzato dal nodo superiore. Questo approccio è necessario quando l'operatore superiore richiede l'accesso completo ai dati (come in certi algoritmi di ordinamento) o quando il riutilizzo del dato materializzato è più economico del ricalcolo.

## Esempi pratici di ottimizzazione algebrica

Si consideri una base di dati composta dalle seguenti relazioni:

* $Impiegati(\underline{Matricola}, Cognome, Nome, Ufficio)$: 100.000 record, 10.000 uffici distinti.
* $Progetti(\underline{Codice}, Titolo, Committente)$: 1000 record, Titolo è chiave candidata.
* $Collaborazioni(\underline{Impiegato}, \underline{Progetto}, Ruolo)$: 500.000 record.

Per l'interrogazione "I dati dei progetti cui collaborano impiegati dell'ufficio 5103", il comando SQL è: `SELECT Progetti.* FROM Impiegati JOIN Collaborazioni ON Matricola=Impiegato JOIN Progetti ON Progetto=Codice WHERE Ufficio = 5103`

L'ottimizzazione algebrica trasforma questa richiesta anticipando la selezione. L'albero risultante vede alla base la selezione $\sigma_\text{Ufficio=5103}(Impiegati)$, il cui risultato entra in join con $Collaborazioni$ sulla condizione $Matr=Imp$. Il risultato di questo join viene infine unito in join con $Progetti$ sulla condizione $Prog=Cod$, con una proiezione finale $\pi_\text{Cod, Titolo, Valore}$.

Per l'interrogazione "I dati degli impiegati che collaborano al progetto Marte", il comando SQL è: `SELECT Impiegati.* FROM Impiegati JOIN Collaborazioni ON Matricola=Impiegato JOIN Progetti ON Progetto=Codice WHERE Titolo = 'Marte'`

In questo caso, l'ottimizzazione sposta la selezione alla base della relazione Progetti: $\sigma_{Titolo='Marte'}(Progetti)$. Il risultato (estremamente selettivo) entra in join con $Collaborazioni$ sulla condizione $Cod=Prog$, e il prodotto di questa operazione effettua il join finale con $Impiegati$ sulla condizione $Imp=Matr$, concludendo con la proiezione $\pi_{Matr, Cog, Nome, Ufficio}$.

## Progettazione fisica nei DBMS relazionali

La ==progettazione fisica== è la fase finale del ciclo di progettazione di una base di dati. ==Prende in _input_ lo **schema logico** e le **informazioni sul carico applicativo** per _produrre_ uno **schema fisico**==, che definisce le strutture di memorizzazione e i parametri specifici del DBMS.

### Strutture primarie e indici

Le strutture primarie definiscono come i dati sono organizzati nel file principale:

* **Disordinata (heap, "unclustered")**: i record sono inseriti senza un ordine specifico.
* **Ordinata ("clustered")**: i dati sono mantenuti fisicamente ordinati secondo una chiave o pseudochiave.
* **Hash ("clustered")**: i dati sono distribuiti in bucket tramite una funzione hash, senza un ordine sequenziale.
* **Clustering plurirelazionale**: memorizzazione fisica ravvicinata di record appartenenti a relazioni diverse ma logicamente collegate (ad esempio ordini e relative righe d'ordine).

Gli indici possono essere densi (un puntatore per ogni record) o sparsi (un puntatore per ogni blocco), semplici o composti. Le tipologie comuni includono:

* **ISAM**: indice statico, tipico di strutture ordinate.
* **B-tree**: indice dinamico e bilanciato, lo standard per la maggior parte dei DBMS.
* **Indici Hash**: indici secondari meno dinamici rispetto ai B-tree.

### Implementazioni nei DBMS commerciali

* **Oracle**: utilizza file heap come primaria, supporta "hash cluster" e cluster plurirelazionali (anche ordinati con B-tree denso). Offre indici secondari B-tree, bit-map e basati su funzioni.
* **DB2**: struttura primaria heap o ordinata con B-tree denso; crea automaticamente un indice sulla chiave primaria e supporta indici secondari B-tree densi.
* ~~**SQL Server**: primaria heap o ordinata con indice B-tree sparso; indici secondari B-tree densi.~~
* ~~**Ingres (storico)**: supportava heap, hash e ISAM (anche compressi).~~
* ~~**Informix (storico)**: struttura primaria heap, indici secondari e primari (cluster) non mantenuti.~~

## Definizione degli indici in SQL e Postgres

Sebbene non sia parte dello standard SQL puro, la creazione di indici è gestita in modo simile dai vari sistemi:

* `CREATE [UNIQUE] INDEX NomeIndice ON NomeTabella(ListaAttributi)`
* `DROP INDEX NomeIndice`

> Il termine `UNIQUE` è considerato [metodologicamente controverso]{.underline} poiché mescola un vincolo logico (l'unicità) con una struttura fisica (l'indice).

Postgres offre comandi avanzati per la gestione fisica:

* `CREATE [ UNIQUE ] INDEX [ name ] ON table [ USING method ] ( { column | ( expression ) } [ ASC | DESC ] )`: permette di specificare il metodo (es. B-tree, Hash, GIST) e l'ordinamento dei `null`.
* `CLUSTER table_name [ USING index_name ]`: riordina fisicamente la tabella in base a un indice esistente, **ma non viene persistito**.
* `VACUUM [ ANALYZE ] table`: recupera spazio e aggiorna le statistiche per l'ottimizzatore.

## Euristiche di progettazione fisica e tuning

La scelta degli indici è il cuore della progettazione fisica. Molti sistemi suggeriscono di definire indici sulle chiavi primarie poiché coinvolte frequentemente in join e selezioni. Il processo di _==tuning==_ consiste nell'==aggiungere o rimuovere indici o modificare strutture primarie== se le prestazioni non sono soddisfacenti, verificando l'uso effettivo degli indici tramite i comandi `EXPLAIN` o `SHOW PLAN`.

### Euristiche di Informix

1. **Non** creare indici su relazioni molto **piccole** (meno di 200 ennuple).
2. **Evitare** indici su campi con cardinalità molto **bassa** (pochi valori distinti); se necessario, preferire indici primari.
3. **Creare** indici su campi soggetti a **frequenti selezioni**.
4. Per l'ottimizzazione dei join, creare **indici** sulla relazione di dimensioni **maggiori**.

### Metodo di Shasha per la scelta della struttura

Shasha propone un albero di decisione per la scelta della struttura primaria:

* Se la **relazione è piccola**, scegliere **Heap senza indice**.
* Se non è piccola:
  * Se è **enorme e senza tempi morti** (aggiornamenti rari), scegliere **Heap con indice**.
  * Se non lo è, e si effettuano ricerche per **intervalli, estremi o ordinamenti**:
    * Se la chiave **non è** sequenziale **ma è** dinamica: **Cluster B-Tree**.
    * Se la chiave **non è** sequenziale **e non** dinamica: **Cluster ISAM**.
    * Se la chiave **è** sequenziale: **Hash**.
  * Se **non** si effettuano ricerche per intervalli: **Hash**.

> ==Risultati sperimentali confermano che per interrogazioni non selettive l'Hash Join è superiore, mentre per query con selezioni forti il Nested Loop è la scelta ottimale.==

## Esercizio di valutazione dei costi (9 Aprile 2018)

Si considerino le relazioni $R1(\underline{A}, B, C)$ e $R2(\underline{D}, E, F)$ con indici sulle chiavi primarie. Dati:

* $N_{1} = 2.000.000$ ennuple, $N_{2} = 4.000.000$ ennuple.
* Fattori di blocco: $f_{1} = 20$, $f_{2} = 40$.
* Attributo $B$ in $R1$: 200.000 valori distinti distribuiti uniformemente tra 1 e 200.000.
* Indici: profondità $p=4$ (radice e foglie incluse), fattore di blocco massimo $f_{i} = 50$.
* Memoria: $q=500$ pagine di buffer.

**Caso 1: `SELECT * FROM R1 JOIN R2 ON C=D`** Postgres sceglie l'**Hash Join**. Il costo dell'Hash Join, non potendo tenere tutta la relazione in memoria ($q < B_{1}$), richiede due passate: lettura e partizionamento di entrambe le relazioni e successiva rilettura per il join. $Costo \approx 3 \times (N_{1}/f_{1} + N_{2}/f_{2}) = 3 \times (100.000 + 100.000) = 600.000$ accessi. Un Nested Loop senza selezione richiederebbe $100.000 + (100.000/500 \times 100.000) = 20.100.000$ accessi, risultando proibitivo.

**Caso 2: `SELECT * FROM R1 JOIN R2 ON C=D WHERE B >= 41 AND B <= 45`** Postgres sceglie **Nested Loop join con accesso diretto alla relazione interna**. La selezione su $B$ ha una selettività elevata: $(45 - 41 + 1) / 200.000 = 5 / 200.000 = 1/40.000$. Numero di ennuple di $R1$ filtrate: $2.000.000 / 40.000 = 50$ ennuple. Costo:

1. Accesso alle 50 ennuple di $R1$ (scansione o indice): trascurabile.
2. Per ogni ennupla (50 volte), accesso diretto a $R2$ tramite indice su chiave primaria $D$: $Costo = 50 \times (p + 1) = 50 \times 5 = 250$ accessi. In questo caso, la selettività della condizione su $B$ rende il Nested Loop estremamente più vantaggioso rispetto all'Hash Join.

\newpage
# SimpleDB
<!-- 
Nell'analisi di un DBMS didattico come **SimpleDB**, è possibile osservare una scomposizione modulare ancora più dettagliata delle responsabilità:

* **Remote**: agisce come interfaccia di comunicazione, ricevendo le richieste dal client e inoltrando il codice SQL al Planner.
* **Planner**: è il modulo decisionale che interpella il Parser per ottenere un'analisi sintattica della query, determina il piano di esecuzione ottimale e lo trasmette al Query.
* **Parser**: esegue l'analisi sintattica formale delle istruzioni ricevute.
* **Query**: riceve il piano di esecuzione e coordina le chiamate al modulo Record per ogni tabella coinvolta nell'operazione.
* **Metadata**: si occupa della gestione degli schemi delle tabelle, conservando le informazioni strutturali della base di dati.
* **Record**: gestisce specificamente i blocchi di memoria destinati a contenere i record delle singole tabelle.
* **Transaction**: garantisce l'integrità dei dati gestendo la concorrenza tra le diverse operazioni simultanee.
* **Buffer**: mantiene in memoria principale le pagine di dati più utilizzate per limitare drasticamente la necessità di accessi costosi alla memoria secondaria.
* **Log**: registra sistematicamente ogni operazione effettuata per garantire l'affidabilità e la possibilità di ripristino del sistema.
* **File**: costituisce il livello più basso che si occupa della lettura e scrittura effettiva delle pagine sul disco fisico. -->

L'architettura di SimpleDB si articola in una serie di moduli cooperanti che gestiscono l'intero ciclo di vita di una richiesta, dalla ricezione della query SQL alla manipolazione fisica dei bit sul disco. Al livello più esterno, il modulo **JDBC** funge da interfaccia di ingresso, ricevendo le richieste dal client e inoltrando il codice SQL al **Planner**. Il Planner ha il compito di determinare la strategia di esecuzione ottimale; per fare ciò, chiama il **Parser** per l'analisi sintattica della stringa SQL, genera un piano di accesso e lo trasmette al modulo **Query**.

Il modulo Query riceve il piano d'azione ed esegue le operazioni logiche interagendo con il modulo **Record** per ogni tabella coinvolta. La gestione della struttura dei dati è affidata ai **Metadata**, che amministrano gli schemi delle tabelle, mentre il modulo Record gestisce l'organizzazione dei blocchi per ospitare i record. La correttezza e l'integrità del sistema sono garantite dal modulo **Transaction**, incaricato di gestire la concorrenza tra utenti e l'affidabilità dei dati in caso di guasti.

La gestione della memoria si basa su tre componenti fondamentali: il **Buffer**, che mantiene in memoria le pagine per limitare gli accessi fisici al disco; il **File**, responsabile delle operazioni di lettura e scrittura delle pagine sul supporto fisico; e il **Log**, che tiene traccia di ogni operazione per permettere il recovery.

## Livelli di astrazione e flussi dei dati

Il sistema opera attraverso una gerarchia di astrazioni che trasformano una visione relazionale dei dati in una visione a blocchi. Il flusso delle chiamate parte dall'alto verso il basso:

1. **JDBC**: Riceve le richieste SQL e attiva il Planner.
2. **Planner**: Determina l'access plan (piano di accesso).
3. **JDBC**: Apre l'access plan, che viene trasformato in un **access scan**. Quest'ultimo funge da iteratore per la query, permettendo di scorrere i risultati come se fossero una sequenza di record.
4. **Record**: Rappresenta l'astrazione relazionale, trasformando una sequenza di blocchi (o un singolo blocco) in una sequenza di record manipolabili.
5. **Buffer**: Fornisce un'astrazione a blocchi di un file, gestendo la permanenza dei dati in memoria principale.
6. **File**: Rappresenta il livello più basso, dove le pagine vengono lette e scritte direttamente sul disco.

Il flusso dei dati segue il percorso inverso, risalendo dai blocchi fisici del file fino ai record restituiti all'interfaccia JDBC.

## Memory Management e principi di persistenza

La gestione della memoria nei sistemi di basi di dati segue due principi cardine dettati dalle differenze di prestazioni tra i supporti di memorizzazione:

* **Minimizzazione degli accessi al disco**: L'I/O su disco è estremamente oneroso in termini di tempo. Per mitigare questo collo di bottiglia, si utilizzano meccanismi di caching, come la CPU cache e la disk cache.
* **Indipendenza dalla memoria virtuale del sistema operativo**: Un DBMS non deve affidarsi alla memoria virtuale del SO per due motivi critici. In primo luogo, la memoria virtuale non garantisce il recovery da crash; il SO potrebbe decidere di scrivere una pagina (swap) sul disco prima che il relativo log sia stato reso persistente, violando i protocolli di affidabilità. In secondo luogo, il SO utilizza euristiche di rimpiazzo generiche e subottime, mentre il database possiede una conoscenza approfondita dei pattern di accesso ai dati e può prendere decisioni di rimpiazzo molto più efficienti.

## Il Package Buffer e la gestione del Buffer Pool

Il package `simpledb.buffer` gestisce la cache dei blocchi disco in memoria centrale. La struttura delle classi principali include:

* **Buffer**: Rappresenta una singola pagina caricata. Contiene riferimenti al `LogMgr` (`lm`), il numero di pin attivi (`pins`), l'identificativo della transazione che ha modificato il buffer (`txnum`) e il Log Sequence Number (`lsn`). Metodi chiave sono `contents()` per ottenere la `Page`, `pin()` e `unpin()`.
* **BufferMgr**: Gestisce il pool di buffer. Tiene traccia dei buffer disponibili (`numAvailable`) e gestisce il tempo massimo di attesa (`MAX_TIME`). Implementa metodi per fissare un blocco in memoria (`pin(BlockId)`), liberarlo (`unpin(Buffer)`) o forzare la scrittura su disco (`flushAll(int)`).
* **FileMgr**: Gestisce l'interazione con il file system, mantenendo informazioni sulla directory del database (`dbDirectory`), la dimensione dei blocchi (`blocksize`) e le statistiche di accesso (`stats`).
* **Page**: Contiene il contenuto effettivo dei dati in un `ByteBuffer` (`bb`) e gestisce il set di caratteri (`CHARSET`).

### Logica di pinning e rimpiazzo

L'operazione di `pin(BlockId)` segue un protocollo preciso descritto nei diagrammi di sequenza:

1. Il `BufferMgr` chiama `tryToPin(BlockId)`.
2. Viene verificata l'esistenza del blocco nel pool tramite `findExistingBuffer(BlockId)`.
3. Se il blocco non è presente (`buff == null`), il gestore sceglie un buffer non fissato tramite `chooseUnpinnedBuffer()`.
4. Il buffer scelto viene assegnato al nuovo blocco con `assignToBlock(BlockId)`. Se il buffer era "sporco" (modificato), viene eseguito un `flush()` che attiva la scrittura fisica tramite `FileMgr.write(BlockId, Page)`.
5. Infine, viene incrementato il contatore dei pin sul buffer.

Se non ci sono buffer disponibili, il sistema entra in un ciclo di attesa (`while: buff == null && !waitingTooLong(timestamp)`) finché un altro processo non libera un buffer.

## Strategie di rimpiazzo dei buffer (Buffer Replacement Strategies)

Poiché il buffer manager non può prevedere con certezza quali pagine verranno richieste in futuro, deve adottare delle euristiche per scegliere quale pagina espellere quando il pool è pieno. La scelta cade obbligatoriamente sulle pagine "unwanted", ovvero quelle con numero di pin pari a zero (unpinned). Si distinguono quattro strategie generali:

1. **Naïve**: Cerca e seleziona semplicemente la prima pagina libera o non fissata che incontra. È la strategia standard di SimpleDB.
2. **FIFO (First-In-First-Out)**: Espelle la pagina che è stata caricata in memoria da più tempo, indipendentemente dalla frequenza d'uso recente.
3. **LRU (Least Recently Used)**: Utilizza la pagina che è stata liberata (unpinned) meno di recente. Si basa sul principio di località temporale.
4. **Clock**: Effettua una scansione circolare dei buffer. Inizia la ricerca dalla pagina successiva a quella dell'ultimo rimpiazzo, comportandosi come una versione più efficiente della strategia naïve che evita di favorire sempre i primi buffer del pool.

SimpleDB implementa internamente il protocollo "no steal", il che significa che una pagina modificata da una transazione non ancora conclusa non può essere espulsa dal buffer e scritta su disco.

## Record Management e organizzazione fisica

Il Record Manager di SimpleDB implementa una gestione di record omogenei, non frammentati (unspanned) e a lunghezza fissa. Ogni blocco viene trattato come un array di slot.

* **Record Page**: Un blocco strutturato come array di record a lunghezza fissa.
* **Status Flag**: Ogni slot inizia con un flag (0 o 1) che indica se lo slot è vuoto o in uso. La cancellazione di un record consiste nel commutare il flag da 1 a 0.
* **Record ID (RID)**: Composto dal numero del blocco e dal numero dello slot all'interno della pagina.

### Calcolo delle posizioni fisiche

Sia $RL$ la lunghezza del record (record length). Le posizioni all'interno della pagina sono calcolate come segue:

* Posizione del flag di stato per lo slot $k$: $(RL+1)\*k$
* Posizione del campo $F$ nel record allo slot $k$: $(RL+1)\*k+OFFSET(F)+1$

Il `Layout` della tabella definisce gli offset dei campi e la dimensione totale dello slot. Ad esempio, per una tabella `STUDENT`, le informazioni potrebbero essere:

* `SId` (int): lunghezza 4, offset 0.
* `SName` (varchar): lunghezza 14, offset 4.
* `GradYear` (int): lunghezza 4, offset 18.
* `MajorId` (int): lunghezza 4, offset 22. La lunghezza totale del record $RL$ sarebbe 26.

## Il Catalogo e la gestione dei Metadati

I metadati sono memorizzati in tabelle di sistema chiamate tabelle di catalogo:

* `tblcat(TblName, RecLength)`: Contiene l'elenco delle tabelle e la lunghezza dei relativi record.
* `fdlcat(TblName, FldName, Type, Length, Offset)`: Descrive ogni campo di ogni tabella.
* `viewcat(ViewName, ViewDef)`: Memorizza le definizioni delle viste.
* `idxcat(Indexname, Tablename, Fieldname)`: Elenca gli indici definiti sui campi.

Il `MetadataMgr` coordina moduli specializzati come `TableMgr`, `ViewMgr`, `StatMgr` (per le statistiche di accesso) e `IndexMgr`.

## Query Management: Piani e Scansioni

L'esecuzione di una query avviene in due fasi: pianificazione ed esecuzione.

1. **Plan**: Rappresenta l'albero logico dell'interrogazione. Le implementazioni includono `TablePlan`, `SelectPlan`, `ProjectPlan` e `ProductPlan`. Ad esempio, una query `SELECT SName FROM STUDENT, ENROLL, SECTION WHERE ...` viene rappresentata come un albero di prodotti cartesiani sormontati da selezioni e proiezioni. Ogni oggetto `Plan` può fornire stime sul numero di blocchi acceduti e record prodotti.
2. **Scan**: È l'interfaccia che esegue effettivamente le operazioni. Ogni nodo dell'albero del piano diventa un oggetto `Scan` (es. `SelectScan`, `TableScan`). Lo scan funziona come un iteratore tramite il metodo `next()`, che restituisce un booleano indicando se è presente una nuova ennupla.

## Ottimizzazione e prestazioni

Per migliorare le performance, SimpleDB include package dedicati a strutture dati avanzate:

* **Index**: Gestisce indici e accesso diretto tramite `BTreeIndex` o `HashIndex`. Gli indici permettono l'uso di `IndexSelectScan` e `IndexJoinScan` per evitare scansioni complete delle tabelle.
* **Materialize**: Gestisce la materializzazione dei risultati intermedi e l'ordinamento dei dati.
* **Multibuffer**: Ottimizza l'uso dei buffer disponibili per operazioni pesanti come il join.
* **Opt**: Contiene il query optimizer per la selezione del piano di accesso più efficiente.

### Esecuzione di un IndexJoinScan

Il diagramma di sequenza per `IndexJoinScan.next()` mostra come il sistema iteri sulla tabella di sinistra (`lhs Scan`). Per ogni record trovato a sinistra, viene resettato l'indice della tabella di destra (`idx.beforeFirst(val)`). Il sistema quindi itera sull'indice (`idx.next()`) e usa il `RID` ottenuto per muovere la scansione della tabella di destra (`rhs TableScan`) direttamente sul record corrispondente tramite `moveToRid(RID)`.
