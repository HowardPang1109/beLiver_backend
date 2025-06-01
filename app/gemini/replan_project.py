import google.generativeai as genai
import json
from datetime import datetime
from app.gemini.json_to_markdown import json_to_markdown

def replan_project_with_gemini(original_json: dict, chat_history: list[dict]) -> dict:
    cleaned_json = {
        "projects": original_json.get("projects", [])
    }
    
    chat_text = "\n".join([
        f"{item['sender'].upper()}: {item['message']}" for item in chat_history
    ])

    prompt = f"""
你是一個專案助理，根據下方原始專案規劃 JSON 與使用者的完整回饋紀錄，請重新產出專案規劃。

## 格式：
請產出符合以下 JSON 結構的內容（保持欄位名稱與結構）：
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

## 調整規則：
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

## 原始專案內容：
{json.dumps(cleaned_json, ensure_ascii=False, indent=2)}

## 使用者對話紀錄：
{chat_text}

## 請直接輸出符合格式的 JSON 結果，不需額外說明或註解。
"""

    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=genai.types.GenerationConfig(temperature=0.2,top_p=0.9))
    
    try:
        response = model.generate_content(prompt)
        if not response.text or not response.text.strip():
            print("⚠️ Gemini 回傳空內容")
            print("🧪 Prompt Preview:\n", prompt[:1000])
            raise ValueError("Gemini 回傳空內容，請檢查 prompt 是否太長或格式有誤。")
        
        raw = response.text.strip().replace("```json", "").replace("```", "")
        updated_json = json.loads(raw)

        return updated_json

    except Exception as e:
        print("🔥 Gemini raw response:")
        print(response.text if response else "（None）")
        raise e