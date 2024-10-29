CREATE TABLE examquestions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT,
    question_id INT,
    score INT NOT NULL,
    reserved1 VARCHAR(255) DEFAULT NULL,
    reserved2 VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);