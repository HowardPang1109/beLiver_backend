import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
genai.configure(api_key=GEMINI_KEY)

text_model = genai.GenerativeModel(model_name="gemini-1.5-flash") # 使用文字模型即可

doc = fitz.open("example.pdf")
all_text = ""

# 逐頁提取純文字
for i in range(len(doc)):
    page = doc.load_page(i)
    all_text += page.get_text() # 提取頁面所有文字

# 合併所有文字後，一次性傳給模型
prompt = f"請幫我閱讀以下 PDF 的內容並以繁體中文摘要重點：\n{all_text}"

# 注意：gemini-1.5-flash 有非常大的上下文窗口，適合處理大量文字
response = text_model.generate_content(prompt)

print("\n=== 最終綜合摘要 ===")
print(response.text)