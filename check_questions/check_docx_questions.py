# check_docx_questions.py
import json
import re
from openai import OpenAI
from docx import Document

client = OpenAI(api_key="sk-d876755b98794f45a266e425ec431a70", base_url="https://api.deepseek.com")

class DocxQuestionImporter:
    def __init__(self):
        pass

    def import_question_bank(self, file_path):
        if not file_path.endswith('.docx'):
            raise ValueError("仅支持 Word 文件格式 (.docx)")

        questions = self._read_from_word(file_path)
        results = []

        for question_text in questions:
            prompt = (
                f"请识别以下完整问题的详细内容，并以 JSON 格式输出，不要包含 ``` 标记。"
                f"答案中有多个选项的都为多选题\n"
                f"判断题选项应使用 '对、错' 格式，并在答案中使用对应的对、错。\n"
                f"单选题、多选题题选项应使用 'A、B、C...' 格式，并在答案中使用对应的字母。例如：答案应为 'A' 或 'A, B'.....。全都使用大写字母\n"
                f"结构如下：\n"
                f"{{'question_type': '', 'content': '', 'answer': '', 'options': [{{'text': '', 'is_correct': true/false}}]}}\n"
                f"完整问题：\n{question_text}"
            )

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            
            content = response.choices[0].message.content.strip()
            content = self.clean_non_standard_json(content)
            try:
                recognized_data = json.loads(content)

                # 检查题目内容是否完整
                if recognized_data['question_type'] in ['单选题', '多选题', '判断题']:
                    # 如果没有选项或没有答案，跳过此题
                    # print(recognized_data.get('options'))
                    if not recognized_data.get('options') or not recognized_data.get('answer').strip():
                        # print("题目缺少选项或答案，跳过此题。")
                        continue
                
                if not recognized_data['content'].strip():
                    # print("题目内容缺失，跳过此题。")
                    continue
                
                results.append(recognized_data)
            except json.JSONDecodeError:
                print("识别结果解析失败，跳过此题：", content)

        return results

    def clean_non_standard_json(self, content):
        content = content.replace("'", '"')
        content = re.sub(r'\btrue\b', 'true', content, flags=re.IGNORECASE)
        content = re.sub(r'\bfalse\b', 'false', content, flags=re.IGNORECASE)
        return content

    def _read_from_word(self, file_path):
        document = Document(file_path)
        questions = []
        
        current_question = ""
        for para in document.paragraphs:
            text = para.text.strip()
            if text:
                current_question += text + "\n"
            else:
                if current_question:
                    questions.append(current_question.strip())
                    current_question = ""
        
        if current_question:
            questions.append(current_question.strip())
        
        return questions