"""
This module provides functionality to reschedule project tasks using Gemini AI.
It takes the current project state and a new task, then generates an updated project schedule.
"""

import json
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
import os
from app.core.db import get_db
from app.models import Milestone as MilestoneModel, Task as TaskModel
from contextlib import contextmanager
from app.schemas.project import ProjectSchema, TaskSchema
from datetime import datetime

@contextmanager
def get_db_session():
    """Database session context manager"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

# Initialize the model
text_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=genai.types.GenerationConfig(temperature=0.2)
)

def default_serializer(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
# def separate_completed_tasks(project_data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
#     """
#     Separate completed and incomplete tasks from the project data.
    
#     Args:
#         project_data: A single project's data
        
#     Returns:
#         Tuple of (completed_data, incomplete_data) where:
#         - completed_data: Contains only completed tasks in the project
#         - incomplete_data: Contains only incomplete tasks in the project
#     """
#     completed_part_of_project = []
#     completed_part_of_project['name'] = project_data['name']
#     completed_part_of_project['summary'] = project_data.get('summary', '')
#     completed_part_of_project['start_time'] = project_data.get('start_time', '')
#     completed_part_of_project['end_time'] = project_data.get('end_time', '')
#     completed_part_of_project['due_date'] = project_data.get('due_date', '')
#     completed_part_of_project['estimated_loading'] = project_data.get('estimated_loading', 0)
#     completed_part_of_project['current_milestone'] = project_data.get('current_milestone', 'null')
#     incomplete_tasks = []
#     # Process each milestone in the project
#     for milestone in project_data.get('milestones', []):
#         completed_tasks = []
        
#         # Separate tasks into completed and incomplete
#         for task in milestone.get('tasks', []):
#             if task.get('is_completed', False):  # Default to False to be more strict
#                 incomplete_tasks.append(task)
#             else:
#                 completed_tasks.append(task)

#         if len(completed_tasks) == len(milestone.get('tasks', [])):
#             completed_part_of_project['milestones'].append(milestone)
#         elif completed_tasks:
#             completed_milestone = {
#                 'name': milestone['name'],
#                 'summary': milestone.get('summary', ''),
#                 'start_time': milestone.get('start_time', ''),
#                 'end_time': milestone.get('end_time', ''),
#                 'estimated_loading': sum(t.get('estimated_loading', 0) for t in completed_tasks),
#                 'tasks': completed_tasks
#             }
#             completed_part_of_project['milestones'].append(completed_milestone)
    
#     return completed_part_of_project, incomplete_tasks

def reschedule_project(project: Dict[str, Any], new_task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reschedule project tasks including a new task using Gemini AI.
    
    Args:
        completed_part_of_project: Completed part of the project data
        incomplete_tasks: Incomplete tasks to be rescheduled
        new_task: New task to be added to the project

    Returns:
        Dict containing the rescheduled project data
    """
    # Step 2: Prepare the prompt for rescheduling incomplete tasks with the new task
    prompt = """
你是一位專業的文件理解助手。你的任務是將一個新的任務插入到專案中。請將新任務依照到期日、預期所需時間插入到new_task裡面的milestone_id的milestone中，並將後面的任務依照新插入的任務調整需要完成的日期。

這些是已經完成的專案:
{project}

這是新的任務:
{new_task}

請遵守以下規則:
1. 所有日期與時間欄位（start_time, end_time, due_date）均需填寫，不得為 null。
2. 所有 estimated_loading 請給出合理整數估算（例如 5, 10, 20），不得為 null，也不能為0!!!
3. 每個 Milestone 至少拆解出 3 項具體任務（tasks）。
4. 任務命名與內容應根據里程碑摘要合理拆解，避免過於模糊或重複。
5. 每個任務的 due_date 請根據邏輯先後順序與工時推論，合理分配至 milestone 結束日前。
6. Milestone 的 estimated_loading 不可比底下所有任務的 estimated_loading 總和多超過 10 小時。
7. estimated_loading 工時估算請依任務類型給予合理範圍，具體如下：
   - 文書處理類任務（如報告撰寫、資料彙整、會議記錄等）通常介於 5～10 小時
   - 程式開發類任務（如撰寫 API、資料庫設計、前端實作等）通常介於 20～60 小時
8. 請依照project的格式回傳，不要做任何格式的修改。
9. 請不要對任何已經完成的任務做修改，而新任務的到期日也應該在該milestone所有已經完成的任務的到期日後。
10. 請僅回傳符合格式的純 JSON 結果，不需額外說明或註解。

以下是回傳的標準格式，依照格式再將 project 的內容填入：
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
              "is_completed": "..."
            }}
          ]
        }}
      ]
    }}
  ]
}}

Return only the updated JSON without any additional text or explanation.
""".format(
    project=json.dumps(project, indent=2, ensure_ascii=False, default=default_serializer),
    new_task=json.dumps(new_task.dict(), indent=2, ensure_ascii=False, default=default_serializer)
)
    
    try:
        # Get response from Gemini
        response = text_model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        if '```json' in response_text:
            # Remove markdown code block if present
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        
        # Parse the rescheduled incomplete tasks
        rescheduled_data = json.loads(response_text)
        
        return rescheduled_data
    
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini response: {e}")
        print(f"Response was: {response_text}")
        raise ValueError("Failed to parse rescheduled project data")
    except Exception as e:
        print(f"Error in reschedule_project: {e}")
        raise

def update_project_task(project: Dict[str, Any], updated_task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reschedule project tasks including a new task using Gemini AI.
    
    Args:
        completed_part_of_project: Completed part of the project data
        incomplete_tasks: Incomplete tasks to be rescheduled
        new_task: New task to be added to the project

    Returns:
        Dict containing the rescheduled project data
    """
    # Step 2: Prepare the prompt for rescheduling incomplete tasks with the new task
    prompt = """
你是一位專業的文件理解助手。你的任務是因應一個已經在專案但是有更新的任務調整整體專案規劃。請將更新的任務依照到期日、預期所需時間重新放入同一個milestone中，並將後面的任務依照調整位置的任務調整需要完成的日期。

這些是已經完成的專案:
{project}

這是有更新的任務:
{updated_task}

請遵守以下規則:
1. 所有日期與時間欄位（start_time, end_time, due_date）均需填寫，不得為 null。
2. 所有 estimated_loading 請給出合理整數估算（例如 5, 10, 20），不得為 null。
3. 每個 Milestone 至少拆解出 3 項具體任務（tasks）。
4. 任務命名與內容應根據里程碑摘要合理拆解，避免過於模糊或重複。
5. 每個任務的 due_date 請根據邏輯先後順序與工時推論，合理分配至 milestone 結束日前。
6. Milestone 的 estimated_loading 不可比底下所有任務的 estimated_loading 總和多超過 10 小時。
7. estimated_loading 工時估算請依任務類型給予合理範圍，具體如下：
   - 文書處理類任務（如報告撰寫、資料彙整、會議記錄等）通常介於 5～10 小時
   - 程式開發類任務（如撰寫 API、資料庫設計、前端實作等）通常介於 20～60 小時
8. 請依照project的格式回傳，不要做任何格式的修改。
9. 請不要對任何已經完成的任務做修改。
10. 請僅回傳符合格式的純 JSON 結果，不需額外說明或註解。

以下是回傳的標準格式，依照格式再將 project 的內容填入：
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
              "is_completed": "..."
            }}
          ]
        }}
      ]
    }}
  ]
}}

Return only the updated JSON without any additional text or explanation.
""".format(
    project=json.dumps(project, indent=2, ensure_ascii=False, default=default_serializer),
    updated_task=json.dumps({
        "id": str(updated_task.id),
        "title": updated_task.title,
        "description": updated_task.description or "",
        "due_date": updated_task.due_date.isoformat() if updated_task.due_date else "",
        "estimated_loading": float(updated_task.estimated_loading) if updated_task.estimated_loading else 0.0,
        "is_completed": updated_task.is_completed or False,
        "milestone_id": str(updated_task.milestone_id)
    }, indent=2, ensure_ascii=False, default=default_serializer)
)
    
    try:
        # Get response from Gemini
        response = text_model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        if '```json' in response_text:
            # Remove markdown code block if present
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        
        # Parse the rescheduled incomplete tasks
        rescheduled_data = json.loads(response_text)
        
        return rescheduled_data
    
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini response: {e}")
        print(f"Response was: {response_text}")
        raise ValueError("Failed to parse rescheduled project data")
    except Exception as e:
        print(f"Error in reschedule_project: {e}")
        raise