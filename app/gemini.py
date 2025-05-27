import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

text_model = genai.GenerativeModel(model_name="gemini-1.5-flash") # 使用文字模型即可

doc = fitz.open("uploads/example.pdf")
all_text = ""

# 逐頁提取純文字
for i in range(len(doc)):
    page = doc.load_page(i)
    all_text += page.get_text() # 提取頁面所有文字

# 合併所有文字後，一次性傳給模型
prompt = f"""
請閱讀以下 PDF 的內容，並根據以下 schema 分析與組織資料：
- 專案（Project）
- 里程碑（Milestone）
- 任務（Task）

請將資訊依照以下格式輸出為 JSON：
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
              "is_completed": true
            }}
          ]
        }}
      ]
    }}
  ]
}}

以下為 PDF 內容：
{all_text}

注意：不要有額外說明
"""


# 注意：gemini-1.5-flash 有非常大的上下文窗口，適合處理大量文字
response = text_model.generate_content(prompt)

print("\n=== 最終綜合摘要 ===")
print(response.text)

clean_text = response.text.replace("```json", "").replace("```", "")

json_data = json.loads(clean_text)