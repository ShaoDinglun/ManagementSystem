# models.py
from peewee import (
    Model, CharField, IntegerField, ForeignKeyField, TextField, 
    DateTimeField, TimestampField, BooleanField, MySQLDatabase
)
from datetime import datetime

db = MySQLDatabase(
    'bs',
    user='root',
    password='111111',
    host='127.0.0.1',
    port=3306
)

class BaseModel(Model):
    reserved1 = CharField(max_length=255, null=True)
    reserved2 = CharField(max_length=255, null=True)
    class Meta:
        database = db

class Students(BaseModel):
    student_id = CharField(unique=True, max_length=20)
    name = CharField(max_length=50)
    student_class = CharField(max_length=50)
    gender = CharField(choices=['男', '女'], max_length=10)  # 使用 CharField 模拟枚举
    phone_number = CharField(max_length=15)
    password = CharField(max_length=255)

class Teachers(BaseModel):
    teacher_id = CharField(unique=True, max_length=20)
    name = CharField(max_length=50)
    gender = CharField(choices=['男', '女'], max_length=10)  # 使用 CharField 模拟枚举
    phone_number = CharField(max_length=15)
    password = CharField(max_length=255)

class Admins(BaseModel):
    admin_id = CharField(unique=True, max_length=20)
    name = CharField(max_length=50)
    phone_number = CharField(max_length=15)
    password = CharField(max_length=255)

class QuestionBanks(BaseModel):
    name = CharField(max_length=100)
    created_at = TimestampField(default=datetime.now)

class Questions(BaseModel):
    question_bank = ForeignKeyField(QuestionBanks, backref='questions', on_delete='CASCADE')
    question_type = CharField(choices=['单选题', '多选题', '填空题', '主观题','判断题'], max_length=20)  # 使用 CharField 模拟枚举
    content = TextField()
    answer = TextField(null=True)

class QuestionOptions(BaseModel):
    question = ForeignKeyField(Questions, backref='options', on_delete='CASCADE')
    option_text = TextField()
    is_correct = BooleanField(default=False)

class Exams(BaseModel):
    name = CharField(max_length=100)
    start_time = DateTimeField()
    end_time = DateTimeField()
    question_bank = ForeignKeyField(QuestionBanks, backref='exams', on_delete='CASCADE')
    created_at = TimestampField(default=datetime.now)

class ExamQuestions(BaseModel):
    exam = ForeignKeyField(Exams, backref='exam_questions', on_delete='CASCADE')
    question = ForeignKeyField(Questions, backref='exam_questions', on_delete='CASCADE')
    score = IntegerField()

class StudentGrades(BaseModel):
    student = ForeignKeyField(Students, backref='grades', on_delete='CASCADE')
    exam = ForeignKeyField(Exams, backref='grades', on_delete='CASCADE')
    grade = IntegerField(null=True)
    
class StudentAnswers(BaseModel):
    student = ForeignKeyField(Students, backref='answers', on_delete='CASCADE')
    exam = ForeignKeyField(Exams, backref='answers', on_delete='CASCADE')
    question = ForeignKeyField(Questions, backref='answers', on_delete='CASCADE')
    selected_option = ForeignKeyField(QuestionOptions, null=True, backref='answers', on_delete='CASCADE')
    answer_text = TextField(null=True)

