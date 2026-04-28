import psycopg2
from psycopg2 import errors
import threading
import time
import os

# Parametri di connessione dal docker-compose
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASS = os.environ.get("DB_PASS", "password")
DB_NAME = os.environ.get("DB_NAME", "atzeni_db")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )


def reset_database():
    """Riporta il database allo stato iniziale prima di ogni test."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM impiegati;")
    cur.execute(
        "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (101, 'Rossi', 1), (102, 'Bruni', 2);"
    )
    conn.commit()
    conn.close()


def log_result(scenario_name, message):
    print(f"[{scenario_name}] {message}")
    with open("test_results.log", "a") as f:
        f.write(f"[{scenario_name}] {message}\n")


# ==========================================
# SCENARIO 1: LOST UPDATE
# ==========================================
def tx_lost_update(nome_tx, isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("SELECT conteggio FROM impiegati WHERE matricola=101;")
        row = cur.fetchone()
        count = row[0] if row is not None else 0
        log_result("LOST_UPDATE", f"{nome_tx} ha letto {count=}")

        time.sleep(1)

        cur.execute(
            f"UPDATE impiegati SET conteggio = {count} + 1 WHERE matricola=101;"
        )
        log_result("LOST_UPDATE", f"{nome_tx} ha impostato count a {count + 1}")
        # 4. Fai commit
        conn.commit()
    except Exception as e:
        # Suggerimento: cattura errors.SerializationFailure per quando testerai con REPEATABLE READ
        conn.rollback()
        log_result("LOST_UPDATE", f"{nome_tx} Errore: {e}")
    finally:
        conn.close()


def test_lost_update():
    reset_database()
    log_result(
        "LOST_UPDATE", "--- INIZIO TEST LOST UPDATE ISOLATION_LEVEL_READ_COMMITTED---"
    )

    livello = psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED

    t1 = threading.Thread(target=tx_lost_update, args=("Tx1", livello))
    t2 = threading.Thread(target=tx_lost_update, args=("Tx2", livello))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    reset_database()
    log_result(
        "LOST_UPDATE", "--- INIZIO TEST LOST UPDATE ISOLATION_LEVEL_REPEATABLE_READ---"
    )

    livello = psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ

    t1 = threading.Thread(target=tx_lost_update, args=("Tx1", livello))
    t2 = threading.Thread(target=tx_lost_update, args=("Tx2", livello))

    t1.start()
    t2.start()
    t1.join()
    t2.join()


# ==========================================
# SCENARIO 2: NON-REPEATABLE READ
# ==========================================
def tx_non_repeatable_read_t1(isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 102")
        row = cur.fetchone()
        count_prima = row[0] if row is not None else 0
        log_result("NON_REPEATABLE_READ", f"T1 count prima {count_prima}")

        time.sleep(2)

        cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 102")
        row = cur.fetchone()
        count_dopo = row[0] if row is not None else 0
        log_result("NON_REPEATABLE_READ", f"T1 count dopo {count_dopo}")

        conn.commit()
    except Exception as e:
        conn.rollback()
        log_result("NON_REPEATABLE_READ", f"T1 Errore: {e}")
    finally:
        conn.close()


def tx_non_repeatable_read_t2():
    # T2 usa il livello di default (READ COMMITTED) perché fa solo una scrittura
    conn = get_connection()
    cur = conn.cursor()
    try:
        time.sleep(0.5)

        cur.execute(
            "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = 102;"
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        log_result("NON_REPEATABLE_READ", f"T2 Errore: {e}")
    finally:
        conn.close()


def test_non_repeatable_read():
    reset_database()
    log_result(
        "NON_REPEATABLE_READ", "--- INIZIO TEST NON-REPEATABLE READ READ_COMMITTED---"
    )

    livello_t1 = psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED

    t1 = threading.Thread(target=tx_non_repeatable_read_t1, args=(livello_t1,))
    t2 = threading.Thread(target=tx_non_repeatable_read_t2)

    t1.start()
    t2.start()
    t1.join()
    t2.join()
    reset_database()

    log_result(
        "NON_REPEATABLE_READ", "--- INIZIO TEST NON-REPEATABLE READ REPEATABLE READS---"
    )

    livello_t1 = psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ

    t1 = threading.Thread(target=tx_non_repeatable_read_t1, args=(livello_t1,))
    t2 = threading.Thread(target=tx_non_repeatable_read_t2)

    t1.start()
    t2.start()
    t1.join()
    t2.join()


# ==========================================
# SCENARIO 3: PHANTOM READ
# ==========================================
def tx_phantom_read_t1(isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) FROM impiegati WHERE conteggio > 0;")
        row = cur.fetchone()
        count_prima = row[0] if row is not None else 0
        log_result(
            "PHANTOM_READ", f"T1 (Prima lettura): Trovati {count_prima} impiegati."
        )

        time.sleep(2)

        cur.execute("SELECT count(*) FROM impiegati WHERE conteggio > 0;")
        row = cur.fetchone()
        count_dopo = row[0] if row is not None else 0
        log_result(
            "PHANTOM_READ", f"T1 (Seconda lettura): Trovati {count_dopo} impiegati."
        )

        if count_prima == count_dopo:
            log_result(
                "PHANTOM_READ",
                "CONCLUSIONE: Phantom Read PREVENUTO! (Tipico di Postgres in REPEATABLE READ)",
            )
        else:
            log_result(
                "PHANTOM_READ",
                "CONCLUSIONE: Phantom Read AVVENUTO! (Normale in READ COMMITTED)",
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        log_result("PHANTOM_READ", f"T1 Errore: {e}")
    finally:
        conn.close()


def tx_phantom_read_t2():
    conn = get_connection()
    cur = conn.cursor()
    try:
        time.sleep(0.5)

        cur.execute(
            "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (105, 'Bianchi', 3);"
        )
        conn.commit()
        log_result(
            "PHANTOM_READ", "T2: Nuovo impiegato 'Bianchi' inserito con successo."
        )
    except Exception as e:
        conn.rollback()
        log_result("PHANTOM_READ", f"T2 Errore: {e}")
    finally:
        conn.close()


def test_phantom_read():
    # ISOLATION_LEVEL_READ_COMMITTED,  Phantom Read
    # ISOLATION_LEVEL_REPEATABLE_READ, no, Postgres lo blocca
    reset_database()
    log_result("PHANTOM_READ", "--- INIZIO TEST PHANTOM READ READ_COMMITTED---")

    livello_t1 = psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED

    t1 = threading.Thread(target=tx_phantom_read_t1, args=(livello_t1,))
    t2 = threading.Thread(target=tx_phantom_read_t2)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    reset_database()
    log_result("PHANTOM_READ", "--- INIZIO TEST PHANTOM READ REPEATABLE_READ---")

    livello_t1 = psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ

    t1 = threading.Thread(target=tx_phantom_read_t1, args=(livello_t1,))
    t2 = threading.Thread(target=tx_phantom_read_t2)

    t1.start()
    t2.start()
    t1.join()
    t2.join()


# ==========================================
# SCENARIO 4: WRITE SKEW (Esercizio Slide)
# ==========================================
def tx_write_skew(nome_tx, matricola, cognome, isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        # Lettura
        cur.execute("SELECT count(*) FROM impiegati;")
        row = cur.fetchone()
        count = row[0] if row is not None else 0
        log_result("WRITE_SKEW", f"{nome_tx} ha letto count = {count}")

        time.sleep(1)  # Simula concorrenza forzando l'intreccio

        cur.execute(
            "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (%s, %s, %s)",
            (matricola, cognome, count),
        )
        conn.commit()
        log_result("WRITE_SKEW", f"{nome_tx} COMMIT completato con successo.")
    except errors.SerializationFailure as e:
        conn.rollback()
        log_result(
            "WRITE_SKEW",
            f"{nome_tx} ABORTITA per Serialization Failure (Errore 40001)! + e={e}",
        )
    finally:
        conn.close()


def test_write_skew():
    reset_database()
    log_result("WRITE_SKEW", "--- INIZIO TEST WRITE SKEW (Livello: SERIALIZABLE) ---")

    livello = psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE

    t1 = threading.Thread(target=tx_write_skew, args=("Tx1", 103, "Verdi", livello))
    t2 = threading.Thread(target=tx_write_skew, args=("Tx2", 104, "Neri", livello))

    t1.start()
    t2.start()
    t1.join()
    t2.join()


# ==========================================
# SCENARIO 5: DEADLOCK
# ==========================================
def tx_deadlock_1():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = 101;"
        )
        log_result("DEADLOCK", "Tx1 ha bloccato Rossi (101).")
        time.sleep(1)
        log_result("DEADLOCK", "Tx1 prova a bloccare Bruni (102)...")
        cur.execute(
            "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = 102;"
        )
        conn.commit()
    except errors.DeadlockDetected:
        conn.rollback()
        log_result("DEADLOCK", "Tx1 ABORTITA dal DBMS per Deadlock (Errore 40P01)!")
    finally:
        conn.close()


def tx_deadlock_2():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = 102;"
        )
        log_result("DEADLOCK", "Tx2 ha bloccato Bruni (102).")
        time.sleep(1)
        log_result("DEADLOCK", "Tx2 prova a bloccare Rossi (101)...")
        cur.execute(
            "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = 101;"
        )
        conn.commit()
    except errors.DeadlockDetected:
        conn.rollback()
        log_result("DEADLOCK", "Tx2 ABORTITA dal DBMS per Deadlock (Errore 40P01)!")
    finally:
        conn.close()


def test_deadlock():
    reset_database()
    log_result("DEADLOCK", "--- INIZIO TEST DEADLOCK ---")
    t1 = threading.Thread(target=tx_deadlock_1)
    t2 = threading.Thread(target=tx_deadlock_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


# ==========================================
# SCENARIO 6: DIRTY READ (Lettura Sporca)
# ==========================================
def tx_dirty_read_t1(isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("UPDATE impiegati SET conteggio = 999 WHERE matricola = 101;")
        log_result(
            "DIRTY_READ",
            "T1 ha modificato il conteggio a 999 ma NON HA ANCORA FATTO COMMIT.",
        )

        time.sleep(2)  # Aspettiamo per dare tempo a T2 di provare a leggere

        # Facciamo volutamente un rollback!
        conn.rollback()
        log_result("DIRTY_READ", "T1 ha fatto ROLLBACK. La modifica a 999 è annullata.")
    except Exception as e:
        conn.rollback()
        log_result("DIRTY_READ", f"T1 Errore: {e}")
    finally:
        conn.close()


def tx_dirty_read_t2(isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        time.sleep(0.5)  # Diamo tempo a T1 di fare l'UPDATE

        cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 101;")
        row = cur.fetchone()
        count = row[0] if row is not None else 0
        log_result("DIRTY_READ", f"T2 ha letto il conteggio: {count}")

        if count == 999:
            log_result(
                "DIRTY_READ",
                "CONCLUSIONE: DIRTY READ AVVENUTO! (Questo in Postgres non dovrebbe succedere)",
            )
        else:
            log_result(
                "DIRTY_READ",
                "CONCLUSIONE: DIRTY READ PREVENUTO! (Postgres ignora il READ UNCOMMITTED e legge l'ultimo dato confermato)",
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        log_result("DIRTY_READ", f"T2 Errore: {e}")
    finally:
        conn.close()


def test_dirty_read():
    reset_database()
    log_result(
        "DIRTY_READ", "--- INIZIO TEST DIRTY READ (FORZANDO READ_UNCOMMITTED) ---"
    )

    # Chiediamo esplicitamente il READ_UNCOMMITTED
    livello = psycopg2.extensions.ISOLATION_LEVEL_READ_UNCOMMITTED

    t1 = threading.Thread(target=tx_dirty_read_t1, args=(livello,))
    t2 = threading.Thread(target=tx_dirty_read_t2, args=(livello,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    if os.path.exists("test_results.log"):
        os.remove("test_results.log")

    print("Attendiamo qualche secondo che Postgres sia pronto...")
    time.sleep(3)

    test_lost_update()
    print("\n")
    test_non_repeatable_read()
    print("\n")
    test_phantom_read()
    print("\n")
    test_write_skew()
    print("\n")
    test_deadlock()
    print("\n")
    test_dirty_read()

    print("\nTest completati. I risultati sono salvati in test_results.log")
