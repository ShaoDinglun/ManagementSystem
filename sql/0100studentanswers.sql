CREATE TABLE studentanswers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    exam_id INT,
    question_id INT,
    selected_option_id INT,
    answer_text TEXT,
    reserved1 VARCHAR(255) DEFAULT NULL,
    reserved2 VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES questionoptions(id) ON DELETE CASCADE
);