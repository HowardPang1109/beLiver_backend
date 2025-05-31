import fitz
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# === Step 1: 初始化模型與金鑰 ===
load_dotenv()  # 載入 .env 中的變數
GEMINI_KEY = os.getenv("GEMINI_KEY")  # 取得 Gemini API 金鑰
genai.configure(api_key=GEMINI_KEY)  # 設定 Gemini API 金鑰

# 初始化句子嵌入模型（MiniLM）
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 初始化 Gemini 模型（flash 版適合即時摘要）
text_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=genai.types.GenerationConfig(temperature=0)  # 設定為穩定輸出
)

# === Step 2: 解析 PDF 為段落 ===
def extract_paragraphs_from_pdf(pdf_path):
    """從 PDF 中解析出段落文字（排除過短段落）"""
    doc = fitz.open(pdf_path)
    paragraphs = []
    for page in doc:
        text = page.get_text()
        # 根據兩個換行分段
        for para in text.split("\n\n"):
            clean_para = para.strip()
            if len(clean_para) > 30:  # 忽略太短的段落
                paragraphs.append(clean_para)
    return paragraphs

# === Step 3: 建立向量索引 ===
def create_faiss_index(paragraphs):
    """將段落轉為向量，並建立 FAISS 索引以供後續語意檢索"""
    embeddings = embedding_model.encode(paragraphs)
    index = faiss.IndexFlatL2(embeddings.shape[1])  # 建立 L2 距離索引
    index.add(np.array(embeddings))  # 加入段落向量
    return index, embeddings

# === Step 4: 進行語意檢索 ===
def retrieve_relevant_chunks(query, paragraphs, index, embeddings, top_k):
    """根據使用者查詢語句，檢索與語意最相近的前 top_k 段落"""
    query_vec = embedding_model.encode([query])
    D, I = index.search(np.array(query_vec), top_k)  # 檢索最相近的索引
    return [paragraphs[i] for i in I[0]]  # 回傳對應段落內容

def refine_chunks_with_gemini(chunks, target="請整理專案概述、里程碑與任務資訊"):
    """使用 Gemini 模型對初步檢索的段落進行第二階段精選（不改寫原文）"""
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

# === Step 5: 呼叫 Gemini 產出結構化 JSON ===
def generate_structured_json(context):
    """將選出的段落進一步轉換為具結構的專案資料 JSON 格式"""
    prompt = f"""
請閱讀以下內容，並依據指定格式進行結構化整理，將專案資訊轉換成 JSON 資料，結構如下：
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
      "current_milestone": "null",
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
6. **Milestone 的 estimated_loading 不可比底下所有任務的 estimated_loading 總和多超過 10 小時。**
7. **estimated_loading 工時估算請依任務類型給予合理範圍，具體如下：**
   - **文書處理類任務**（如報告撰寫、資料彙整、會議記錄等）通常介於 **5～10 小時**，例如：
     - 「撰寫會議記錄」：estimated_loading = 5
     - 「彙整市場資料」：estimated_loading = 8
   - **程式開發類任務**（如撰寫 API、資料庫設計、前端實作等）通常介於 **20～60 小時**，例如：
     - 「開發後端 API」：estimated_loading = 40
     - 「建立資料庫 schema 並撰寫 seed script」：estimated_loading = 30
8. **請僅回傳符合格式的純 JSON 結果，不需額外說明或註解。**

以下為內容：
{context}
"""
    response = text_model.generate_content(prompt)
    raw_text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw_text)  # 將回應文字轉為 JSON 物件

# === 主流程 ===
def main(pdf_path):
    """主執行流程：從 PDF 到 JSON 的全流程串接"""
    print("📄 正在處理 PDF...")
    paragraphs = extract_paragraphs_from_pdf(pdf_path)

    print("🔍 建立向量索引...")
    index, embeddings = create_faiss_index(paragraphs)

    print("🤖 檢索相關段落...")
    query = "請整理專案概述、里程碑與任務資訊"
    top_chunks = retrieve_relevant_chunks(query, paragraphs, index, embeddings, top_k=15)

    print("🧠 進行 Gemini 精煉摘要...")
    refined_context = refine_chunks_with_gemini(top_chunks)

    print(refined_context)

    print("📦 呼叫 Gemini 結構化 JSON...")
    structured_json = generate_structured_json(refined_context)

    print("✅ 完成！已生成 JSON 結構：")
    print(json.dumps(structured_json, indent=2, ensure_ascii=False))

    return structured_json

# 程式入口點
if __name__ == "__main__":
    """
    改動後優點：
    1. 減少模型輸入長度，提高效率和準確度
    分段切割、過濾短段落：只保留 >30 字的段落，避免丟入過多無意義或太短的文字。
    FAISS 向量檢索選出相關段落：先用向量檢索挑出與查詢最相關的段落，縮小上下文範圍，讓模型只聚焦在重要內容。
    減少輸入字數：模型輸入字數少了，回應會更精準且成本更低。
    2. 多階段處理，提升結果品質
    第一階段 FAISS 檢索：用語意索引找到相關段落。
    第二階段 Gemini 精煉：由 Gemini 模型從候選段落中再挑選真正重要的段落，避免帶入雜訊。
    分段、精煉後再結構化：最後讓 Gemini 模型在精簡上下文內生成結構化 JSON，準確性更高。
    3. 提升結構化與一致性
    透過明確的 Prompt 和多階段流程，模型更容易依規範產生符合格式的結果。
    避免把大量未經篩選的雜訊輸入模型，導致回應內容混亂或不完整。
    """
    main("uploads/example.pdf")

