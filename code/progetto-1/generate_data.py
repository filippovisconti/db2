import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
import random
from datetime import date, timedelta
import time

# Configurazione
DB_PARAMS = {
    "dbname": "university",
    "user": "db_admin",
    "password": "****",
    "host": "localhost",
    "port": "5432",
}

NUM_COURSES = 100
NUM_STUDENTS = 50000
NUM_EXAMS = 15000000

CLEAR_TABLES_ON_START = True

fake = Faker("it_IT")


def clear_tables(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE exams, students, courses RESTART IDENTITY CASCADE;")
    conn.commit()
    print("Tabelle svuotate e contatori resettati con successo.\n")


def generate_courses(conn):
    print(f"Generazione di {NUM_COURSES} corsi...")
    courses = []
    departments = ["Informatica", "Matematica", "Fisica", "Ingegneria", "Economia"]
    for _ in range(NUM_COURSES):
        courses.append(
            (
                fake.unique.bothify(text="???-####").upper(),
                fake.catch_phrase()[:100],
                random.choice([6, 9, 12]),
                random.choice(departments),
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO courses (course_code, course_name, credits, department) VALUES %s",
            courses,
        )
    conn.commit()


def generate_students(conn):
    print(f"Generazione di {NUM_STUDENTS} studenti...")
    students = []
    for _ in range(NUM_STUDENTS):
        students.append(
            (
                fake.unique.bothify(text="MATR#######"),
                fake.first_name(),
                fake.last_name(),
                random.randint(2015, 2024),
            )
        )

    batch_size = 10000
    with conn.cursor() as cur:
        for i in range(0, len(students), batch_size):
            execute_values(
                cur,
                "INSERT INTO students (matricola, first_name, last_name, enrollment_year) VALUES %s",
                students[i : i + batch_size],
            )
    conn.commit()


def generate_exams(conn):
    print(f"Generazione di {NUM_EXAMS} esami ...")
    exams = []
    start_date = date(2015, 1, 1)

    for _ in range(NUM_EXAMS):
        random_days = random.randint(0, 3200)
        exam_date = start_date + timedelta(days=random_days)

        exams.append(
            (
                random.randint(1, NUM_STUDENTS),
                random.randint(1, NUM_COURSES),
                exam_date,
                random.randint(18, 31),
            )
        )

    batch_size = 20000
    with conn.cursor() as cur:
        for i in range(0, len(exams), batch_size):
            execute_values(
                cur,
                "INSERT INTO exams (student_id, course_id, exam_date, grade) VALUES %s",
                exams[i : i + batch_size],
            )
            if (i % 200000 == 0) and i > 0:
                print(f"... inseriti {i} esami")
    conn.commit()


def main():
    start_time = time.time()
    try:
        conn = psycopg2.connect(
            dbname=DB_PARAMS["dbname"],
            user=DB_PARAMS["user"],
            password=DB_PARAMS["password"],
            host=DB_PARAMS["host"],
            port=DB_PARAMS["port"],
        )

        if CLEAR_TABLES_ON_START:
            clear_tables(conn)

        generate_courses(conn)
        generate_students(conn)
        generate_exams(conn)

        conn.close()
        end_time = time.time()
        print(f"\nCompletato! DB inizializzato in {end_time - start_time} secondi.")

    except Exception as e:
        print(f"Errore: {e}")


if __name__ == "__main__":
    main()
