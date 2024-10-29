*现有情况*
使用python的flask框架开发后端
数据库使用mysql
前端页面使用html和css开发
小程序端预计使用微信小程序开发

*说明文档*
# methods.py
from datetime import datetime
from io import BytesIO
import logging
import os
from models import Admins, ExamQuestions, QuestionBanks, QuestionOptions, Questions, StudentGrades, Students, StudentAnswers, Exams, Teachers
from peewee import DoesNotExist
from check_questions.check_docx_questions import DocxQuestionImporter
from check_questions.check_excel_questions import ExcelQuestionImporter

# 初始化日志记录
# 配置日志文件
local_date = datetime.strftime(datetime.now(),"%Y%m%d")
logging.basicConfig(filename=os.path.join("./logs",f'{local_date}.log'), level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 学生模块
class StudentModule:
    def register(self, student_id, name, student_class, gender, phone_number, password, confirm_password):
        if password != confirm_password:
            logger.warning(f"Password confirmation failed for student {student_id}")
            return {"status": "error", "message": "Passwords do not match"}
        try:
            Students.create(
                student_id=student_id,
                name=name,
                student_class=student_class,
                gender=gender,
                phone_number=phone_number,
                password=password
            )
            logger.info(f"Student {student_id} registered successfully")
            return {"status": "success", "message": "Student registered"}
        except Exception as e:
            logger.error(f"Error registering student {student_id}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def login(self, student_id, password):
        try:
            student = Students.get(Students.student_id == student_id, Students.password == password)
            logger.info(f"Student {student_id} logged in successfully")
            return {"status": "success", "message": "Login successful"}
        except DoesNotExist:
            logger.warning(f"Login failed for student {student_id}")
            return {"status": "error", "message": "Invalid credentials"}

    def logout(self):
        logger.info("Student logged out")
        return {"status": "success", "message": "Logout successful"}

    def list_exams(self):
        """
        列出所有当前正在进行的考试
        """
        try:
            current_time = datetime.now()
            exams = Exams.select().where(
                (Exams.start_time <= current_time) &
                (Exams.end_time >= current_time)
            )
            exam_list = [{"id": exam.id, "name": exam.name, "start_time": exam.start_time, "end_time": exam.end_time} for exam in exams]
            return {"status": "success", "exams": exam_list}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def submit_exam_answers(self, student_id, exam_id, answers):
        """
        处理学生提交的答案
        """
        try:
            student = Students.get(Students.id == student_id)
            exam = Exams.get(Exams.id == exam_id)

            # 遍历答案并保存到数据库
            for question_id, answer_data in answers.items():
                question = Questions.get(Questions.id == question_id)
                selected_option_id = answer_data.get('selected_option_id')
                answer_text = answer_data.get('answer_text')

                # 查找或创建学生答案记录
                student_answer, created = StudentAnswers.get_or_create(
                    student=student,
                    exam=exam,
                    question=question,
                    defaults={"selected_option": selected_option_id, "answer_text": answer_text}
                )

                if not created:
                    # 如果记录已存在，更新答案
                    student_answer.selected_option = selected_option_id
                    student_answer.answer_text = answer_text
                    student_answer.save()

            return {"status": "success", "message": "Answers submitted successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# 教师模块
class TeacherModule:

    def register(self, teacher_id, name, gender, phone_number, password, confirm_password):
        # 检查密码和确认密码是否匹配
        if password != confirm_password:
            logger.warning(f"Password confirmation failed for teacher {teacher_id}")
            return {"status": "error", "message": "Passwords do not match"}

        try:
            # 创建教师账户
            Teachers.create(
                teacher_id=teacher_id,
                name=name,
                gender=gender,
                phone_number=phone_number,
                password=password
            )
            logger.info(f"Teacher {teacher_id} registered successfully")
            return {"status": "success", "message": "Teacher registered"}
        except Exception as e:
            logger.error(f"Error registering teacher {teacher_id}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def login(self, teacher_id, password):
        try:
            # 验证教师ID和密码
            teacher = Teachers.get(Teachers.teacher_id == teacher_id, Teachers.password == password)
            logger.info(f"Teacher {teacher_id} logged in successfully")
            return {"status": "success", "message": "Login successful"}
        except DoesNotExist:
            logger.warning(f"Login failed for teacher {teacher_id}")
            return {"status": "error", "message": "Invalid credentials"}

    def logout(self):
        # 处理教师注销
        logger.info("Teacher logged out")
        return {"status": "success", "message": "Logout successful"}

    def manage_question_bank(self, action, question_bank_id=None, question_bank_name=None):
        if action == 'add':
            # 添加题库
            QuestionBanks.create(name=question_bank_name)
            return {"status": "success", "message": "Question bank added successfully"}
        
        elif action == 'edit':
            # 修改题库
            question_bank = QuestionBanks.get(QuestionBanks.id == question_bank_id)
            if question_bank_name:
                question_bank.name = question_bank_name
                question_bank.save()
            return {"status": "success", "message": "Question bank edited successfully"}
        
        elif action == 'delete':
            # 删除题库
            question_bank = QuestionBanks.get(QuestionBanks.id == question_bank_id)
            question_bank.delete_instance()
            return {"status": "success", "message": "Question bank deleted successfully"}

        else:
            return {"status": "error", "message": "Invalid action"}
    
    def get_question_by_id(self, question_id):
        try:
            question = Questions.get_by_id(question_id)
            return question
        except Questions.DoesNotExist:
            return None

    def update_question(self, question_id, question_type, content, answer):
        question = self.get_question_by_id(question_id)
        if question:
            question.question_type = question_type
            question.content = content
            question.answer = answer
            question.save()
            return question
        else:
            return None

    def update_options(self, question_id, options_data):
        # 首先删除原有的选项
        QuestionOptions.delete().where(QuestionOptions.question == question_id).execute()

        # 添加新的选项
        for option_text, is_correct in options_data:
            option = QuestionOptions.create(
                question=question_id,
                option_text=option_text,
                is_correct=is_correct
            )
        return True
    
    def import_question_bank(self, file_path, question_bank_id):
        try:
            excel_importer = ExcelQuestionImporter()
            docx_importer = DocxQuestionImporter()
            # 根据文件类型选择解析器
            if file_path.endswith('.xlsx'):
                parsed_data = excel_importer.recognize_tabular_questions(file_path)
            elif file_path.endswith('.csv'):
                parsed_data = excel_importer.recognize_tabular_questions(file_path)
            elif file_path.endswith('.docx'):
                parsed_data = docx_importer.import_question_bank(file_path)
            else:
                logger.error("Unsupported file type")
                return {"status": "error", "message": "仅支持 Excel (.xlsx, .csv) 和 Word (.docx) 文件"}

            # 获取对应的题库
            question_bank = QuestionBanks.get_or_none(QuestionBanks.id == question_bank_id)
            if not question_bank:
                logger.error(f"Question bank {question_bank_id} not found")
                return {"status": "error", "message": "Question bank not found"}
            
            # 导入解析的数据到数据库
            for question_data in parsed_data:
                # 处理题目类型转换
                question_type = self.map_question_type(question_data['question_type'])

                # 创建新的题目
                question = Questions.create(
                    question_bank=question_bank,
                    question_type=question_type,
                    content=question_data['content'],
                    answer=question_data.get('answer', None)
                )
                
                # 处理选项，仅对单选题、多选题和判断题进行选项入库
                if question_type in ['单选题', '多选题', '判断题']:
                    options = question_data.get('options', [])
                    for option in options:
                        QuestionOptions.create(
                            question=question,
                            option_text=option['text'],
                            is_correct=option['is_correct']
                        )

            logger.info(f"Questions imported successfully into question bank {question_bank_id}")
            return {"status": "success", "message": "Question bank imported successfully"}

        except Exception as e:
            logger.error(f"Error importing question bank: {str(e)}")
            return {"status": "error", "message": str(e)}

    def map_question_type(self, raw_type):
        """
        映射原始的题目类型到数据库定义的题目类型。
        :param raw_type: 原始题目类型字符串
        :return: 数据库定义的题目类型
        """
        type_map = {
            '单选题': '单选题',
            '多选题': '多选题',
            '填空题': '填空题',
            '简答题': '主观题',
            '判断题': '判断题',
            '选择题': '单选题',  # 处理可能存在的不同名称
            '多选': '多选题'      # 处理可能存在的不同名称
        }
        return type_map.get(raw_type, '主观题')  # 如果找不到，默认返回“主观题”
    
    def create_exam(self, name, start_time, end_time, question_bank_id):
        try:
            exam = Exams.create(
                name=name,
                start_time=start_time,
                end_time=end_time,
                question_bank=question_bank_id
            )
            logger.info(f"Exam '{name}' created successfully")
            return {"status": "success", "message": "Exam created successfully", "exam_id": exam.id}
        except Exception as e:
            logger.error(f"Error creating exam '{name}': {str(e)}")
            return {"status": "error", "message": str(e)}

    def delete_exam(self, exam_id):
        try:
            exam = Exams.get_by_id(exam_id)
            exam.delete_instance(recursive=True)
            logger.info(f"Exam ID '{exam_id}' deleted successfully")
            return {"status": "success", "message": "Exam deleted successfully"}
        except DoesNotExist:
            logger.error(f"Exam ID '{exam_id}' does not exist")
            return {"status": "error", "message": "Exam not found"}

    def edit_exam(self, exam_id, name=None, start_time=None, end_time=None):
        try:
            exam = Exams.get_by_id(exam_id)
            if name:
                exam.name = name
            if start_time:
                exam.start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
                print(exam.start_time)
            if end_time:
                exam.end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
            exam.save()
            logger.info(f"Exam ID '{exam_id}' updated successfully")
            return {"status": "success", "message": "Exam updated successfully"}
        except DoesNotExist:
            logger.error(f"Exam ID '{exam_id}' does not exist")
            return {"status": "error", "message": "Exam not found"}

    def assign_questions_to_exam(self, exam_id, question_ids_with_scores):
        try:
            # 首先删除已有的试题
            ExamQuestions.delete().where(ExamQuestions.exam == exam_id).execute()

            for item in question_ids_with_scores:
                question_id = item['question_id']
                score = item['score']
                ExamQuestions.create(
                    exam=exam_id,
                    question=question_id,
                    score=score
                )
            logger.info(f"Questions assigned to exam ID '{exam_id}' successfully")
            return {"status": "success", "message": "Questions assigned to exam successfully"}
        except Exception as e:
            logger.error(f"Error assigning questions to exam ID '{exam_id}': {str(e)}")
            return {"status": "error", "message": str(e)}

    def auto_grade_exam(self, exam_id):
        try:
            exam_questions = ExamQuestions.select().where(ExamQuestions.exam == exam_id)
            for eq in exam_questions:
                if eq.question.question_type in ['单选题', '多选题', '判断题']:
                    student_answers = StudentAnswers.select().where(
                        StudentAnswers.exam == exam_id,
                        StudentAnswers.question == eq.question
                    )
                    correct_options = QuestionOptions.select().where(
                        QuestionOptions.question == eq.question,
                        QuestionOptions.is_correct == True
                    )
                    correct_option_ids = [str(option.id) for option in correct_options]

                    for sa in student_answers:
                        if eq.question.question_type == '单选题':
                            if sa.selected_option and str(sa.selected_option.id) in correct_option_ids:
                                sa.reserved1 = str(eq.score)
                            else:
                                sa.reserved1 = '0'
                        elif eq.question.question_type == '多选题':
                            student_option_ids = sa.answer_text.split(',') if sa.answer_text else []
                            if set(student_option_ids) == set(correct_option_ids):
                                sa.reserved1 = str(eq.score)
                            else:
                                sa.reserved1 = '0'
                        elif eq.question.question_type == '判断题':
                            if sa.selected_option and str(sa.selected_option.id) in correct_option_ids:
                                sa.reserved1 = str(eq.score)
                            else:
                                sa.reserved1 = '0'
                        sa.save()

            # 计算每个学生的总成绩并保存到 StudentGrades 表
            self.calculate_and_save_total_grades(exam_id)

            logger.info(f"Exam ID '{exam_id}' auto graded successfully")
            return {"status": "success", "message": "Exam auto graded successfully"}
        except Exception as e:
            logger.error(f"Error auto grading exam ID '{exam_id}': {str(e)}")
            return {"status": "error", "message": str(e)}

    def calculate_and_save_total_grades(self, exam_id):
        # 获取参加考试的所有学生
        students = Students.select().join(StudentAnswers).where(StudentAnswers.exam == exam_id).distinct()
        for student in students:
            # 计算学生的总成绩
            total_grade = 0.0
            student_answers = StudentAnswers.select().where(
                StudentAnswers.exam == exam_id,
                StudentAnswers.student == student
            )
            for sa in student_answers:
                if sa.reserved1:
                    total_grade += float(sa.reserved1)

            # 更新或创建 StudentGrades 表中的记录
            student_grade, created = StudentGrades.get_or_create(
                student=student,
                exam=exam_id,
                defaults={'grade': total_grade}
            )
            if not created:
                student_grade.grade = total_grade
                student_grade.save()

    def view_exam_grades(self, exam_id, student_id=None, student_name=None):
        try:
            query = StudentGrades.select().where(StudentGrades.exam == exam_id)
            if student_id:
                query = query.join(Students).where(Students.student_id.contains(student_id))
            elif student_name:
                query = query.join(Students).where(Students.name.contains(student_name))

            grades = []
            for sg in query:
                grades.append({
                    "student_id": sg.student.student_id,
                    "name": sg.student.name,
                    "grade": sg.grade
                })
            logger.info(f"Grades retrieved for exam ID '{exam_id}'")
            return {"status": "success", "grades": grades}
        except Exception as e:
            logger.error(f"Error retrieving grades for exam ID '{exam_id}': {str(e)}")
            return {"status": "error", "message": str(e)}

    def generate_exam_report(self, exam_id):
        try:
            exam_questions = ExamQuestions.select().where(ExamQuestions.exam == exam_id)
            report = []
            for eq in exam_questions:
                total_attempts = StudentAnswers.select().where(
                    StudentAnswers.exam == exam_id,
                    StudentAnswers.question == eq.question
                ).count()
                correct_attempts = StudentAnswers.select().join(QuestionOptions).where(
                    StudentAnswers.exam == exam_id,
                    StudentAnswers.question == eq.question,
                    QuestionOptions.is_correct == True
                ).count()
                correct_rate = (correct_attempts / total_attempts * 100) if total_attempts else 0
                report.append({
                    "question_content": eq.question.content,
                    "correct_rate": correct_rate
                })
            logger.info(f"Exam report generated for exam ID '{exam_id}'")
            return {"status": "success", "report": report}
        except Exception as e:
            logger.error(f"Error generating report for exam ID '{exam_id}': {str(e)}")
            return {"status": "error", "message": str(e)}


# 管理员模块
class AdminModule:

    def login(self, username, password):
        try:
            # 验证管理员用户名和密码
            admin = Admins.get(Admins.admin_id == username, Admins.password == password)
            logger.info(f"Admin {username} logged in successfully")
            return {"status": "success", "message": "Login successful"}
        except DoesNotExist:
            logger.warning(f"Login failed for admin {username}")
            return {"status": "error", "message": "Invalid credentials"}

    def logout(self):
        # 处理管理员注销
        logger.info("Admin logged out")
        return {"status": "success", "message": "Logout successful"}

    def modify_teacher_account(self, action, teacher_id=None, teacher_info=None):
        try:
            if action == 'add':
                Teachers.create(**teacher_info)
                logger.info(f"Teacher {teacher_info['teacher_id']} added successfully")
                return {"status": "success", "message": "Teacher added successfully"}

            elif action == 'update':
                teacher = Teachers.get(Teachers.teacher_id == teacher_id)  # 获取特定的教师记录
                teacher.name = teacher_info['name']  # 更新姓名
                teacher.gender = teacher_info['gender']  # 更新性别
                teacher.phone_number = teacher_info['phone_number']  # 更新手机号
                teacher.password = teacher_info['password']  # 更新密码
                teacher.save()  # 保存修改
                logger.info(f"Teacher {teacher_id} updated successfully")
                return {"status": "success", "message": "Teacher updated successfully"}


            elif action == 'delete':
                teacher = Teachers.get(Teachers.teacher_id == teacher_id)
                teacher.delete_instance()
                logger.info(f"Teacher {teacher_id} deleted successfully")
                return {"status": "success", "message": "Teacher deleted successfully"}

            elif action == 'query':
                if teacher_id:
                    teachers = Teachers.select().where(Teachers.teacher_id == teacher_id)
                elif teacher_info and 'name' in teacher_info:
                    teachers = Teachers.select().where(Teachers.name.contains(teacher_info['name']))
                else:
                    teachers = Teachers.select()

                teachers_list = [{"teacher_id": t.teacher_id, "name": t.name, "gender": t.gender, "phone_number": t.phone_number} for t in teachers]
                return {"status": "success", "teachers": teachers_list}

            else:
                return {"status": "error", "message": "Invalid action"}
        
        except DoesNotExist:
            logger.error(f"Teacher {teacher_id} does not exist")
            return {"status": "error", "message": "Teacher not found"}
        except Exception as e:
            logger.error(f"Error modifying teacher {teacher_id}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def modify_student_account(self, action, student_id=None, student_info=None):
        try:
            if action == 'add':
                Students.create(**student_info)
                logger.info(f"Student {student_info['student_id']} added successfully")
                return {"status": "success", "message": "Student added successfully"}

            elif action == 'update':
                student = Students.get(Students.student_id == student_id)  # 获取特定学生实例
                student.name = student_info['name']  # 更新姓名
                student.gender = student_info['gender']  # 更新性别
                student.phone_number = student_info['phone_number']  # 更新手机号
                student.password = student_info['password']  # 更新密码
                student.save()  # 保存更改
                logger.info(f"Student {student_id} updated successfully")
                return {"status": "success", "message": "Student updated successfully"}


            elif action == 'delete':
                student = Students.get(Students.student_id == student_id)
                student.delete_instance()
                logger.info(f"Student {student_id} deleted successfully")
                return {"status": "success", "message": "Student deleted successfully"}

            elif action == 'query':
                if student_id:
                    students = Students.select().where(Students.student_id == student_id)
                elif student_info and 'name' in student_info:
                    students = Students.select().where(Students.name.contains(student_info['name']))
                else:
                    students = Students.select()

                students_list = [{"student_id": s.student_id, "name": s.name, "gender": s.gender, "phone_number": s.phone_number} for s in students]
                return {"status": "success", "students": students_list}

            else:
                return {"status": "error", "message": "Invalid action"}
        
        except DoesNotExist:
            logger.error(f"Student {student_id} does not exist")
            return {"status": "error", "message": "Student not found"}
        except Exception as e:
            logger.error(f"Error modifying student {student_id}: {str(e)}")
            return {"status": "error", "message": str(e)}

    def log_system_activity(self, operation):
        # 记录系统活动日志
        logger.info(f"System operation: {operation}")
        return {"status": "success", "message": f"Operation '{operation}' logged"}
#api.py
from datetime import datetime
import os
import tempfile
from flask import Flask, redirect, request, jsonify, render_template, session, url_for
from methods import StudentModule, TeacherModule, AdminModule
from models import ExamQuestions, Exams, QuestionBanks, QuestionOptions, Questions, StudentAnswers, StudentGrades, Students
app = Flask(__name__)

student_module = StudentModule()
teacher_module = TeacherModule()
admin_module = AdminModule()

# 首页
@app.route('/')
def home():
    return render_template('index.html')

# 学生模块 API
app.secret_key = 'your_secret_key'  # Flask session 需要一个 secret key
# 学生注册
@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        data = request.form
        result = student_module.register(
            student_id=data['student_id'],
            name=data['name'],
            student_class=data['student_class'],
            gender=data['gender'],
            phone_number=data['phone_number'],
            password=data['password'],
            confirm_password=data['confirm_password']
        )
        if result["status"] == "success":
            return redirect(url_for('student_login'))
        return jsonify(result), 400
    return render_template('student_register.html')

# 学生登录
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        data = request.form
        result = student_module.login(
            student_id=data['student_id'],
            password=data['password']
        )
        if result["status"] == "success":
            # 登录成功后将学生 ID 存储到 session 中
            student = Students.get(Students.student_id == data['student_id'])
            session['student_id'] = student.id
            return redirect(url_for('exam_list'))
        return jsonify(result), 400
    return render_template('student_login.html')

# 学生注销
@app.route('/student/logout', methods=['GET'])
def student_logout():
    # 注销时清除 session 中的 student_id
    session.pop('student_id', None)
    result = student_module.logout()
    return render_template('index.html')

# 参加考试页面
@app.route('/student/exam_list', methods=['GET'])
def exam_list():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    result = student_module.list_exams()
    if result["status"] == "success":
        exams = result["exams"]
        return render_template('student_exam_list.html', exams=exams)
    else:
        return jsonify(result), 400

# 自定义过滤器，将索引转换为字母 (A, B, C...)
@app.template_filter('char_from_index')
def char_from_index(index):
    return chr(64 + index)  # 64 是 ASCII 中 "@" 的值，加上索引生成 A, B, C, ...

# 注册过滤器
app.jinja_env.filters['char_from_index'] = char_from_index
# 参加特定考试页面
@app.route('/student/exam/<int:exam_id>', methods=['GET', 'POST'])
def take_exam(exam_id):
    if 'student_id' not in session:
        return redirect(url_for('student_login'))

    exam = Exams.get_or_none(Exams.id == exam_id)
    if not exam:
        return "考试不存在", 404

    exam_questions = ExamQuestions.select().where(ExamQuestions.exam == exam)
    questions = [eq.question for eq in exam_questions]

    student_answers = {}
    if 'student_id' in session:
        student_id = session['student_id']
        answers = StudentAnswers.select().where(
            (StudentAnswers.student_id == student_id) & 
            (StudentAnswers.exam_id == exam_id)
        )
        for answer in answers:
            student_answers[answer.question.id] = answer.selected_option.id if answer.selected_option else answer.answer_text

    if request.method == 'POST':
        data = request.form
        answers = {}
        for question in questions:
            if question.question_type in ['单选题', '判断题']:
                selected_value = data.get(f'question_{question.id}')
                if selected_value:
                    selected_option_id, selected_option_text = selected_value.split('-')
                    # 验证选项 ID 是否在数据库中存在
                    option = QuestionOptions.get_or_none(QuestionOptions.id == selected_option_id)
                    print(f"Debug: Received option ID = {selected_option_id}, Found in DB = {option}")
                    if option:
                        answers[question.id] = {"selected_option_id": int(selected_option_id), "answer_text": selected_option_text}
                    else:
                        return render_template('student_take_exam.html', exam=exam, questions=questions, student_answers=student_answers, error="选项无效")
            elif question.question_type == '多选题':
                selected_values = data.getlist(f'question_{question.id}')
                if selected_values:
                    selected_option_ids = []
                    selected_option_texts = []
                    for value in selected_values:
                        option_id, option_text = value.split('-')
                        option = QuestionOptions.get_or_none(QuestionOptions.id == option_id)
                        print(f"Debug: Received option ID = {option_id}, Found in DB = {option}")
                        if option:
                            selected_option_ids.append(option_id)
                            selected_option_texts.append(option_text)
                        else:
                            return render_template('student_take_exam.html', exam=exam, questions=questions, student_answers=student_answers, error="多选题的选项无效")
                    answers[question.id] = {
                        "selected_option_id": ",".join(selected_option_ids),
                        "answer_text": ",".join(selected_option_texts)
                    }
            else:
                answer_text = data.get(f'question_{question.id}_text')
                if answer_text:
                    answers[question.id] = {"answer_text": answer_text}

        result = student_module.submit_exam_answers(session['student_id'], exam_id, answers)
        if result["status"] == "success":
            return redirect(url_for('exam_list'))
        else:
            return render_template('student_take_exam.html', exam=exam, questions=questions, student_answers=student_answers, error=result["message"])

    return render_template('student_take_exam.html', exam=exam, questions=questions, student_answers=student_answers)

# 教师模块 API
# 教师注册
@app.route('/teacher/register', methods=['GET', 'POST'])
def teacher_register():
    if request.method == 'POST':
        data = request.form
        result = teacher_module.register(
            teacher_id=data['teacher_id'],
            name=data['name'],
            gender=data['gender'],
            phone_number=data['phone_number'],
            password=data['password'],
            confirm_password=data['confirm_password']
        )
        if result["status"] == "success":
            return redirect(url_for('teacher_login'))
        return jsonify(result), 400
    return render_template('teacher_register.html')

# 教师登录
@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        data = request.form
        result = teacher_module.login(
            teacher_id=data['teacher_id'],
            password=data['password']
        )
        if result["status"] == "success":
            # 登录成功后将教师ID存储到 session 中
            session['teacher_id'] = data['teacher_id']
            return redirect(url_for('teacher_dashboard'))
        else:
            # 如果登录失败，返回错误信息
            return render_template('teacher_login.html', error=result['message']), 400
    return render_template('teacher_login.html')

# 教师注销
@app.route('/teacher/logout', methods=['GET'])
def teacher_logout():
    # 清除 session 中的 teacher_id
    session.pop('teacher_id', None)
    result = teacher_module.logout()
    return render_template('index.html')

# 教师仪表盘
@app.route('/teacher/dashboard', methods=['GET'])
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    return render_template('teacher_dashboard.html', teacher_id=session['teacher_id'])

# 管理题库
@app.route('/teacher/manage_question_banks', methods=['GET', 'POST'])
def manage_question_banks():
    if request.method == 'POST':
        action = request.form['action']
        question_bank_id = request.form.get('question_bank_id', None)
        question_bank_name = request.form.get('question_bank_name', None)
        
        if action == 'add':
            # 添加题库
            QuestionBanks.create(name=question_bank_name)
            return redirect(url_for('manage_question_banks'))
        
        elif action == 'delete':
            # 删除题库
            question_bank = QuestionBanks.get(QuestionBanks.id == question_bank_id)
            question_bank.delete_instance()
            return redirect(url_for('manage_question_banks'))

    # 获取题库列表
    question_banks = QuestionBanks.select()
    return render_template('teacher_manage_question_banks.html', question_banks=question_banks)

# 修改题目
@app.route('/teacher/question_bank/<int:question_bank_id>/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_bank_id, question_id):
    if 'teacher_id' not in session:
        return redirect('/teacher/login')

    try:
        question_bank = QuestionBanks.get_by_id(question_bank_id)
    except QuestionBanks.DoesNotExist:
        return "题库不存在", 404

    question = teacher_module.get_question_by_id(question_id)
    if not question:
        return "题目不存在", 404

    if request.method == 'POST':
        question_type = request.form['question_type']
        content = request.form['content']
        answer = request.form.get('answer', '')

        teacher_module.update_question(question_id, question_type, content, answer)

        # 处理选项
        options = request.form.getlist('options')
        correct_options = request.form.getlist('correct_option')

        options_data = []
        for idx, option_text in enumerate(options):
            is_correct = str(idx + 1) in correct_options
            options_data.append((option_text, is_correct))

        teacher_module.update_options(question_id, options_data)

        return redirect(url_for('question_bank_details', question_bank_id=question_bank_id))

    else:
        options = QuestionOptions.select().where(QuestionOptions.question == question_id)
        return render_template('edit_question.html', question_bank=question_bank, question=question, options=options)

# 题目明细
@app.route('/teacher/question_bank/<int:question_bank_id>', methods=['GET', 'POST'])
def question_bank_details(question_bank_id):
    question_bank = QuestionBanks.get_or_none(QuestionBanks.id == question_bank_id)
    if not question_bank:
        return {"status": "error", "message": "Question bank not found"}, 404

    if request.method == 'POST':
        action = request.form['action']
        
        if action == 'import':
            file = request.files['file']
            if not file:
                return jsonify({"status": "error", "message": "No file provided"}), 400
            
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            
            result = teacher_module.import_question_bank(file_path, question_bank_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)

            return redirect(url_for('question_bank_details', question_bank_id=question_bank_id))
        
        elif action == 'add_question':
            question_type = request.form['question_type']
            content = request.form['content']
            answer = request.form['answer']
            
            new_question = Questions.create(
                question_bank=question_bank,
                question_type=question_type,
                content=content,
                answer=answer
            )
            
            if question_type in ['单选题', '多选题', '判断题']:
                options = request.form.getlist('options')
                correct_options = request.form.getlist('correct_option')
                for index, option_text in enumerate(options):
                    QuestionOptions.create(
                        question=new_question,
                        option_text=option_text,
                        is_correct=(str(index) in correct_options)
                    )
            
            return redirect(url_for('question_bank_details', question_bank_id=question_bank_id))
        
        elif action == 'delete_question':
            question_id = request.form['question_id']
            question = Questions.get(Questions.id == question_id)
            question.delete_instance(recursive=True)
            return redirect(url_for('question_bank_details', question_bank_id=question_bank_id))
        
        elif action == 'edit_question':
            question_id = request.form['question_id']
            question = Questions.get(Questions.id == question_id)
            question.content = request.form['content']
            question.answer = request.form['answer']
            question.save()
            
            if question.question_type in ['单选题', '多选题', '判断题']:
                QuestionOptions.delete().where(QuestionOptions.question == question).execute()
                options = request.form.getlist('options')
                correct_options = request.form.getlist('correct_option')
                for index, option_text in enumerate(options):
                    QuestionOptions.create(
                        question=question,
                        option_text=option_text,
                        is_correct=(str(index) in correct_options)
                    )
            
            return redirect(url_for('question_bank_details', question_bank_id=question_bank_id))

    questions = Questions.select().where(Questions.question_bank == question_bank)
    question_data = []
    for question in questions:
        options = QuestionOptions.select().where(QuestionOptions.question == question)
        question_data.append({
            'question': question,
            'options': options
        })
    
    return render_template('question_bank_details.html', question_bank=question_bank, question_data=question_data)

# 考试管理页面
@app.route('/teacher/manage_exams', methods=['GET'])
def manage_exams():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    exams = Exams.select()
    return render_template('teacher_manage_exams.html', exams=exams)

# 创建考试页面
@app.route('/teacher/create_exam', methods=['GET', 'POST'])
def create_exam():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    if request.method == 'POST':
        exam_name = request.form['exam_name']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        question_bank_id = request.form['question_bank_id']

        result = teacher_module.create_exam(
            name=exam_name,
            start_time=start_time,
            end_time=end_time,
            question_bank_id=question_bank_id
        )

        if result["status"] == "success":
            return redirect(url_for('edit_exam', exam_id=result["exam_id"]))
        else:
            return render_template('teacher_create_exam.html', error=result["message"])

    question_banks = QuestionBanks.select()
    return render_template('teacher_create_exam.html', question_banks=question_banks)

# 编辑考试页面
@app.route('/teacher/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
def edit_exam(exam_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    exam = Exams.get_or_none(Exams.id == exam_id)
    if not exam:
        return "考试不存在", 404

    if request.method == 'POST':
        action = request.form['action']
        if action == 'update_exam':
            exam_name = request.form['exam_name']
            start_time = request.form['start_time']
            end_time = request.form['end_time']

            result = teacher_module.edit_exam(
                exam_id=exam_id,
                name=exam_name,
                start_time=start_time,
                end_time=end_time
            )
            if result["status"] == "success":
                return redirect(url_for('manage_exams'))
            else:
                return render_template('teacher_edit_exam.html', exam=exam, error=result["message"])

        elif action == 'assign_questions':
            question_ids = request.form.getlist('question_ids')
            question_scores = request.form.getlist('question_scores')
            question_data = []
            for q_id, score in zip(question_ids, question_scores):
                question_data.append({
                    "question_id": q_id,
                    "score": score
                })
            result = teacher_module.assign_questions_to_exam(exam_id, question_data)
            if result["status"] == "success":
                return redirect(url_for('manage_exams'))
            else:
                return render_template('teacher_edit_exam.html', exam=exam, error=result["message"])

    questions = Questions.select().where(Questions.question_bank == exam.question_bank)
    assigned_questions = ExamQuestions.select().where(ExamQuestions.exam == exam)
    assigned_question_ids = [aq.question.id for aq in assigned_questions]  # 获取已分配的题目ID列表

    return render_template('teacher_edit_exam.html', exam=exam, questions=questions, assigned_question_ids=assigned_question_ids)

# 删除考试
@app.route('/teacher/delete_exam/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    result = teacher_module.delete_exam(exam_id)
    return redirect(url_for('manage_exams'))

# 自动批改客观题
@app.route('/teacher/auto_grade_exam/<int:exam_id>', methods=['POST'])
def auto_grade_exam(exam_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    result = teacher_module.auto_grade_exam(exam_id)
    if result["status"] == "success":
        return redirect(url_for('manage_exams'))
    else:
        return jsonify(result), 400

# 阅卷页面
@app.route('/teacher/grade_exam/<int:exam_id>', methods=['GET', 'POST'])
def grade_exam(exam_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    exam = Exams.get_or_none(Exams.id == exam_id)
    if not exam:
        return "考试不存在", 404

    if request.method == 'POST':
        student_id = request.form.get('student_id') or request.form.get('hidden_student_id')
        if not student_id:
            return "学生ID不存在", 400
        
        try:
            student_id = int(student_id)
        except ValueError:
            return "无效的学生ID", 400

        student = Students.get_or_none(Students.id == student_id)
        if not student:
            return "学生不存在", 404

        grades = {}
        for key in request.form:
            if key.startswith('grade_'):
                question_id = int(key.split('_')[1])
                grades[question_id] = float(request.form[key])

        # 更新每个题目的得分
        for question_id, grade in grades.items():
            question = Questions.get_or_none(Questions.id == question_id)
            if not question:
                continue

            student_answer = StudentAnswers.get_or_none(
                StudentAnswers.exam == exam,
                StudentAnswers.question == question,
                StudentAnswers.student == student
            )
            if student_answer:
                student_answer.reserved1 = str(grade)
                student_answer.save()
            else:
                StudentAnswers.create(
                    exam=exam,
                    question=question,
                    student=student,
                    reserved1=str(grade),
                    answer_text="未作答"
                )

        # 计算并保存学生的总成绩
        total_grade = sum(grades.values())

        student_grade, created = StudentGrades.get_or_create(
            student=student,
            exam=exam,
            defaults={'grade': total_grade}
        )
        if not created:
            student_grade.grade = total_grade
            student_grade.save()

        return redirect(url_for('grade_exam', exam_id=exam_id, student_id=student_id))

    students = Students.select().join(StudentAnswers).where(StudentAnswers.exam == exam).distinct()
    student_id = request.args.get('student_id')
    selected_student = None
    student_answers = []

    if student_id:
        selected_student = Students.get_or_none(Students.id == int(student_id))
        if selected_student:
            student_answers = StudentAnswers.select().where(
                StudentAnswers.exam == exam,
                StudentAnswers.student == selected_student
            ).join(Questions)

    # 获取每个问题的最大分数
    exam_questions = ExamQuestions.select().where(ExamQuestions.exam == exam)
    question_score_mapping = {eq.question.id: eq.score for eq in exam_questions}

    # 为多选题预先获取选项，以避免在模板中查询数据库
    option_mapping = {}
    for sa in student_answers:
        if sa.question.question_type == '多选题' and sa.answer_text:
            option_ids = sa.answer_text.split(',')
            options = QuestionOptions.select().where(QuestionOptions.id.in_(option_ids))
            option_mapping[sa.question.id] = {option.id: option.option_text for option in options}

    # 确保在视图函数中正确传递模板变量
    return render_template(
        'teacher_grade_exam.html',
        exam=exam,
        students=students,
        student_answers=student_answers,
        selected_student=selected_student,
        question_score_mapping=question_score_mapping,
        option_mapping=option_mapping
    )

# 成绩查询
@app.route('/teacher/view_grades/<int:exam_id>', methods=['GET'])
def view_grades(exam_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    student_id = request.args.get('student_id', None)
    student_name = request.args.get('student_name', None)
    result = teacher_module.view_exam_grades(exam_id, student_id, student_name)
    if result["status"] == "success":
        grades = result["grades"]
        return render_template('teacher_view_grades.html', exam_id=exam_id, grades=grades)
    else:
        return jsonify(result), 400

# 考试成绩数据报表
@app.route('/teacher/exam_report/<int:exam_id>', methods=['GET'])
def exam_report(exam_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    result = teacher_module.generate_exam_report(exam_id)
    if result["status"] == "success":
        report = result["report"]
        return render_template('teacher_exam_report.html', exam_id=exam_id, report=report)
    else:
        return jsonify(result), 400

# 管理员登录
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.form
        result = admin_module.login(
            username=data['username'],
            password=data['password']
        )
        if result["status"] == "success":
            # 登录成功后将管理员ID存储到session中
            session['admin_id'] = data['username']
            return redirect(url_for('admin_dashboard'))  # 假设登录后跳转到管理员的仪表盘页面
        return jsonify(result), 400
    return render_template('admin_login.html')

# 管理员注销
@app.route('/admin/logout', methods=['GET'])
def admin_logout():
    # 清除 session 中的 admin_id
    session.pop('admin_id', None)
    result = admin_module.logout()
    return render_template('index.html')

# 管理员仪表盘
@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# 学生账户管理页面
@app.route('/admin/manage_students', methods=['GET'])
def manage_students():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_manage_students.html')

# 教师账户管理页面
@app.route('/admin/manage_teachers', methods=['GET'])
def manage_teachers():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_manage_teachers.html')

# 系统日志查看页面
@app.route('/admin/view_logs', methods=['GET'])
def view_logs():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    try:
        local_date = datetime.strftime(datetime.now(),"%Y%m%d")
        with open(f'./logs/{local_date}.log', 'r') as f:
            logs = f.readlines()
        return render_template('admin_view_logs.html', logs=logs)
    except FileNotFoundError:
        return "日志文件不存在"

# 查询教师账户
@app.route('/admin/search_teacher', methods=['POST'])
def search_teacher():
    teacher_id = request.form['teacher_id']
    name = request.form['name']
    result = admin_module.modify_teacher_account(action='query', teacher_id=teacher_id, teacher_info={'name': name})
    return render_template('admin_manage_teachers.html', teachers=result['teachers'])

# 查询学生账户
@app.route('/admin/search_student', methods=['POST'])
def search_student():
    student_id = request.form['student_id']
    name = request.form['name']
    result = admin_module.modify_student_account(action='query', student_id=student_id, student_info={'name': name})
    return render_template('admin_manage_students.html', students=result['students'])

# 更新教师账户
@app.route('/admin/update_teacher/<teacher_id>', methods=['POST'])
def update_teacher(teacher_id):
    teacher_info = {
        'name': request.form['name'],
        'gender': request.form['gender'],
        'phone_number': request.form['phone_number'],
        'password': request.form['password']
    }
    
    print(f"Teacher info: {teacher_info}")
    
    # 更新教师账户
    admin_module.modify_teacher_account(action='update', teacher_id=teacher_id, teacher_info=teacher_info)
    return render_template('admin_manage_teachers.html')

# 更新学生账户
@app.route('/admin/update_student/<student_id>', methods=['POST'])
def update_student(student_id):
    student_info = {
        'name': request.form['name'],
        'gender': request.form['gender'],
        'phone_number': request.form['phone_number'],
        'password': request.form['password']
    }
    admin_module.modify_student_account(action='update', student_id=student_id, student_info=student_info)
    return render_template('admin_manage_students.html')

# 新增教师账户页面
@app.route('/admin/admin_add_teacher', methods=['GET'])
def add_teacher_page():
    return render_template('admin_add_teacher.html')

# 处理新增教师账户表单提交的路由
@app.route('/admin/add_teacher', methods=['POST'])
def add_teacher():
    teacher_info = {
        'teacher_id': request.form['teacher_id'],
        'name': request.form['name'],
        'gender': request.form['gender'],
        'phone_number': request.form['phone_number'],
        'password': request.form['password']
    }
    # 调用方法处理教师的新增
    result = admin_module.modify_teacher_account(action='add', teacher_info=teacher_info)
    if result["status"] == "success":
        return render_template('admin_manage_teachers.html')
    else:
        return result["message"], 400

# 新增学生账户页面
@app.route('/admin/admin_add_student', methods=['GET'])
def add_student_page():
    return render_template('admin_add_student.html')

# 处理新增学生账户表单提交的路由
@app.route('/admin/add_student', methods=['POST'])
def add_student():
    student_info = {
        'student_id': request.form['student_id'],
        'name': request.form['name'],
        'gender': request.form['gender'],
        'phone_number': request.form['phone_number'],
        'password': request.form['password']
    }
    # 调用方法处理学生的新增
    result = admin_module.modify_student_account(action='add', student_info=student_info)
    if result["status"] == "success":
        return render_template('admin_manage_students.html')
    else:
        return result["message"], 400

# 删除教师账户
@app.route('/admin/delete_teacher/<teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    admin_module.modify_teacher_account(action='delete', teacher_id=teacher_id)
    return redirect(url_for('manage_teachers'))

# 删除学生账户
@app.route('/admin/delete_student/<student_id>', methods=['POST'])
def delete_student(student_id):
    admin_module.modify_student_account(action='delete', student_id=student_id)
    return redirect(url_for('manage_students'))

# 启动 Flask 服务
if __name__ == '__main__':
    app.run(debug=True)
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


*论文目录*
1 绪论	2
1.1 课题的研究背景	2
1.2 国内外发展和现状	2
1.3 系统研究内容概述	2
1.4 论文结构	2
2 系统相关技术的介绍	4
2.1 Flask框架	4
2.2 MySQL数据库	6
2.4 微信小程序开发	10
2.5 大语言模型的应用	10
3 系统可行性	13
3.1 可行性分析的目的	13
3.2 经济可行性分析	14
3.3 操作可行性分析	15
3.4 技术可行性分析	17
4 系统需求分析	20
4.1 系统用户需求分析	20
4.2 系统功能需求分析	20
4.3 数据流分析	20
5 系统设计	20
5.1 系统设计架构与工作原理	20
5.2 系统总体设计	20
5.3 系统数据模型设计	20
5.4 系统界面设计	20
6 系统实现	20
6.1 开发环境的搭建	20
6.2 各模块的实现过程	21
6.3 系统前后端的集成与交互实现	21
7 结论	21
参考文献	21
致谢	21
*需要注意的事项*
如果有需要放图的地方情帮我留出位置来。
代码部分留空
*你需要做的事情*
6.2 各模块的实现过程
学生模块：实现注册、登录和考试功能。
教师模块：实现题库管理、考试管理和成绩管理功能，应用大语言模型进行题库的自动解析。
管理员模块：实现账户管理和系统维护功能。

生成论文相关内容
