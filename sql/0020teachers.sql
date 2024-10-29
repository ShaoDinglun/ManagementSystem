CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    gender ENUM('男', '女') NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    password VARCHAR(255) NOT NULL,
    reserved1 VARCHAR(255) DEFAULT NULL,
    reserved2 VARCHAR(255) DEFAULT NULL
);