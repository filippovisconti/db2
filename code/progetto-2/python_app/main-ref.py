from typing import Callable, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import errors
from psycopg2.extensions import (
    ISOLATION_LEVEL_READ_COMMITTED,
    ISOLATION_LEVEL_READ_UNCOMMITTED,
    ISOLATION_LEVEL_REPEATABLE_READ,
    ISOLATION_LEVEL_SERIALIZABLE,
)
import threading
import time
import os

DB_HOST: str = os.environ.get("DB_HOST", "localhost")
DB_USER: str = os.environ.get("DB_USER", "admin")
DB_PASS: str = os.environ.get("DB_PASS", "password")
DB_NAME: str = os.environ.get("DB_NAME", "atzeni_db")


@contextmanager
def db_transaction(isolation_level: Optional[int] = None):
    conn = psycopg2.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )
    if isolation_level is not None:
        conn.set_isolation_level(isolation_level)
    cur = conn.cursor()
    try:
        yield conn, cur
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def fetch_single_value(cur, default: int = 0) -> int:
    row = cur.fetchone()
    return row[0] if row is not None else default


def reset_database() -> None:
    with db_transaction() as (conn, cur):
        cur.execute("DELETE FROM impiegati;")
        cur.execute(
            "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (101, 'Rossi', 1), (102, 'Bruni', 2);"
        )
        conn.commit()


def log_result(scenario_name: str, message: str) -> None:
    log_line = f"[{scenario_name}] {message}"
    print(log_line)
    with open("test_results.log", "a") as f:
        f.write(log_line + "\n")


def run_test_scenario(
    scenario_name: str,
    title: str,
    t1_func: Callable,
    t1_args: tuple = (),
    t2_func: Optional[Callable] = None,
    t2_args: tuple = (),
) -> None:
    reset_database()
    log_result(scenario_name, f"--- {title} ---")

    t1: threading.Thread = threading.Thread(target=t1_func, args=t1_args)
    t2: Optional[threading.Thread] = (
        threading.Thread(target=t2_func, args=t2_args) if t2_func else None
    )

    t1.start()
    if t2:
        t2.start()

    t1.join()
    if t2:
        t2.join()


# SCENARIO 1: LOST UPDATE
def tx_lost_update(nome_tx: str, isolation_level: int) -> None:
    try:
        with db_transaction(isolation_level) as (conn, cur):
            cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 101;")
            count: int = fetch_single_value(cur)
            log_result("LOST_UPDATE", f"{nome_tx} ha letto {count=}")

            time.sleep(1)

            cur.execute(
                "UPDATE impiegati SET conteggio = %s + 1 WHERE matricola = 101;",
                (count,),
            )

            log_result("LOST_UPDATE", f"{nome_tx} imposta count a {count + 1}")
            conn.commit()
            log_result("LOST_UPDATE", f"{nome_tx} COMMIT confermato.")

    except errors.SerializationFailure:
        log_result(
            "LOST_UPDATE",
            f"CONCLUSIONE: {nome_tx} ABORTITA. Serialization Failure. Previene Lost Update",
        )
    except Exception as e:
        log_result("LOST_UPDATE", f"{nome_tx} Errore imprevisto: {e}")


def test_lost_update() -> None:
    run_test_scenario(
        "LOST_UPDATE",
        "INIZIO TEST LOST UPDATE (READ COMMITTED)",
        tx_lost_update,
        ("Tx1", ISOLATION_LEVEL_READ_COMMITTED),
        tx_lost_update,
        ("Tx2", ISOLATION_LEVEL_READ_COMMITTED),
    )
    run_test_scenario(
        "LOST_UPDATE",
        "INIZIO TEST LOST UPDATE (REPEATABLE READ)",
        tx_lost_update,
        ("Tx1", ISOLATION_LEVEL_REPEATABLE_READ),
        tx_lost_update,
        ("Tx2", ISOLATION_LEVEL_REPEATABLE_READ),
    )


# SCENARIO 2: NON-REPEATABLE READ
def tx_non_repeatable_read_t1(isolation_level: int) -> None:
    try:
        with db_transaction(isolation_level) as (conn, cur):
            cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 102;")
            count_prima: int = fetch_single_value(cur)
            log_result("NON_REPEATABLE_READ", f"T1 count prima: {count_prima}")

            time.sleep(2)

            cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 102;")
            count_dopo: int = fetch_single_value(cur)
            log_result("NON_REPEATABLE_READ", f"T1 count dopo:  {count_dopo}")

            if count_prima == count_dopo:
                log_result(
                    "NON_REPEATABLE_READ",
                    "Non-Repeatable Read PREVENUTO! (I valori coincidono)",
                )
            else:
                log_result(
                    "NON_REPEATABLE_READ",
                    "Non-Repeatable Read AVVENUTO! (Il valore è cambiato)",
                )
            conn.commit()
    except Exception as e:
        log_result("NON_REPEATABLE_READ", f"T1 Errore: {e}")


def tx_non_repeatable_read_t2() -> None:
    try:
        with db_transaction() as (conn, cur):
            time.sleep(0.5)
            cur.execute(
                "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = 102;"
            )
            log_result(
                "NON_REPEATABLE_READ",
                "T2: Valore modificato.",
            )
            conn.commit()
            log_result(
                "NON_REPEATABLE_READ",
                "T2: Valore committato con successo.",
            )
    except Exception as e:
        log_result("NON_REPEATABLE_READ", f"T2 Errore: {e}")


def test_non_repeatable_read() -> None:
    run_test_scenario(
        "NON_REPEATABLE_READ",
        "INIZIO TEST NON-REPEATABLE READ (READ COMMITTED)",
        tx_non_repeatable_read_t1,
        (ISOLATION_LEVEL_READ_COMMITTED,),
        tx_non_repeatable_read_t2,
    )
    run_test_scenario(
        "NON_REPEATABLE_READ",
        "INIZIO TEST NON-REPEATABLE READ (REPEATABLE READ)",
        tx_non_repeatable_read_t1,
        (ISOLATION_LEVEL_REPEATABLE_READ,),
        tx_non_repeatable_read_t2,
    )


# SCENARIO 3: PHANTOM READ
def tx_phantom_read_t1(isolation_level: int) -> None:
    try:
        with db_transaction(isolation_level) as (conn, cur):
            cur.execute("SELECT count(*) FROM impiegati WHERE conteggio > 0;")
            count_prima = fetch_single_value(cur)
            log_result(
                "PHANTOM_READ", f"T1 (Prima lettura): Trovati {count_prima} impiegati."
            )

            time.sleep(2)

            cur.execute("SELECT count(*) FROM impiegati WHERE conteggio > 0;")
            count_dopo = fetch_single_value(cur)
            log_result(
                "PHANTOM_READ", f"T1 (Seconda lettura): Trovati {count_dopo} impiegati."
            )

            if count_prima == count_dopo:
                log_result(
                    "PHANTOM_READ",
                    "Phantom Read PREVENUTO!",
                )
            else:
                log_result("PHANTOM_READ", "Phantom Read AVVENUTO!")
            conn.commit()
    except Exception as e:
        log_result("PHANTOM_READ", f"T1 Errore: {e}")


def tx_phantom_read_t2() -> None:
    try:
        with db_transaction() as (conn, cur):
            time.sleep(0.5)
            cur.execute(
                "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (%s, %s, %s);",
                (105, "Bianchi", 3),
            )
            conn.commit()
            log_result(
                "PHANTOM_READ", "T2: Nuovo impiegato 'Bianchi' inserito con successo."
            )
    except Exception as e:
        log_result("PHANTOM_READ", f"T2 Errore: {e}")


def test_phantom_read() -> None:
    run_test_scenario(
        "PHANTOM_READ",
        "INIZIO TEST PHANTOM READ (READ COMMITTED)",
        tx_phantom_read_t1,
        (ISOLATION_LEVEL_READ_COMMITTED,),
        tx_phantom_read_t2,
    )
    run_test_scenario(
        "PHANTOM_READ",
        "INIZIO TEST PHANTOM READ (REPEATABLE READ)",
        tx_phantom_read_t1,
        (ISOLATION_LEVEL_REPEATABLE_READ,),
        tx_phantom_read_t2,
    )


# SCENARIO 4: WRITE SKEW
def tx_write_skew(
    nome_tx: str, matricola: int, cognome: str, isolation_level: int
) -> None:
    try:
        with db_transaction(isolation_level) as (conn, cur):
            cur.execute("SELECT count(*) FROM impiegati;")
            count: int = fetch_single_value(cur)
            log_result("WRITE_SKEW", f"{nome_tx} ha letto count = {count}")

            time.sleep(1)

            cur.execute(
                "INSERT INTO impiegati (matricola, cognome, conteggio) VALUES (%s, %s, %s)",
                (matricola, cognome, count),
            )
            cur.execute("SELECT count(*) FROM impiegati;")
            count: int = fetch_single_value(cur)
            log_result("WRITE_SKEW", f"{nome_tx} ha letto updated count = {count}")
            conn.commit()
            cur.execute("SELECT count(*) FROM impiegati;")
            count: int = fetch_single_value(cur)
            log_result("WRITE_SKEW", f"{nome_tx} ha letto post commit count = {count}")
            log_result(
                "WRITE_SKEW", f"CONCLUSIONE: {nome_tx} COMMIT completato con successo."
            )

    except errors.SerializationFailure:
        log_result(
            "WRITE_SKEW",
            f"{nome_tx} ABORTITA per Serialization Failure",
        )
    except Exception as e:
        log_result("WRITE_SKEW", f"{nome_tx} Errore imprevisto: {e}")


def test_write_skew() -> None:
    run_test_scenario(
        "WRITE_SKEW",
        "INIZIO TEST WRITE SKEW (Livello: REPEATABLE_READ)",
        tx_write_skew,
        ("Tx1", 103, "Verdi", ISOLATION_LEVEL_REPEATABLE_READ),
        tx_write_skew,
        ("Tx2", 104, "Neri", ISOLATION_LEVEL_REPEATABLE_READ),
    )
    run_test_scenario(
        "WRITE_SKEW",
        "INIZIO TEST WRITE SKEW (Livello: SERIALIZABLE)",
        tx_write_skew,
        ("Tx1", 103, "Verdi", ISOLATION_LEVEL_SERIALIZABLE),
        tx_write_skew,
        ("Tx2", 104, "Neri", ISOLATION_LEVEL_SERIALIZABLE),
    )


# SCENARIO 5: DEADLOCK
def tx_deadlock(nome_tx: str, mat_1: int, mat_2: int) -> None:
    try:
        with db_transaction() as (conn, cur):
            cur.execute(
                "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = %s;",
                (mat_1,),
            )
            log_result("DEADLOCK", f"{nome_tx} ha bloccato matricola {mat_1}.")

            time.sleep(1)

            log_result("DEADLOCK", f"{nome_tx} prova a bloccare matricola {mat_2}...")
            cur.execute(
                "UPDATE impiegati SET conteggio = conteggio + 1 WHERE matricola = %s;",
                (mat_2,),
            )
            conn.commit()
            log_result("DEADLOCK", f"{nome_tx} ha completato entrambi gli update.")

    except errors.DeadlockDetected:
        log_result("DEADLOCK", f"{nome_tx} ABORTITA per Deadlock!")
    except Exception as e:
        log_result("DEADLOCK", f"{nome_tx} Errore imprevisto: {e}")


def test_deadlock() -> None:
    run_test_scenario(
        "DEADLOCK",
        "INIZIO TEST DEADLOCK",
        tx_deadlock,
        ("Tx1", 101, 102),
        tx_deadlock,
        ("Tx2", 102, 101),
    )


# SCENARIO 6: DIRTY READ
def tx_dirty_read_t1(isolation_level: int) -> None:
    try:
        with db_transaction(isolation_level) as (conn, cur):
            cur.execute("UPDATE impiegati SET conteggio = 999 WHERE matricola = 101;")
            log_result(
                "DIRTY_READ",
                "T1 ha modificato il conteggio a 999 ma NON HA FATTO COMMIT.",
            )

            time.sleep(2)

            conn.rollback()
            log_result(
                "DIRTY_READ",
                "T1 ha fatto ROLLBACK.",
            )
    except Exception as e:
        log_result("DIRTY_READ", f"T1 Errore: {e}")


def tx_dirty_read_t2(isolation_level: int) -> None:
    try:
        with db_transaction(isolation_level) as (conn, cur):
            time.sleep(0.5)

            cur.execute("SELECT conteggio FROM impiegati WHERE matricola = 101;")
            count = fetch_single_value(cur)
            log_result("DIRTY_READ", f"T2 ha letto il conteggio: {count}")

            if count == 999:
                log_result(
                    "DIRTY_READ", "DIRTY READ AVVENUTO! (Non possibile su Postgres)"
                )
            else:
                log_result(
                    "DIRTY_READ",
                    "DIRTY READ PREVENUTO! (Postgres infatti forza READ COMMITTED)",
                )
            conn.commit()
    except Exception as e:
        log_result("DIRTY_READ", f"T2 Errore: {e}")


def test_dirty_read() -> None:
    run_test_scenario(
        "DIRTY_READ",
        "INIZIO TEST DIRTY READ (FORZANDO READ_UNCOMMITTED)",
        tx_dirty_read_t1,
        (ISOLATION_LEVEL_READ_UNCOMMITTED,),
        tx_dirty_read_t2,
        (ISOLATION_LEVEL_READ_UNCOMMITTED,),
    )


if __name__ == "__main__":
    if os.path.exists("test_results.log"):
        os.remove("test_results.log")

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
