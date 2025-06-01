from typing import Dict, Any
import json
import os
from dotenv import load_dotenv

import google.generativeai as genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv('GEMINI_KEY')

def configure_gemini():
    """Configure Gemini API with the API key."""
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

def json_to_markdown(json_data: Dict[Any, Any]) -> str:
    """
    Convert JSON data to Markdown format using Gemini.
    
    Args:
        json_data (Dict): The JSON data to be converted to markdown
        
    Returns:
        str: Markdown formatted text
    """
    try:
        # Convert JSON to string for prompt
        json_str = json.dumps(json_data, indent=2)
        
        # Configure Gemini
        model = configure_gemini()
        
        # Create prompt for Gemini
        prompt = f"""
        Please convert the following JSON data into a well-formatted Markdown document.
        Make it readable and properly structured with appropriate headers and sections.
        
        JSON Data:
        {json_str}

        # Note:
        1. Don't add words or explaination that isn't relevent to the JSON data.
        2. Don't give another translate version in the project summary.
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Return the markdown content
        return response.text
        
    except Exception as e:
        return f"Error converting JSON to Markdown: {str(e)}"

if __name__ == "__main__":
    test_json =  {
                "name": "系統分析與設計期末專案",
                "summary": "實際運用系統分析與設計概念，從無到有的系統開發過程，培養團隊協作、需求蒐集與系統實作的能力。設計出具有實用性及潛在商業價值的資訊系統解決方案。",
                "start_time": "2024-02-26",
                "end_time": "2024-06-09",
                "due_date": "2024-06-09",
                "estimated_loading": 100,
                "current_milestone": "Milestone 4",
                "milestones": [
                    {
                    "name": "Milestone 1：專案構想與初步分析",
                    "summary": "專案構想與初步分析，包含問題與機會、IT 對策、預期效益、初步分析、產品獨特賣點、功能矩陣、市場分析、同業最佳實務、第三方工具比較、可行性分析等。",
                    "start_time": "2024-03-04",
                    "end_time": "2024-03-17",
                    "estimated_loading": 15,
                    "tasks": [
                        {
                        "title": "市場調查與趨勢分析",
                        "description": "進行市場調查或趨勢分析，驗證專案可行性。",
                        "due_date": "2024-03-10",
                        "estimated_loading": 5,
                        "is_completed": False
                        },
                        {
                        "title": "撰寫專案構想書",
                        "description": "撰寫包含問題陳述、解決方案、預期效益等內容的專案構想書。",
                        "due_date": "2024-03-15",
                        "estimated_loading": 5,
                        "is_completed": False
                        },
                        {
                        "title": "製作簡報投影片",
                        "description": "製作簡潔明瞭的簡報投影片，呈現專案構想與初步分析結果。",
                        "due_date": "2024-03-17",
                        "estimated_loading": 5,
                        "is_completed": False
                        }
                    ]
                    },
                    {
                    "name": "Milestone 2：系統提案與使用者訪談",
                    "summary": "系統設計初步成形以及對使用者需求的驗證，包含修訂後的專案構想、Wireframe 或 UI Prototype、使用者訪談或測試紀錄。",
                    "start_time": "2024-04-08",
                    "end_time": "2024-04-21",
                    "estimated_loading": 30,
                    "tasks": [
                        {
                        "title": "根據Milestone 1 反饋修正專案構想",
                        "description": "根據Milestone 1 的回饋，修正專案構想和設計。",
                        "due_date": "2024-04-10",
                        "estimated_loading": 5,
                        "is_completed": False 
                        },
                        {
                        "title": "設計Wireframe 或 UI Prototype",
                        "description": "設計低保真或高保真原型，展現系統介面與流程設計。",
                        "due_date": "2024-04-15",
                        "estimated_loading": 10,
                        "is_completed": False
                        },
                        {
                        "title": "進行使用者訪談並撰寫報告",
                        "description": "進行使用者訪談，收集使用者需求並撰寫訪談報告。",
                        "due_date": "2024-04-20",
                        "estimated_loading": 15,
                        "is_completed": False
                        }
                    ]
                    },
                    {
                    "name": "Milestone 3：系統開發與測試",
                    "summary": "MVP 的開發完成度，根據反饋驗證是否符合使用者核心需求，包含已開發功能的影片或現場 Demo、Usability Testing 與 Test-Driven Development。",
                    "start_time": "2024-05-20",
                    "end_time": "2024-06-02",
                    "estimated_loading": 35,
                    "tasks": [
                        {
                        "title": "系統功能開發",
                        "description": "開發MVP的核心功能。",
                        "due_date": "2024-05-27",
                        "estimated_loading": 15,
                        "is_completed": False
                        },
                        {
                        "title": "進行Usability Testing",
                        "description": "進行可用性測試，收集使用者回饋。",
                        "due_date": "2024-05-31",
                        "estimated_loading": 10,
                        "is_completed": False
                        },
                        {
                        "title": "製作簡報與Demo影片",
                        "description": "製作簡報並錄製系統Demo影片。",
                        "due_date": "2024-06-02",
                        "estimated_loading": 10,
                        "is_completed": False
                        }
                    ]
                    },
                    {
                    "name": "Milestone 4：最終文件與程式碼提交",
                    "summary": "繳交完整文件與程式碼，包含User Stories Mapping、BPMN、Wireframes、測試報告、專案管理追蹤、API 文件、系統文件、EER圖等至少三種。",
                    "start_time": "2024-06-02",
                    "end_time": "2024-06-09",
                    "estimated_loading": 20,
                    "tasks": [
                        {
                        "title": "撰寫README.md文件",
                        "description": "撰寫README.md文件，整合所有文字交付成果、圖表等。",
                        "due_date": "2024-06-05",
                        "estimated_loading": 5,
                        "is_completed": False
                        },
                        {
                        "title": "完成程式碼與測試報告",
                        "description": "完成程式碼編寫，並撰寫測試報告。",
                        "due_date": "2024-06-07",
                        "estimated_loading": 10,
                        "is_completed": False
                        },
                        {
                        "title": "提交所有文件與程式碼",
                        "description": "將所有文件和程式碼提交至指定平台。",
                        "due_date": "2024-06-09",
                        "estimated_loading": 5,
                        "is_completed": False
                        }
                    ]
                    }
                ]
                }
    result = json_to_markdown(test_json)
    print(result)