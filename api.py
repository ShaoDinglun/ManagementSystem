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
