CREATE INDEX idx_exams_student_id ON exams(student_id);
CREATE INDEX idx_exams_course_id ON exams(course_id);

CREATE INDEX idx_exams_date ON exams(exam_date DESC);
CREATE INDEX idx_courses_department ON courses(department);
