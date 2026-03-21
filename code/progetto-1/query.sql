CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(10) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    credits SMALLINT NOT NULL CHECK (credits > 0 AND credits <= 18),
    department VARCHAR(50) NOT NULL
);

CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    matricola VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    enrollment_year SMALLINT NOT NULL
);

CREATE TABLE exams (
    exam_id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    exam_date DATE NOT NULL,
    grade SMALLINT NOT NULL CHECK (grade >= 18 AND grade <= 31),

    CONSTRAINT fk_student FOREIGN KEY (student_id) REFERENCES students (student_id),
    CONSTRAINT fk_course FOREIGN KEY (course_id) REFERENCES courses (course_id)
);


-- Campiona i dati e aggiorna la tabella di sistema pg_statistic, calcolando la distribuzione dei valori e permettendo al Query Planner di fare stime accurate sui costi.
ANALYZE exams, students, courses;

-- query 1
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.course_name, e.exam_date, e.grade
FROM exams e
JOIN courses c ON e.course_id = c.course_id
WHERE c.department = 'Informatica' AND e.grade = 31;

-- query 2
EXPLAIN (ANALYZE, BUFFERS)
SELECT s.matricola, c.course_name, e.grade, e.exam_date
FROM exams e
JOIN students s ON e.student_id = s.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE e.grade >= 28 AND e.exam_date >= '2023-01-01' AND e.exam_date <= '2023-12-31'
ORDER BY e.exam_date DESC;

-- query 3
EXPLAIN (ANALYZE, BUFFERS)
SELECT s.matricola, s.first_name, s.last_name,
       SUM(c.credits) AS total_credits,
       ROUND(AVG(e.grade), 2) AS average_grade
FROM exams e
JOIN students s ON e.student_id = s.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE s.matricola = 'MATR0000000' AND e.grade >= 18  -- Inserisci una matricola vera qui
GROUP BY s.student_id, s.matricola, s.first_name, s.last_name;

-- CREATE INDEXES

-- 1. Indici sulle Foreign Key (Essenziali per le JOIN)
CREATE INDEX idx_exams_student_id ON exams(student_id);
CREATE INDEX idx_exams_course_id ON exams(course_id);

-- 2. Indice Composto per filtrare velocemente corso e voto (Per Q1)
CREATE INDEX idx_exams_course_grade ON exams(course_id, grade);

-- 3. Indice sulle date per supportare le ricerche per range e gli ordinamenti (Per Q2)
CREATE INDEX idx_exams_date ON exams(exam_date DESC);

-- 4. Indice sulle dimensioni (Per Q1)
CREATE INDEX idx_courses_department ON courses(department);
