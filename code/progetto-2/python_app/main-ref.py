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
    try:
        cur.execute("DELETE FROM impiegati;")
        cur.execute(
            "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (101, 'Rossi', 1), (102, 'Bruni', 2);"
        )
        conn.commit()
    finally:
        conn.close()


def log_result(scenario_name, message):
    log_line = f"[{scenario_name}] {message}"
    print(log_line)
    with open("test_results.log", "a") as f:
        f.write(log_line + "\n")


def run_test_scenario(
    scenario_name, title, t1_func, t1_args=(), t2_func=None, t2_args=()
):
    reset_database()
    log_result(scenario_name, f"--- {title} ---")

    t1 = threading.Thread(target=t1_func, args=t1_args)
    t2 = threading.Thread(target=t2_func, args=t2_args) if t2_func else None

    t1.start()
    if t2:
        t2.start()

    t1.join()
    if t2:
        t2.join()


# ==========================================
# SCENARIO 1: LOST UPDATE
# ==========================================
def tx_lost_update(nome_tx, isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("SELECT conteggio FROM impiegati WHERE matricola=101;")
        count = (cur.fetchone() or [0])[0]
        log_result("LOST_UPDATE", f"{nome_tx} ha letto {count=}")

        time.sleep(1)

        cur.execute(
            f"UPDATE impiegati SET conteggio = {count} + 1 WHERE matricola=101;"
        )
        log_result("LOST_UPDATE", f"{nome_tx} imposta count a {count + 1}")
        conn.commit()
        log_result("LOST_UPDATE", f"{nome_tx} COMMIT confermato.")
    except errors.SerializationFailure:
        conn.rollback()
        log_result(
            "LOST_UPDATE",
            f"CONCLUSIONE: {nome_tx} ABORTITA per Serialization Failure (Previene Lost Update!)",
        )
    except Exception as e:
        conn.rollback()
        log_result("LOST_UPDATE", f"{nome_tx} Errore imprevisto: {e}")
    finally:
        conn.close()


def test_lost_update():
    lvl_rc = psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED
    run_test_scenario(
        "LOST_UPDATE",
        "INIZIO TEST LOST UPDATE (READ COMMITTED)",
        tx_lost_update,
        ("Tx1", lvl_rc),
        tx_lost_update,
        ("Tx2", lvl_rc),
    )

    lvl_rr = psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ
    run_test_scenario(
        "LOST_UPDATE",
        "INIZIO TEST LOST UPDATE (REPEATABLE READ)",
        tx_lost_update,
        ("Tx1", lvl_rr),
        tx_lost_update,
        ("Tx2", lvl_rr),
    )


# ==========================================
# SCENARIO 2: NON-REPEATABLE READ
# ==========================================
def tx_non_repeatable_read_t1(isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 102")
        count_prima = (cur.fetchone() or [0])[0]
        log_result("NON_REPEATABLE_READ", f"T1 count prima: {count_prima}")

        time.sleep(2)

        cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 102")
        count_dopo = (cur.fetchone() or [0])[0]
        log_result("NON_REPEATABLE_READ", f"T1 count dopo:  {count_dopo}")

        if count_prima == count_dopo:
            log_result(
                "NON_REPEATABLE_READ",
                "Non-Repeatable Read PREVENUTO! (I valori coincidono)",
            )
        else:
            log_result(
                "NON_REPEATABLE_READ",
                "Non-Repeatable Read AVVENUTO! (Il valore è cambiato durante la transazione)",
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        log_result("NON_REPEATABLE_READ", f"T1 Errore: {e}")
    finally:
        conn.close()


def tx_non_repeatable_read_t2():
    conn = get_connection()
    cur = conn.cursor()
    try:
        time.sleep(0.5)
        cur.execute(
            "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = 102;"
        )
        conn.commit()
        log_result(
            "NON_REPEATABLE_READ", "T2: Valore modificato e committato con successo."
        )
    except Exception as e:
        conn.rollback()
        log_result("NON_REPEATABLE_READ", f"T2 Errore: {e}")
    finally:
        conn.close()


def test_non_repeatable_read():
    lvl_rc = psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED
    run_test_scenario(
        "NON_REPEATABLE_READ",
        "INIZIO TEST NON-REPEATABLE READ (READ COMMITTED)",
        tx_non_repeatable_read_t1,
        (lvl_rc,),
        tx_non_repeatable_read_t2,
    )

    lvl_rr = psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ
    run_test_scenario(
        "NON_REPEATABLE_READ",
        "INIZIO TEST NON-REPEATABLE READ (REPEATABLE READ)",
        tx_non_repeatable_read_t1,
        (lvl_rr,),
        tx_non_repeatable_read_t2,
    )


# ==========================================
# SCENARIO 3: PHANTOM READ
# ==========================================
def tx_phantom_read_t1(isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) FROM impiegati WHERE conteggio > 0;")
        count_prima = (cur.fetchone() or [0])[0]
        log_result(
            "PHANTOM_READ", f"T1 (Prima lettura): Trovati {count_prima} impiegati."
        )

        time.sleep(2)

        cur.execute("SELECT count(*) FROM impiegati WHERE conteggio > 0;")
        count_dopo = (cur.fetchone() or [0])[0]
        log_result(
            "PHANTOM_READ", f"T1 (Seconda lettura): Trovati {count_dopo} impiegati."
        )

        if count_prima == count_dopo:
            log_result(
                "PHANTOM_READ",
                "Phantom Read PREVENUTO! (Tipico di Postgres in REPEATABLE READ)",
            )
        else:
            log_result(
                "PHANTOM_READ",
                "Phantom Read AVVENUTO! (L'aggregato è cambiato, normale in READ COMMITTED)",
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
    lvl_rc = psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED
    run_test_scenario(
        "PHANTOM_READ",
        "INIZIO TEST PHANTOM READ (READ COMMITTED)",
        tx_phantom_read_t1,
        (lvl_rc,),
        tx_phantom_read_t2,
    )

    lvl_rr = psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ
    run_test_scenario(
        "PHANTOM_READ",
        "INIZIO TEST PHANTOM READ (REPEATABLE READ)",
        tx_phantom_read_t1,
        (lvl_rr,),
        tx_phantom_read_t2,
    )


# ==========================================
# SCENARIO 4: WRITE SKEW
# ==========================================
def tx_write_skew(nome_tx, matricola, cognome, isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) FROM impiegati;")
        count = (cur.fetchone() or [0])[0]
        log_result("WRITE_SKEW", f"{nome_tx} ha letto count = {count}")

        time.sleep(1)

        cur.execute(
            "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (%s, %s, %s)",
            (matricola, cognome, count),
        )
        conn.commit()
        log_result(
            "WRITE_SKEW", f"CONCLUSIONE: {nome_tx} COMMIT completato con successo."
        )
    except errors.SerializationFailure:
        conn.rollback()
        log_result(
            "WRITE_SKEW",
            f"{nome_tx} ABORTITA per Serialization Failure (Previene Write Skew!)",
        )
    except Exception as e:
        conn.rollback()
        log_result("WRITE_SKEW", f"{nome_tx} Errore imprevisto: {e}")
    finally:
        conn.close()


def test_write_skew():
    lvl_ser = psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
    run_test_scenario(
        "WRITE_SKEW",
        "INIZIO TEST WRITE SKEW (Livello: SERIALIZABLE)",
        tx_write_skew,
        ("Tx1", 103, "Verdi", lvl_ser),
        tx_write_skew,
        ("Tx2", 104, "Neri", lvl_ser),
    )


# ==========================================
# SCENARIO 5: DEADLOCK
# ==========================================
def tx_deadlock(nome_tx, mat_1, mat_2):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = {mat_1};"
        )
        log_result("DEADLOCK", f"{nome_tx} ha bloccato matricola {mat_1}.")
        time.sleep(1)

        log_result("DEADLOCK", f"{nome_tx} prova a bloccare matricola {mat_2}...")
        cur.execute(
            f"UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = {mat_2};"
        )
        conn.commit()
        log_result("DEADLOCK", f"{nome_tx} ha completato entrambi gli update.")
    except errors.DeadlockDetected:
        conn.rollback()
        log_result(
            "DEADLOCK",
            f"{nome_tx} ABORTITA dal DBMS per Deadlock (Errore 40P01)!",
        )
    except Exception as e:
        conn.rollback()
        log_result("DEADLOCK", f"{nome_tx} Errore imprevisto: {e}")
    finally:
        conn.close()


def test_deadlock():
    run_test_scenario(
        "DEADLOCK",
        "INIZIO TEST DEADLOCK",
        tx_deadlock,
        ("Tx1", 101, 102),
        tx_deadlock,
        ("Tx2", 102, 101),
    )


# ==========================================
# SCENARIO 6: DIRTY READ
# ==========================================
def tx_dirty_read_t1(isolation_level):
    conn = get_connection()
    conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        cur.execute("UPDATE impiegati SET conteggio = 999 WHERE matricola = 101;")
        log_result(
            "DIRTY_READ", "T1 ha modificato il conteggio a 999 ma NON HA FATTO COMMIT."
        )

        time.sleep(2)

        conn.rollback()
        log_result(
            "DIRTY_READ",
            "T1 ha fatto ROLLBACK. La modifica a 999 è annullata in modo sicuro.",
        )
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
        time.sleep(0.5)

        cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 101;")
        count = (cur.fetchone() or [0])[0]
        log_result("DIRTY_READ", f"T2 ha letto il conteggio: {count}")

        if count == 999:
            log_result(
                "DIRTY_READ",
                "DIRTY READ AVVENUTO! (Non supportato da Postgres, ma logicamente fallato)",
            )
        else:
            log_result(
                "DIRTY_READ",
                "DIRTY READ PREVENUTO! (Postgres ignora READ UNCOMMITTED e forza READ COMMITTED)",
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        log_result("DIRTY_READ", f"T2 Errore: {e}")
    finally:
        conn.close()


def test_dirty_read():
    lvl_ru = psycopg2.extensions.ISOLATION_LEVEL_READ_UNCOMMITTED
    run_test_scenario(
        "DIRTY_READ",
        "INIZIO TEST DIRTY READ (FORZANDO READ_UNCOMMITTED)",
        tx_dirty_read_t1,
        (lvl_ru,),
        tx_dirty_read_t2,
        (lvl_ru,),
    )


if __name__ == "__main__":
    if os.path.exists("test_results.log"):
        os.remove("test_results.log")

    # time.sleep(1)

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
