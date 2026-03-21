---
title: "TAGD-01-ai"
author:
  - Filippo Visconti
template:
  - template.tex
---

# Organizzazione fisica e gestione delle interrogazioni

L'architettura di un sistema di gestione di basi di dati (DBMS) è strutturata per gestire il flusso delle informazioni partendo dalle richieste ad alto livello fino alla memorizzazione fisica dei dati. Il processo ha inizio con il **Gestore delle interrogazioni**, che riceve istruzioni espresse in linguaggio SQL. Questo componente ha il compito di tradurre le query in operazioni eseguibili come la scansione delle tabelle, l'accesso diretto ai record o l'ordinamento dei dati. Una volta definito il piano d'azione, la richiesta passa al **Gestore dei metodi d'accesso**, il quale opera attraverso quella che viene definita lettura "virtuale". Questo livello a sua volta interagisce con il **Gestore del buffer**, che funge da intermediario per ottimizzare le prestazioni eseguendo letture fisiche attraverso il **Gestore della memoria secondaria**. Quest'ultimo è l'interfaccia finale che comunica direttamente con i dispositivi di **memoria secondaria**, dove i dati risiedono stabilmente.

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
* **File**: costituisce il livello più basso che si occupa della lettura e scrittura effettiva delle pagine sul disco fisico.

La distinzione tra **memoria principale** e **memoria secondaria** è fondamentale per comprendere le prestazioni di un database. I programmi possono fare riferimento esclusivamente a dati presenti nella memoria principale. Tuttavia, le basi di dati devono necessariamente risiedere nella memoria secondaria per due ragioni critiche: le dimensioni, spesso superiori alla capacità della RAM, e la persistenza, ovvero la necessità che i dati sopravvivano allo spegnimento del sistema. Di conseguenza, ogni dato memorizzato su disco deve essere trasferito nella memoria principale per poter essere elaborato; questa dinamica di trasferimento è ciò che definisce i concetti di gerarchia di memoria.

I dispositivi di memoria secondaria sono organizzati fisicamente in **blocchi** di lunghezza fissa, solitamente nell'ordine di alcuni KB. Specularmente, nella memoria centrale viene allocata un'area della stessa dimensione chiamata **pagina**. Le operazioni fondamentali sui dispositivi si limitano alla lettura di un blocco dal disco verso una pagina e alla scrittura di una pagina su un blocco del disco. Nella pratica tecnica, i termini "blocco" e "pagina" sono spesso usati come sinonimi. Il sistema operativo assegna un numero univoco a ogni blocco del disco, garantendo che ogni unità di memorizzazione abbia un indirizzo univoco all'interno del sistema di elaborazione.

Le prestazioni di un disco tradizionale (meccanico a rotazione) sono determinate da tre fattori temporali:

1. **Tempo di posizionamento della testina (seek time)**: il tempo necessario per muovere la testina sulla traccia corretta, mediamente compreso tra 4ms e 15ms.
2. **Tempo di latenza (rotational delay)**: il tempo necessario affinché il settore corretto ruoti sotto la testina, variabile tra 2ms e 8ms in base alla velocità di rotazione (da 4K a 15K giri al minuto).
3. **Tempo di trasferimento di un blocco**: il tempo effettivo di passaggio dei dati, che rappresenta solo una frazione di millisecondo data la velocità di trasferimento tra 100 e 600MB/s. Complessivamente, un accesso richiede mediamente non meno di qualche millisecondo.

Il costo di un accesso alla memoria secondaria è di quattro o più ordini di grandezza superiore rispetto alle operazioni in memoria centrale: parliamo di millisecondi contro decimi o centesimi di microsecondo. Per questo motivo, nelle applicazioni definite "I/O bound", il costo totale dipende quasi esclusivamente dal numero di accessi al disco. È importante notare che leggere un singolo bit o un intero blocco ha lo stesso costo temporale. Inoltre, l'accesso a blocchi contigui è meno oneroso, specialmente se il disco esegue il _prefetching_, ovvero la lettura anticipata di intere tracce memorizzate in una cache interna.

Le **Unità a Stato Solido (SSD)** introducono caratteristiche differenti: essendo prive di parti meccaniche, offrono un accesso diretto a costo uniforme, risultando molto più veloci dei dischi tradizionali per gli accessi casuali. Tuttavia, il loro costo per gigabyte è ancora superiore e le prestazioni in scrittura tendono a peggiorare nel tempo poiché il numero di riscritture è limitato e il sistema deve distribuire i dati in posizioni diverse per preservare l'integrità delle celle. Nonostante la velocità superiore, l'accesso a un SSD resta comunque di vari ordini di grandezza più lento della RAM (decine o centinaia di microsecondi contro decimi o centesimi di microsecondo).

Il **File System** del sistema operativo gestisce la memoria secondaria tipicamente su due livelli:

* **Livello basso**: fornisce primitive per agire sui blocchi (leggi/scrivi un blocco in una pagina, alloca/dealloca blocchi contigui).
* **Livello alto**: gestisce i file come sequenze di caratteri o oggetti dotati di nome, struttura e una posizione corrente, offrendo primitive come il posizionamento (_seek_) e la lettura/scrittura in posizioni specifiche.

Un DBMS può interagire con il file system in diversi modi:

* **A livello di blocchi**: garantisce un controllo completo sul posizionamento fisico, permettendo di distribuire oggetti su più dispositivi. Lo svantaggio è l'estrema complessità amministrativa e la necessità di avere dischi dedicati esclusivamente al DBMS.
* **A livello di file**: è più semplice da realizzare (un file per ogni tabella), ma il DBMS perde la visibilità sulla reale allocazione dei blocchi e sul buffer, con un impatto negativo sulle prestazioni.
* **Soluzione intermedia**: è l'approccio più frequente. Il DBMS usa il file system in modo limitato per creare/eliminare file e gestire flussi di blocchi, ma mantiene il controllo diretto sull'organizzazione interna, decidendo come i record sono distribuiti nei blocchi e quale sia la struttura interna ai blocchi stessi.

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

* **fix** o **pin**: richiesta di un blocco. Se il blocco non è nel buffer, viene eseguita una lettura fisica. Il sistema restituisce l'indirizzo della pagina e incrementa il contatore di pin.
* **setDirty** (o **setModified**): comunica che la pagina è stata modificata.
* **unfix** o **unpin**: comunica che il programma ha terminato l'uso della pagina, permettendo al gestore di decrementare il contatore.
* **force** o **flush**: forza il trasferimento sincrono di una pagina sporca sulla memoria secondaria.

Durante l'esecuzione di una `fix`, il gestore cerca la pagina nel buffer. Se non la trova, deve cercare una pagina "libera" (con contatore a zero). Se la pagina scelta per il rimpiazzo è "sporca", deve prima salvarla su disco. Se non ci sono pagine con contatore a zero, il sistema può seguire due politiche:

* **No-steal**: l'operazione viene posta in attesa finché una pagina non viene liberata.
* **Steal**: viene selezionata una "vittima" anche tra le pagine occupate, scrivendone i dati su disco se sporca (questo approccio è più complesso e spesso evitato nelle implementazioni semplificate).

Le scritture su disco possono quindi essere **sincrone** (richieste esplicite di flush) o **asincrone** (decise dal gestore per liberare spazio o per ottimizzare le prestazioni del dispositivo sfruttando i tempi morti).

## Strategie di rimpiazzo (Buffer Replacement)

Quando è necessario caricare un nuovo blocco e il buffer è pieno di pagine non utilizzate, bisogna scegliere quale sacrificare. Le strategie principali sono:

* **Naive**: sceglie la prima pagina libera incontrata nella scansione.
* **FIFO (First-In-First-Out)**: sostituisce la pagina che è stata caricata da più tempo.
* **LRU (Least Recently Used)**: sostituisce la pagina che è stata utilizzata meno di recente. È la strategia che meglio approssima la previsione del futuro basandosi sul passato.
* **Clock**: esegue una scansione circolare partendo dalla posizione successiva all'ultimo rimpiazzo, offrendo un'approssimazione efficiente della LRU.

Consideriamo un esercizio con un buffer di 4 pagine (0-3). Lo stato iniziale all'istante 9 vede:

* Pagina 0: blocco 70, pin 1, load 1, dirty 1.
* Pagina 1: blocco 33, pin 2, load 7, dirty 0.
* Pagina 2: blocco 35, pin 0, load 3, unpin 8, dirty 0.
* Pagina 3: blocco 47, pin 1, load 9, dirty 0.

Se all'istante 11 viene eseguita una `pin(60)`, il sistema cerca una pagina libera (pin=0). L'unica è la pagina 2. Poiché non contiene il blocco 60, deve caricarlo. Il blocco 35 viene rimpiazzato dal 60. Se la strategia fosse **LRU**, all'istante 17 per una `pin(70)`, si cercherebbero pagine con pin=0. Se dopo varie operazioni di `unpin` la pagina 0 fosse libera, essa verrebbe scelta se il suo istante di ultimo utilizzo fosse il più remoto.

## Organizzazione dei record nei blocchi

Un file è composto logicamente da **record** (ennuple) ma è organizzato fisicamente in **blocchi**. Poiché le dimensioni di questi due elementi sono solitamente diverse, è necessario gestire la loro mappatura. I record possono essere a **lunghezza fissa** o **variabile**. I blocchi possono essere **omogenei** (record di una sola relazione) o **eterogenei** (record di relazioni diverse, utile per ottimizzare i join fisici).

Se un record è interamente contenuto in un blocco, si parla di organizzazione **unspanned**. Se un record può essere diviso tra più blocchi, si parla di **spanned**. In caso di record a lunghezza fissa $L_R$ e blocchi di dimensione $L_B$, il **fattore di blocco** (numero di record per blocco) è calcolato come: $f = \lfloor L_B / L_R \rfloor$

L'organizzazione interna di una pagina prevede solitamente un **dizionario di pagina** e una **parte utile**. Una struttura comune prevede due stack che crescono in direzioni opposte: uno stack per il dizionario (puntatori alle ennuple $\*t1, \*t2, \dots$) e uno stack per i dati effettivi ($t1, t2, \dots$). Questo permette di gestire record di lunghezza variabile. La pagina include anche informazioni di controllo della struttura fisica e del file system, oltre a un bit di parità per il controllo degli errori.

## Strutture fisiche e file disordinati

Le strutture fisiche si dividono in:

* **Primarie**: definiscono come i record sono organizzati nel file.
* **Secondarie**: strutture ausiliarie (come gli indici) per velocizzare l'accesso.

Le tipologie principali sono sequenziali, calcolate (Hash) o ad albero. Tra le sequenziali, la più semplice è la **struttura disordinata** (chiamata anche file seriale, heap o "entry sequenced"). In questa organizzazione, non esiste un ordine logico: i nuovi record vengono inseriti solitamente in coda o occupando i "voti" lasciati da cancellazioni precedenti.

Le operazioni su un file disordinato includono la scansione (`beforeFirst`, `next`), la lettura di campi (`getInt`, `getString`) e l'aggiornamento (`setInt`, `insert`, `delete`). L'implementazione della `next` verifica se nel blocco corrente ci sono altri record; in caso negativo, passa al primo record del blocco successivo. Il costo di ricerca e inserimento in un file disordinato è **lineare** rispetto al numero di blocchi del file, rendendolo inefficiente per basi di dati di grandi dimensioni senza l'ausilio di indici secondari. Sebbene l'inserimento potrebbe sembrare $O(1)$ scrivendo in coda, la necessità di verificare vincoli di integrità (come l'unicità della chiave) richiede comunque una scansione completa, riportando il costo a $O(N)$.

# Strutture ordinate e File Hash

In un sistema di gestione di basi di dati, l'organizzazione fisica dei record può seguire criteri logico-matematici precisi per ottimizzare il reperimento delle informazioni. Una delle modalità fondamentali è la **struttura ordinata**, in cui ogni record, ovvero ogni ennupla della relazione, occupa una posizione fisica specifica determinata dal valore di un particolare campo. Questo campo viene definito **chiave** o, con maggior rigore accademico, **pseudochiave**, poiché funge da criterio di ordinamento ma non è necessariamente una chiave primaria in senso logico.

Si consideri un esempio basato su una tabella composta dagli attributi Matricola, Cognome e Nome. Se il file è **ordinato per Matricola**, i record appariranno in una sequenza numerica crescente:

* 15 Neri Piero
* 21 Rossi Mario
* 30 Bianchi Gino
* 38 Verdi Luigi
* 40 Rossi Mario
* 53 Neri Luca

Alternativamente, la stessa base di dati potrebbe essere mantenuta in una struttura **ordinata per Cognome**. In questo scenario, l'ordine alfabetico prevale su quello numerico della matricola, portando a una disposizione differente:

* 30 Bianchi Gino
* 15 Neri Piero
* 53 Neri Luca
* 21 Rossi Mario
* 40 Rossi Mario
* 38 Verdi Luigi

L'adozione di una struttura ordinata comporta sfide significative per quanto riguarda la manutenzione della coerenza durante le operazioni di modifica. Gli **aggiornamenti** richiedono spesso interventi strutturali pesanti: l'inserimento di un nuovo record non può avvenire semplicemente in coda al file (come in una struttura heap), ma deve rispettare la posizione prevista dal criterio di ordinamento. Ad esempio, inserendo il record "66 Bruni Marco" in una tabella ordinata per cognome, il sistema deve individuare la posizione corretta (tra Bianchi e Neri) e traslare fisicamente tutti i record successivi per creare lo spazio necessario. Lo stesso problema si presenta con campi a lunghezza variabile quando un valore viene aggiornato con una stringa più lunga della precedente, causando uno slittamento dei record contigui.

Per gestire queste inefficienze, si adottano diverse strategie, spesso combinate tra loro:

* **Riorganizzazione immediata**: il file viene riscritto istantaneamente per mantenere l'ordine perfetto, operazione molto costosa in termini di I/O.
* **Spazio inizialmente ridondante**: si lasciano spazi vuoti (_padding_) all'interno dei blocchi per ospitare futuri inserimenti senza causare slittamenti immediati.
* **Inserimenti in coda o in blocchi di overflow**: i nuovi record vengono temporaneamente memorizzati in un'area separata e collegati alla posizione corretta tramite puntatori.
* **Riorganizzazioni periodiche**: il sistema esegue ciclicamente una manutenzione globale del file per ricompattare i dati ed eliminare le aree di overflow.

Sebbene le strutture ordinate permettano teoricamente l'uso della **ricerca binaria**, la loro applicazione pratica nei DBMS è limitata. La difficoltà risiede nella struttura fisica dei file: come si individua esattamente la "metà" di un file memorizzato su disco per poi procedere ricorsivamente? Per tale ragione, nelle basi di dati relazionali, queste strutture vengono utilizzate quasi esclusivamente in combinazione con gli indici, dando vita ai file **ISAM** (_Indexed Sequential Access Method_) o a file ordinati dotati di un indice primario. Restano comunque strumenti preziosi quando è necessario fornire risultati già ordinati all'utente o come fase preparatoria per operazioni costose come il merge-join.

Una tecnica radicalmente differente per l'accesso efficiente ai dati è rappresentata dai **File Hash**. Questa organizzazione mira a fornire un accesso diretto o associativo basato sul valore di un campo di ricerca. In un sistema come SimpleDB, l'efficienza è evidente nel passaggio dal metodo di scansione totale `beforeFirst()` a un metodo mirato `beforeFirst(searchKey)`. Questa tecnica traspone sul disco i concetti delle **tavole hash** utilizzate nella memoria centrale.

L'obiettivo di una tavola hash è l'accesso diretto a un record tramite il valore di una chiave. Se lo spazio dei possibili valori della chiave è paragonabile al numero di record effettivi (ad esempio, 1000 studenti con matricole da 1 a 1000), è possibile utilizzare un semplice array dove l'indice corrisponde alla chiave. Tuttavia, quando i possibili valori sono molto più numerosi di quelli utilizzati (ad esempio, 40 studenti con matricole a 6 cifre, che generano un milione di combinazioni potenziali), l'uso di un array diretto causerebbe un enorme spreco di memoria.

La soluzione consiste nell'utilizzare una **funzione hash**, che associa a ogni valore della chiave un "indirizzo" in uno spazio di dimensione contenuta, paragonabile al numero di record da memorizzare. Poiché lo spazio delle chiavi è vasto e quello degli indirizzi è limitato, la funzione non può essere iniettiva, rendendo inevitabili le **collisioni** (ovvero quando chiavi diverse corrispondono allo stesso indirizzo). Una buona funzione hash deve distribuire i valori in modo casuale e uniforme per minimizzare tali eventi. Un esempio didattico è la funzione modulo: $K \pmod{n}$, dove $n$ è la dimensione della tavola.

Si consideri un diagramma di flusso che illustra il processo: a sinistra abbiamo l'insieme delle chiavi (es. "John Smith", "Lisa Smith", "Sam Doe", "Sandra Dee"). Al centro agisce la **hash function** che mappa queste stringhe in valori numerici a destra, definiti **hashes**. In questo schema specifico, "Lisa Smith" viene mappata all'indirizzo `01`, "Sam Doe" al `04`, mentre "John Smith" e "Sandra Dee" collidono entrambi sull'indirizzo `02` (evidenziato graficamente per indicare l'anomalia). Gli indirizzi disponibili vanno da `00` a `15`.

Analizziamo un esercizio numerico con 8 record dotati delle seguenti chiavi: 240772, 240810, 449726, 447004, 453900, 281425, 281267, 405154. Utilizzando una tavola hash con 10 posizioni e la funzione $K \pmod{10}$, la distribuzione risulta:

* Posizione 0: ospita 240810, ma collide con 453900.
* Posizione 2: ospita 240772.
* Posizione 4: ospita 447004, ma collide con 405154.
* Posizione 5: ospita 281425.
* Posizione 6: ospita 449726.
* Posizione 7: ospita 281267.
	* Le chiavi 453900 e 405154 rimangono inizialmente "escluse" dalla tavola principale.

Per la **gestione delle collisioni**, si impiegano diverse tecniche:

1. **Posizioni successive disponibili**: si cerca il primo slot libero dopo quello calcolato.
2. **Tabella di overflow**: i record collidenti vengono inseriti in un'area separata gestita tramite liste collegate.
3. **Funzioni hash alternative**: si applica una seconda funzione in caso di collisione.

Il "costo" di queste strutture viene valutato in termini di accessi medi. In un esempio con 40 record e una tavola da 50 posizioni, si potrebbero avere 20 record senza collisioni, 5 gruppi di collisioni da 2 record, 2 gruppi da 3 e 1 gruppo da 4. Il numero medio di accessi si calcola come: $(28 \times 1 + 8 \times 2 + 3 \times 3 + 1 \times 4) / 40 = 1,425$ Sebbene le collisioni siano quasi sempre presenti, la probabilità di collisioni multiple decresce rapidamente al crescere della loro numerosità, mantenendo la molteplicità media molto bassa.

Il concetto si estende al **File Hash** organizzato per blocchi. Qui, ogni "indirizzo" della funzione hash punta a un intero blocco che può contenere più record (fattore di blocco $F$). Lo spazio degli indirizzi si riduce: se $F = 10$, per 50 posizioni totali si possono usare solo 5 blocchi (funzione $\pmod{5}$ invece di $\pmod{50}$). Le collisioni che eccedono la capacità del blocco (_overflow_) sono tipicamente gestite tramite il collegamento di nuovi blocchi.

Riprendendo l'esempio degli 8 record con $F = 5$ e funzione $K \pmod{2}$:

* **Blocco 0** (chiavi pari): riceve 240810, 453900, 240772, 405154, 447004. Avendo raggiunto il limite di 5 record, la chiave successiva con resto 0 (449726) deve andare in overflow.
* **Blocco 1** (chiavi dispari): riceve 281425, 281267.

Il confronto tra tavola hash e file hash mostra che quest'ultimo è più efficiente. Con 40 record:

* Tavola hash (50 posizioni): 12 record in overflow, costo medio 1,425.
* File hash (5 blocchi da 10): solo 2 record in overflow, costo medio 1,05. Questa efficienza superiore deriva dal fatto che il blocco funge da "ammortizzatore" per le collisioni locali.

Le stime statistiche confermano che all'aumentare del fattore di blocco $F$, la lunghezza media delle catene di overflow e il costo di accesso diminuiscono drasticamente, anche con coefficienti di riempimento elevati. Ad esempio, con un riempimento del $90%$ ($T/(F \times B) = 0.9$):

* Se $F = 1$, il costo è $5,495$.
* Se $F = 10$, il costo scende a $1,345$.

In conclusione, il file hash è l'organizzazione più efficiente per l'accesso puntuale (uguaglianza), con un costo medio vicino all'unità. Tuttavia, non è adatto a ricerche per intervalli e tende a degradare se lo spazio diventa saturo. Per ovviare alla rigidità delle dimensioni, si ricorre a tecniche di **hashing dinamico**, come l'hashing estendibile o lineare, che permettono al file di adattarsi alla variazione del numero di record nel tempo.

## Analisi delle collisioni e organizzazione delle strutture di accesso

L'efficienza di un file hash è strettamente legata alla gestione delle collisioni e alla lunghezza delle catene di overflow. La stima della lunghezza media di queste catene varia in funzione di quattro parametri fondamentali: il numero totale di record esistenti ($T$), il numero di blocchi allocati ($B$), il fattore di blocco ($F$) e il coefficiente di riempimento, definito dal rapporto $T/(F \times B)$. All'aumentare del coefficiente di riempimento, la probabilità di collisione cresce, influenzando direttamente il costo di accesso.

Dalle analisi statistiche emerge che, mantenendo un coefficiente di riempimento costante, un fattore di blocco $F$ più elevato riduce drasticamente la lunghezza media delle catene di overflow. Ad esempio, con un coefficiente di riempimento del $0.9$ (file molto pieno), se $F=1$ la lunghezza media delle catene è di $4.495$, mentre se $F=10$ scende a soli $0.345$. Il costo di un'operazione, inteso come numero di accessi necessari, è calcolato sommando l'unità (l'accesso al blocco primario) alla lunghezza media delle catene di overflow. Nelle stesse condizioni di riempimento ($0.9$), il costo passa da $5.495$ per $F=1$ a $1.345$ per $F=10$. In generale, un file hash ben progettato mantiene un costo medio di poco superiore all'unità. Sebbene il caso peggiore teorico sia estremamente costoso, la sua probabilità statistica è talmente bassa da poter essere ignorata nelle applicazioni reali.

Il file hash rappresenta l'organizzazione più efficiente per l'accesso diretto basato su valori della chiave con condizioni di uguaglianza, operazione definita accesso puntuale. Tuttavia, presenta limitazioni strutturali: non è efficiente per le ricerche basate su intervalli e tende a degenerare se lo spazio sovrabbondante si riduce. Queste strutture funzionano correttamente solo con file la cui dimensione non varia sensibilmente nel tempo, a meno di non ricorrere a tecniche di hashing dinamico, come l'hashing estendibile o lineare.

## Hashing estendibile

L'hashing estendibile supera la rigidità delle strutture statiche poiché il numero di blocchi (o bucket) non è predefinito. Questa tecnica utilizza una directory dei blocchi che può variare di dimensione, sebbene solitamente cresca in modo lento. Il sistema si basa sulla rappresentazione binaria del valore di hash ottenuto dalla chiave.

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

* **Indice Primario**: definito su un campo che rispetta l'ordinamento fisico della memorizzazione del file (detto anche indice di cluster). Esiste al più un indice primario per file.
* **Indice Secondario**: definito su un campo il cui ordinamento è diverso da quello di memorizzazione. Un file può avere molteplici indici secondari.

Un'ulteriore distinzione riguarda la copertura dei valori:

* **Indice Denso**: contiene un riferimento per ogni singolo valore della chiave presente nel file. Gli indici secondari devono necessariamente essere densi.
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

* $B/R = 40$ record per blocco.
* $N_F = 1.000.000 / 40 = 25.000$ blocchi.
* $B/(K+P) = 4000 / 8 = 500$ record indice per blocco.
* $N_D = 1.000.000 / 500 = 2.000$ blocchi.
* $N_S = 25.000 / 500 = 50$ blocchi.

L'indice sparso risulta significativamente più piccolo ($50$ blocchi contro i $25.000$ del file), facilitando enormemente la ricerca. Gli indici garantiscono un accesso diretto efficiente (puntuale e per intervalli) e una scansione sequenziale ordinata. Tuttavia, rendono inefficienti le modifiche, gli inserimenti e le eliminazioni a causa della rigidità dell'ordinamento. Per mitigare questi problemi si utilizzano blocchi di overflow, marcature per l'eliminazione (_tombstones_), riempimento parziale o riorganizzazioni periodiche.

## Indici multilivello e B-tree

Poiché gli indici sono file ordinati, è possibile costruire indici sugli indici per evitare scansioni sequenziali tra i blocchi dell'indice stesso. Questo crea una struttura multilivello dove l'indice di livello superiore è sempre primario e sparso rispetto a quello inferiore. Il processo prosegue fino a ottenere un livello composto da un solo blocco (la radice).

Il numero di blocchi al livello $j$ è dato da: $N_j = N_{j-1} / (B/(K+P))$ Il numero di blocchi a cui un blocco fa riferimento è detto _fan-out_. Negli indici multilivello la profondità è solitamente ridotta (tra 3 e 5). Con un fan-out di $500$, un indice denso di $2.000$ blocchi richiede solo 3 livelli ($N_1=2000, N_2=4, N_3=1$), mentre uno sparso di $50$ blocchi ne richiede solo 2 ($N_1=50, N_2=1$).

I DBMS moderni utilizzano strutture più sofisticate come i **B-tree** per gestire l'elevata dinamicità. Un B-tree è un albero di ricerca bilanciato in cui ogni nodo corrisponde a un blocco. Caratteristiche principali:

* Mantenimento del perfetto bilanciamento (foglie allo stesso livello).
* Riempimento parziale dei nodi (mediamente $70%$, con un minimo garantito del $50%$).
* In un albero di ordine $P$, ogni nodo ha fino a $P$ figli e $P-1$ etichette ordinate.
* L'i-esimo sottoalbero contiene chiavi $K$ tali che $K_{i-1} \leq K < K_i$.

Negli inserimenti, se una foglia è piena, avviene uno **split** (divisione del nodo) che può propagarsi verso l'alto fino alla radice. Le eliminazioni possono causare un **merge** (fusione di nodi) se il riempimento scende sotto la soglia.

Si distinguono due varianti:

1. **B+ tree**: Tutte le chiavi e i riferimenti ai dati compaiono nelle foglie. Le foglie sono collegate tra loro in una lista per ottimizzare le ricerche su intervalli. I nodi intermedi contengono solo chiavi per guidare la ricerca. È la struttura più usata nei DBMS.
2. **B tree**: Le chiavi e i riferimenti ai dati possono trovarsi anche nei nodi intermedi e non vengono ripetuti nelle foglie.

Il costo di ricerca in queste strutture è pari alla profondità dell'albero. Grazie alla bufferizzazione della radice e dei primi livelli, il costo reale di un accesso diretto scende spesso a soli $2$ o $3$ accessi fisici.

# Organizzazione fisica ed esecuzione delle interrogazioni

L'architettura di un sistema di gestione di basi di dati (DBMS) è strutturata per trasformare una richiesta espressa in un linguaggio dichiarativo ad alto livello in operazioni fisiche sulla memoria secondaria. Il processo segue una gerarchia precisa di moduli: il **Gestore delle interrogazioni** riceve istruzioni in linguaggio SQL e determina la strategia di esecuzione (scansione, accesso diretto o ordinamento). Questa strategia viene passata al **Gestore dei metodi d'accesso**, che effettua una cosiddetta "lettura virtuale". Questo livello interagisce con il **Gestore del buffer**, responsabile del coordinamento tra memoria principale e secondaria tramite "letture fisiche". Il comando giunge infine al **Gestore della memoria secondaria**, che opera direttamente sui dispositivi di memorizzazione fisica.

L'esecuzione e l'ottimizzazione delle interrogazioni sono affidate al **Query Processor**, o Ottimizzatore. La necessità di questo modulo deriva dal concetto di ==indipendenza dei dati==: le interrogazioni SQL descrivono insiemi di ennuple con pochissima proceduralità, lasciando al sistema il compito di scegliere la migliore strategia realizzativa tra diverse alternative possibili. Il **processo di esecuzione** si articola in fasi **sequenziali**:

1. **Analisi lessicale, sintattica e semantica**: trasforma il codice SQL in un'espressione algebrica, verificando la correttezza rispetto allo schema contenuto nel **Catalogo**.
2. **Ottimizzazione algebrica**: applica trasformazioni all'espressione algebrica per renderla più efficiente.
3. **Ottimizzazione basata sui costi**: trasforma l'espressione algebrica ottimizzata in un **piano di accesso** (o piano di esecuzione), consultando le strutture fisiche e i profili delle relazioni memorizzati nel Catalogo.

Il **Catalogo** contiene i cosiddetti "Profili" delle relazioni, ovvero informazioni quantitative aggiornate periodicamente (tramite comandi come `update statistics`). Tali profili includono la cardinalità di ciascuna relazione, le dimensioni delle ennuple e dei singoli valori, il numero di valori distinti degli attributi e i valori minimi e massimi. Questi dati sono fondamentali nella fase finale dell'ottimizzazione per stimare i costi delle operazioni e le dimensioni dei risultati intermedi.

## Dall'SQL all'algebra e ottimizzazione euristica

Un'interrogazione SQL viene semplificata nei suoi componenti fondamentali: il prodotto cartesiano (clausola `FROM`), la selezione (clausola `WHERE`) e la proiezione (clausola `SELECT`). 

Ad esempio, la query: `SELECT A , E FROM R1, R3, R2 WHERE C=D AND B=20 AND F=G AND I>2` può essere tradotta nel predicato algebrico: $\pi_{AE}(\sigma_{C=D \wedge B=20 \wedge F=G \wedge I>2}((R1 \bowtie R2) \bowtie R3))$

Le interrogazioni vengono rappresentate graficamente tramite **alberi**, dove le foglie sono i dati (relazioni o file) e i nodi intermedi sono gli operatori (prima algebrici, poi operatori di accesso effettivi). L'ottimizzazione algebrica utilizza euristiche basate sulla nozione di equivalenza: due espressioni sono equivalenti se producono lo stesso risultato per ogni istanza della base di dati. Il DBMS cerca l'espressione equivalente meno costosa seguendo l'euristica fondamentale di eseguire selezioni e proiezioni il prima possibile per ridurre le dimensioni dei risultati intermedi. Questo concetto è noto come "push selections down" e "push projections down".

Le regole specifiche per l'ottimizzazione algebrica includono:

* Decomporre le selezioni congiuntive in selezioni atomiche successive.
* ==Anticipare il più possibile le selezioni, specialmente le più selettive.==
* ==Combinare prodotti cartesiani e selezioni per formare join, riordinando se necessario gli operandi==.
* ==Anticipare le proiezioni==, anche introducendone di nuove, per limitare la dimensione dei record nei risultati intermedi (particolarmente utile se i risultati vengono materializzati).

## Esecuzione delle operazioni 

I DBMS offrono operatori fisici che implementano gli operatori algebrici. Gli operatori fondamentali sono la **scansione** e l'**accesso diretto**, seguiti da operazioni di livello più alto come l'_ordinamento_ e il _join_.

==La **Scansione** consiste nell'accesso sequenziale a una tabella.== Permette la lettura completa, la selezione su qualunque predicato, la proiezione (senza eliminazione di duplicati) e la gestione delle ennuple correnti (inserimento, modifica, eliminazione). I metodi offerti sono `open`, `next`, `read`, `modify`, `insert`, `delete` e `close`. Il **costo** è **lineare** rispetto al **numero di blocchi** del file, ovvero $O(N)$.

==L'**Accesso diretto** è possibile solo se supportato da strutture fisiche come indici o hash.== L'accesso basato su indice è utile per selezioni puntuali ($A_{i}=v$) o su intervallo ($v_{1} \leq A_{i} \leq v_{2}$), a patto che l'indice sia selettivo (ossia che il risultato contenga poche ennuple rispetto alla relazione di partenza). Il **costo** ha **due** componenti: la _profondità dell'indice_ (logaritmica) e l'_accesso ai record effettivi_ (che dipende dalla selettività). In caso di **selezione congiuntiva** con più indici disponibili, il sistema può usare l'indice più selettivo e valutare l'altra condizione successivamente, oppure usare entrambi gli indici per ottenere liste di indirizzi ed eseguirne l'intersezione. Se gli indirizzi sono ai record, l'intersezione identifica esattamente i record cercati; se sono ai blocchi, identifica i blocchi potenzialmente utili. Per la **selezione disgiuntiva**, **se entrambi i campi sono selettivi e indicizzati**, si esegue l'**unione** dei risultati; **se anche uno solo non è selettivo**, l'uso dell'indice è **inutile** e si preferisce la scansione sequenziale.

Il costo degli indici su campi non chiave è composto dalla profondità dell'indice e il costo dell'accesso ai record:

* **Indice secondario**: i record sono sparpagliati, quindi potrebbe servire un accesso per ogni record trovato.
* **Indice primario**: i record sono fisicamente consecutivi, quindi il costo è approssimativamente pari al numero di record trovati diviso il fattore di blocco.

L'**Accesso diretto basato su hash** è estremamente efficiente per interrogazioni puntuali, con un costo approssimabile a una costante, ma non per ricerche su intervallo. Per predicati congiuntivi e disgiuntivi, vale lo stesso discorso fatto per gli indici.

## Ordinamento e Merge-Sort esterno

L'ordinamento è un'operazione cruciale per produrre risultati ordinati (`ORDER BY`), eliminare duplicati (`DISTINCT`), preparare raggruppamenti (`GROUP BY`) o join. Poiché le basi di dati spesso superano la dimensione della memoria principale, si utilizza il **Merge-sort esterno**.

L'algoritmo tradizionale con tre buffer (due di input e uno di output) segue un approccio "bottom-up":

1. Si divide il file in porzioni che entrano in memoria.
2. Si ordina ogni porzione in memoria e la si scrive su disco (creazione dei _run_).
3. Si fondono (_merge_) le porzioni a coppie fino a ordinare l'intero file. Il costo complessivo per un file di $N$ blocchi è circa $2 \times N \times \log_{2}N$ accessi al disco, poiché ogni passo di merge richiede di leggere e scrivere l'intero file.

Se è disponibile molta memoria (molte pagine di buffer $P$), le prestazioni migliorano riducendo il numero di passi di merge. Inizialmente si ordinano run composti da $P$ blocchi. Successivamente, si esegue un merge a più vie, fondendo contemporaneamente tante porzioni quante sono le pagine del buffer disponibili. Con $P$ buffer, è possibile ordinare un file in:

* Una passata se $P \geq N$.
* Due passate se $P^{2} \geq N$ (ovvero $P \geq \sqrt{N}$), con un costo di $3 \times N$ (si legge il file, lo si scrive ordinato in run, si rilegge per il merge finale senza memorizzare il risultato intermedio).
* Tre passate se $P^{3} \geq N$. 

==In generale, con $i$ passate si può ordinare un file di $P^{i}$ blocchi. Il numero di passate necessario è il più piccolo intero $i$ per cui $P \geq \sqrt[i]{N}$.==

Ad esempio, per un file di $N=10.000.000$ di blocchi con un buffer di $10.000$ pagine ($100MB$), si potrebbero ordinare $10.000$ blocchi alla volta ottenendo $1000$ porzioni ordinate. Fondendo queste porzioni con un merge a $1000$ vie, l'ordinamento si completerebbe in un unico passo di merge (due passate totali). In sintesi, se $P \geq \sqrt{N}$, l'operazione richiede $3 \times N$ accessi.

> Vedere Esercizio 5 di [[26/02/2013]{.underline}](https://tagd.inf.uniroma3.it/compitiPDF/20130226bdIIsoluz.pdf)
