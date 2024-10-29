CREATE TABLE exams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    question_bank_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reserved1 VARCHAR(255) DEFAULT NULL,
    reserved2 VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (question_bank_id) REFERENCES questionbanks(id) ON DELETE CASCADE
);