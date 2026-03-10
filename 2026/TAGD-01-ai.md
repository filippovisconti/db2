---
title: "TAGD-01-ai"
author:
  - Filippo Visconti
template:
  - template.tex
---


# Organizzazione fisica e gestione del buffer

## Architettura di base di un DBMS

Un DBMS è organizzato come una **struttura a livelli**, in cui ogni componente ha il compito di gestire un aspetto specifico dell’esecuzione delle interrogazioni e dell’accesso ai dati.

Il livello più alto è il **gestore delle interrogazioni**, che riceve comandi SQL e li traduce in operazioni eseguibili dal sistema.

Per eseguire queste operazioni il sistema utilizza diversi componenti:

* il **gestore dei metodi di accesso**, che implementa operazioni come scansione sequenziale, accesso diretto e ordinamento;

* il **gestore del buffer**, che consente di leggere i dati in modo virtuale mantenendo in memoria le pagine più utili;

* il **gestore della memoria secondaria**, che si occupa della lettura e scrittura fisica dei dati sul disco.

In sostanza, l’esecuzione di una query segue questo flusso:

1. il sistema riceve una query SQL,

2. la query viene analizzata e trasformata in un piano di esecuzione,

3. il piano utilizza metodi di accesso ai dati,

4. i dati vengono recuperati tramite il buffer manager,

5. se necessario vengono effettuate operazioni di lettura o scrittura su disco.

Questa organizzazione è fondamentale perché **l’accesso al disco è molto più lento rispetto all’accesso alla memoria principale**, quindi il DBMS cerca di ridurre il più possibile le operazioni di I/O.

# Architettura di SimpleDB

Nel sistema didattico **SimpleDB** l’architettura è suddivisa in diversi moduli.

Il componente **Remote** riceve le richieste dal client e passa le query SQL al planner.

Il **Planner** ha il compito di coordinare l’elaborazione della query. Per farlo chiama il **Parser**, che esegue l’analisi sintattica della query SQL, e poi costruisce il piano di esecuzione che verrà eseguito dal sistema.

Il componente **Query** riceve il piano e lo esegue, richiamando le operazioni necessarie sui dati.

Il modulo **Metadata** gestisce gli schemi delle tabelle, cioè le informazioni sulla struttura dei dati.

Il modulo **Record** gestisce i blocchi contenenti i record delle tabelle.

Il componente **Transaction** si occupa della gestione della concorrenza tra transazioni.

Il **Buffer manager** mantiene in memoria alcune pagine di dati per ridurre il numero di accessi al disco.

Il **Log manager** registra le operazioni eseguite in modo da garantire affidabilità e recupero in caso di errore.

Infine il **File manager** si occupa delle operazioni di lettura e scrittura delle pagine su disco.

# Il buffer: una metafora

Il funzionamento del buffer può essere spiegato con una metafora molto semplice.

Immaginiamo di avere molti documenti conservati in un classificatore. Quando dobbiamo lavorare su alcuni di essi, li spostiamo sulla scrivania per averli a portata di mano. Una volta terminato il lavoro, possiamo rimetterli nel classificatore.

In questa analogia:

* il **classificatore** rappresenta il disco,

* la **scrivania** rappresenta la memoria principale,

* i **documenti sulla scrivania** corrispondono alle pagine mantenute nel buffer.

Questo esempio mostra che non ha senso lavorare direttamente sul classificatore ogni volta che serve un documento: è molto più efficiente tenerlo temporaneamente sulla scrivania.

# Il principio di località

Il buffer sfrutta il **principio di località**. Questo principio afferma che i dati utilizzati recentemente hanno un’elevata probabilità di essere riutilizzati nel prossimo futuro. Si tratta di un comportamento tipico dei programmi e delle interrogazioni sui database.

Esistono due forme principali di località:

* **località temporale**, secondo cui i dati usati recentemente tenderanno a essere riutilizzati presto;

* **località spaziale**, secondo cui se un dato viene utilizzato è probabile che vengano utilizzati anche dati vicini.

Il buffer manager sfrutta questo comportamento mantenendo in memoria i blocchi che sono stati usati più recentemente o che potrebbero essere utilizzati di nuovo.

# Gestione dei buffer

La **gestione del buffer** ha lo scopo di ridurre il numero di accessi alla memoria secondaria. Poiché gli accessi al disco sono molto costosi in termini di tempo, mantenere alcune pagine in memoria principale consente di migliorare significativamente le prestazioni del sistema.

Il buffer manager mantiene in memoria un insieme di pagine che rappresentano copie temporanee dei blocchi presenti su disco. Quando un componente del DBMS ha bisogno di accedere a un blocco, il buffer manager verifica se il blocco è già presente nel buffer. Se lo è, l’accesso avviene direttamente in memoria; altrimenti il blocco deve essere letto dal disco.

# Dati gestiti dal buffer manager

Il buffer manager gestisce principalmente **pagine di dati**. Una pagina è l’unità di trasferimento tra disco e memoria principale.

Ogni pagina nel buffer è associata ad alcune informazioni di controllo, tra cui:

* il **blocco su disco** a cui la pagina corrisponde;

* un **contatore di utilizzo**, che indica quante operazioni stanno usando quella pagina;

* un **flag di modifica** (dirty bit), che indica se la pagina è stata modificata e quindi deve essere riscritta su disco.

Queste informazioni permettono al sistema di sapere quando una pagina può essere rimossa dal buffer e se deve essere salvata prima sul disco.

# Funzioni del buffer manager

Il buffer manager offre diverse funzioni ai livelli superiori del DBMS.

Una delle operazioni principali è la **fix**, che serve a richiedere una pagina nel buffer. Quando un componente richiede una pagina, il buffer manager verifica se è già presente nel buffer. Se la pagina è già disponibile, viene restituita immediatamente; altrimenti deve essere caricata dal disco.

Un’altra operazione importante è la **unfix**, che segnala che un componente ha terminato di usare una pagina.

Queste operazioni permettono al sistema di gestire correttamente l’uso concorrente delle pagine.

# Esecuzione della fix

Quando viene richiesta una pagina tramite l’operazione di fix, il buffer manager esegue una serie di passi.

Prima controlla se la pagina richiesta è già presente nel buffer. Se lo è, aumenta il contatore di utilizzo e restituisce la pagina.

Se la pagina non è presente nel buffer, il sistema deve caricarla dal disco. Se nel buffer è disponibile uno spazio libero, la pagina viene semplicemente caricata.

Se invece il buffer è pieno, il sistema deve scegliere una pagina da rimuovere. In questo caso entra in gioco una **strategia di rimpiazzo**.

Se la pagina da rimuovere è stata modificata, deve essere prima scritta su disco per evitare la perdita di dati.

# Strategie di rimpiazzo

Quando il buffer è pieno e deve essere caricata una nuova pagina, il sistema deve scegliere quale pagina eliminare dal buffer.

Questa scelta viene effettuata tramite una **politica di rimpiazzo**.

Una strategia molto semplice è la strategia **NAIF**, che seleziona una pagina in modo arbitrario tra quelle disponibili.

Una strategia più efficace è **LRU (Least Recently Used)**. Questa strategia rimuove la pagina che non viene utilizzata da più tempo. L’idea è basata sul principio di località: se una pagina non è stata usata recentemente, è meno probabile che venga usata nel prossimo futuro.

LRU tende a funzionare bene nella pratica perché sfrutta il comportamento tipico dei programmi.

# Blocchi e record

Nel DBMS i dati sono organizzati in **record**, che rappresentano le singole tuple delle relazioni. I record non vengono memorizzati individualmente sul disco, ma sono raggruppati all’interno di **blocchi** (o pagine).

Il blocco è quindi l’unità di trasferimento tra memoria secondaria e memoria principale. Quando il sistema deve accedere a un record, in realtà legge l’intero blocco che lo contiene.

Questa scelta è dovuta al fatto che le operazioni di I/O sono molto costose e quindi conviene trasferire una quantità relativamente grande di dati alla volta.

# Record e blocchi

Un blocco può contenere più record. Il numero di record che possono essere memorizzati in un blocco dipende dalla dimensione del blocco e dalla dimensione dei record.

Per questo motivo il DBMS deve gestire attentamente l’organizzazione interna dei blocchi per utilizzare lo spazio in modo efficiente.

# Fattore di blocco

Il **fattore di blocco** indica quanti record possono essere memorizzati all’interno di un blocco.

Formalmente è il rapporto tra:

* la dimensione del blocco

* la dimensione del record

Sapere quanti record entrano in un blocco è molto importante per stimare il **costo delle operazioni di accesso ai dati**, perché il numero di blocchi da leggere influisce direttamente sul numero di accessi al disco.
