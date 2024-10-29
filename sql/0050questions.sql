CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_bank_id INT,
    question_type ENUM('单选题', '多选题', '填空题', '主观题','判断题') NOT NULL,
    content TEXT NOT NULL,
    answer TEXT,
    reserved1 VARCHAR(255) DEFAULT NULL,
    reserved2 VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (question_bank_id) REFERENCES questionbanks(id) ON DELETE CASCADE
);