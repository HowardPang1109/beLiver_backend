import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import io

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)
text_model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=genai.types.GenerationConfig(temperature=0))

def get_gemini_project_draft(file_content: bytes):
  pdf_file = fitz.open(stream=io.BytesIO(file_content), filetype="pdf")
  all_text = ""

  for page in pdf_file:
    all_text += page.get_text()

  prompt = f"""
請閱讀以下 PDF 內容，並依據指定格式進行結構化整理，將專案資訊轉換成 JSON 資料，結構如下：
- 專案（Project）：包含專案整體資訊。
- 里程碑（Milestone）：專案中各階段的重要成果與期間。
- 任務（Task）：從里程碑摘要中推論與拆解出具體工作項目。

請依照以下格式輸出 JSON：
{{
  "projects": [
  {{
    "name": "...",
    "summary": "...",
    "start_time": "...",
    "end_time": "...",
    "due_date": "...",
    "estimated_loading": ...,
    "current_milestone": "...",
    "milestones": [
    {{
      "name": "...",
      "summary": "...",
      "start_time": "...",
      "end_time": "...",
      "estimated_loading": ...,
      "tasks": [
      {{
        "title": "...",
        "description": "...",
        "due_date": "...",
        "estimated_loading": ...,
        "is_completed": false
      }}
      ]
    }}
    ]
  }}
  ]
}}

請遵守以下規則：
1. **所有日期與時間欄位（start_time, end_time, due_date）均需填寫**，不得為 null。
2. **所有 estimated_loading 請給出合理整數估算**（例如 5, 10, 20），不得為 null。
3. 每個 Milestone 至少拆解出 **3 項具體任務（tasks）**。
4. 任務命名與內容應根據里程碑摘要合理拆解，避免過於模糊或重複。
5. **每個任務的 due_date 請根據邏輯先後順序與工時推論，合理分配至 milestone 結束日前。**
6. **請僅回傳符合格式的純 JSON 結果，不需額外說明或註解。**

以下為 PDF 內容：
{all_text}
"""
  response = text_model.generate_content(prompt)
  clean_text = response.text.replace("```json", "").replace("```", "")
  json_data = json.loads(clean_text)
  return json_data
