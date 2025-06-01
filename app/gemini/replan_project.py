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
1. 根據使用者 chat 討論內容調整 milestone 與 task 數量、描述與工時。
2. 每個 milestone 至少要拆解出 3 個具體任務。
3. 所有 estimated_loading 為合理整數。
4. 任務的 due_date 請合理分配在 milestone 結束日前。
5. 僅輸出 JSON 結果（不要包含說明文字）。

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