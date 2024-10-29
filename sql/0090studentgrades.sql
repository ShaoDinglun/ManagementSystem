CREATE TABLE studentgrades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    exam_id INT,
    grade INT,
    reserved1 VARCHAR(255) DEFAULT NULL,
    reserved2 VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);