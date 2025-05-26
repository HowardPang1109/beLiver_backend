# beLiver_backend

[DB 說明文件](https://docs.google.com/document/d/1MVfwYKya8sNw13MMvOnkbZTI1VISRFEDar-_8Z5tNM0/edit?usp=sharing)

## 🚀 專案啟動方式

### 1. 啟動本地伺服器

```bash
cd app
uvicorn main:app --reload
```

### 2. 伺服器啟動後，你可以在瀏覽器開啟：

```bash
http://localhost:8000/docs
```
這是自動產生的 Swagger API 文件介面，可直接測試 API。

## 🔐 使用者登入範例

### 1. 使用預設帳號登入：

```json
{
  "email": "alice@example.com",
  "password": "pass1234"
}
```

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "pass1234"
}'
```

### 2. 登入成功後，會回傳：

```json
{
  "user_id": "u1",
  "name": "Alice",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## ✅ 驗證方式（JWT）

之後每個 API 請求都要在 Header 加上：

```makefile
Authorization: Bearer <你的 token>
```

你可以在 `/docs` 點右上角 **Authorize**，貼上 token，Swagger 會自動加到每個請求中。

## 🧪 curl 範例指令

取得某個專案的對話紀錄（以 `proj01` 為例）：

```bash
curl -X GET "http://localhost:8000/assistant/history?projectId=proj01" \
  -H "Authorization: Bearer <你的 token>"
```

請將 `<你的 token>` 替換為你登入後取得的實際 JWT。

## 📁 上傳檔案範例

上傳多個檔案並關聯到 `proj01`：

```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer <你的 token>" \
  -F "files=@doc1.pdf" \
  -F "files=@spec.docx" \
  -F "projectId=proj01"
```

## 📦 環境變數（.env）範例

```env
DB_NAME=beliver_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your_jwt_secret
```