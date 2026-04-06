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
