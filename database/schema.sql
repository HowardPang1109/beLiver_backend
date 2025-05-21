-- 使用者表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC'
);

-- 專案表（先不加 current_milestone_id）
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    summary TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    estimated_loading NUMERIC(3,1),  -- 預估時間（小時）
    due_date DATE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);

-- 里程碑表
CREATE TABLE milestones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    summary TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    estimated_loading NUMERIC(3,1),  -- 預估時間（小時）
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE
);

-- 回頭加上 current_milestone_id 欄位與外鍵
ALTER TABLE projects
ADD COLUMN current_milestone_id INTEGER,
ADD CONSTRAINT fk_current_milestone
    FOREIGN KEY (current_milestone_id) REFERENCES milestones(id) ON DELETE SET NULL;

-- 任務表
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,  -- 任務截止日期（原 ddl）
    estimated_loading NUMERIC(3,1),  -- 預估時間（小時）
    milestone_id INTEGER REFERENCES milestones(id) ON DELETE SET NULL,
    is_completed BOOLEAN DEFAULT FALSE
);

-- 檔案表
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE
);

-- AI 助理訊息表
CREATE TABLE chat_histories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    sender VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
