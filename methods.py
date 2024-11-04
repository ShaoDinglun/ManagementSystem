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
            print(answers)
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
