# 使用官方 Python 基底映像
FROM python:3.13-alpine

# 複製專案檔案
COPY . .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 開放 port
EXPOSE 8080

# 啟動 FastAPI（用 Uvicorn）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
