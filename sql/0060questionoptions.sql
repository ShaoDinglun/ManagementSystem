CREATE TABLE questionoptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    reserved1 VARCHAR(255) DEFAULT NULL,
    reserved2 VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);