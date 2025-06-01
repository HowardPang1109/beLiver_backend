from datetime import datetime
import string
import fitz
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
import json
import io
from dotenv import load_dotenv

# === 初始化 ===
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
text_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=genai.types.GenerationConfig(temperature=0)
)

# === 工具函式 ===
def extract_paragraphs_from_pdf_bytes(file_content: bytes):
    doc = fitz.open(stream=io.BytesIO(file_content), filetype="pdf")
    paragraphs = []
    for page in doc:
        text = page.get_text()
        for para in text.split("\n\n"):
            clean_para = para.strip()
            if len(clean_para) > 30:
                paragraphs.append(clean_para)
    return paragraphs

def create_faiss_index(paragraphs):
    embeddings = embedding_model.encode(paragraphs)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, embeddings

def retrieve_relevant_chunks(query, paragraphs, index, embeddings, top_k):
    query_vec = embedding_model.encode([query])
    D, I = index.search(np.array(query_vec), top_k)
    return [paragraphs[i] for i in I[0]]

def refine_chunks_with_gemini(chunks, target="請整理專案概述、里程碑與任務資訊"):
    context = "\n\n".join(chunks)
    prompt = f"""
你是一位專業的文件理解助手。

請從以下內容中，**挑選出與「{target}」最相關的重要段落（約 5～8 段）**，原封不動列出。不要添加新的內容。

請遵守以下規則：
- 每段以「---」分隔。
- 僅保留原始段落，**請勿改寫內容或重新摘要**。
- 精選段落總長度以約 1000～1500 字為上限。

以下為原始內容：
{context}
"""
    response = text_model.generate_content(prompt)
    return response.text.strip()

def generate_structured_json(context, title, deadline):
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(today)
    prompt = f"""
請閱讀以下內容，並依據指定格式進行結構化整理，將專案資訊轉換成 JSON 資料，結構如下：
- 專案（Project）：包含專案整體資訊。
- 里程碑（Milestone）：專案中各階段的重要成果與期間。
- 任務（Task）：從里程碑摘要中推論與拆解出具體工作項目。
- 今天是 {today}，專案的 start_time 也是 {today}，你之後安排的進度也是從今天開始。
- 專案的 name 為 {title}
- 專案的 due_date 和 end_time 都是 {deadline}

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
      "current_milestone": ...,
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
1. 所有日期與時間欄位（start_time, end_time, due_date）均需填寫，不得為 null。
2. 所有 estimated_loading 請給出合理整數估算（例如 5, 10, 20），不得出現 % 的圖案，也不得為 null。
3. current_milestone 請務必填寫 milestone 陣列裡面第一個 milestone 的 'name'，不得為 null。
4. 每個 Milestone 至少拆解出 3 項具體任務（tasks）。
5. 任務命名與內容應根據里程碑摘要合理拆解，避免過於模糊或重複。
6. 每個任務的 due_date 請根據邏輯先後順序與工時推論，合理分配至 milestone 結束日前。
7. Milestone 的 estimated_loading 不可比底下所有任務的 estimated_loading 總和多超過 10 小時。
8. estimated_loading 工時估算請依任務類型給予合理範圍，具體如下：
   - 文書處理類任務（如報告撰寫、資料彙整、會議記錄等）通常介於 5～10 小時
   - 程式開發類任務（如撰寫 API、資料庫設計、前端實作等）通常介於 20～60 小時
9. 請先不要讓 project 的總 estimated_loading 超過 100 小時，最多到 99 小時。
10. 請僅回傳符合格式的純 JSON 結果，不需額外說明或註解。

以下為內容：
{context}
"""
    response = text_model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "")
    return json.loads(clean_text)

# === 主 API 函式 ===
def get_gemini_project_draft(file_content: bytes, title: string, deadline: datetime):
    paragraphs = extract_paragraphs_from_pdf_bytes(file_content)
    index, embeddings = create_faiss_index(paragraphs)
    top_chunks = retrieve_relevant_chunks("請整理專案概述、里程碑與任務資訊", paragraphs, index, embeddings, top_k=15)
    refined_context = refine_chunks_with_gemini(top_chunks)
    structured_json = generate_structured_json(refined_context, title, deadline)
    return structured_json
