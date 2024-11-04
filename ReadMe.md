# 基于Python的考试管理系统

## 项目概述
本项目旨在设计并实现一个基于Python Flask框架的智能化考试管理系统，支持学生、教师和管理员角色操作，以简化和提升考试管理的效率与智能化水平。系统采用B/S架构，通过前端HTML和CSS实现页面交互，后端利用Flask提供API接口，并使用MySQL数据库管理数据。创新点在于集成了大语言模型来自动解析和导入题库，以提高教师的题库管理效率。

## 功能模块

### 学生模块
- **注册**：填写学号、姓名、班级、性别、手机号、密码等信息进行注册。
- **登录与注销**：支持账号登录、注销，保证系统访问的安全性。
- **参加考试**：查看考试列表并选择进入考试，提交考试答案。
  
### 教师模块
- **注册**：填写教师号、姓名、性别、手机号、密码等信息进行注册。
- **登录与注销**：教师账号的登录、注销操作。
- **题库管理**：支持创建题库，导入题目（支持Word或Excel文件上传，并通过大语言模型自动识别题目类型、题目、选项和答案），添加、修改和删除题目。
- **考试管理**：创建考试，选择题库、题目类型及分数，支持自动批改客观题及手动阅卷、成绩查询等。
  
### 管理员模块
- **账户管理**：支持教师和学生账户的管理，包括查询、添加、修改和删除。
- **系统日志**：基于 `logging` 库记录操作日志。

## 技术栈

- **后端**：Python Flask
- **数据库**：MySQL
- **前端**：HTML、CSS
- **移动端**：微信小程序（支持学生端考试功能）
- **大语言模型**：用于题库题型、题目、选项和答案的自动解析与导入

## 系统架构

系统采用前后端分离的B/S架构，主要包括以下模块：
- **学生模块**：用户注册、登录、考试参与与答案提交。
- **教师模块**：题库管理（导入/添加/修改/删除）、考试管理及阅卷功能。
- **管理员模块**：账户管理、系统日志管理。

## 系统设计

### 数据库设计
系统数据库由多个表组成，包括但不限于：
- **学生表**：记录学生的基本信息。
- **教师表**：记录教师的基本信息。
- **题库表**：存储题库的题目信息。
- **考试表**：记录考试基本信息、考试时间、题目类型和分数等。
- **成绩表**：用于记录学生成绩信息。

### 前端设计
前端设计基于响应式布局，提供简洁的用户界面，包括登录页面、考试页面和成绩查询页面等，确保用户体验流畅。

## 系统特点

- **模块化设计**：分为学生、教师和管理员模块，便于系统的扩展和维护。
- **智能化题库管理**：教师可以通过上传Word或Excel文件批量导入题目，大语言模型将自动解析题目内容，极大提高效率。
- **微信小程序支持**：为学生端提供移动考试端，增加系统的灵活性。
- **数据安全与日志管理**：管理员可以通过日志记录监控系统的运行情况，提升系统安全性。

## 安装与运行

### 环境依赖
- Python >= 3.7
- Flask
- MySQL
- HTML、CSS
- 微信小程序开发工具

### 本地运行步骤

1. 克隆项目仓库：
   https://github.com/ShaoDinglun/ManagementSystem.git
2. 安装python3.12
3. 安装pipenv
4. 安装并进入pipenv虚拟环境
   pipenv install
   pipenv shell
6. 安装依赖项
   pip install -r ./requirements.txt


