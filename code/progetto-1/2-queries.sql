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
WHERE s.matricola = 'MATR1332760' AND e.grade >= 18
GROUP BY s.student_id, s.matricola, s.first_name, s.last_name;
