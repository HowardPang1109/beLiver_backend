CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- 使用者表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL
);

-- 專案表（使用 current_milestone 為文字欄位）
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    summary TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    estimated_loading NUMERIC(5,1),
    due_date DATE,
    current_milestone VARCHAR(255),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE
);

-- 里程碑表
CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    summary TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    estimated_loading NUMERIC(3,1),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE
);

-- 任務表
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    estimated_loading NUMERIC(3,1),
    milestone_id UUID REFERENCES milestones(id) ON DELETE SET NULL,
    is_completed BOOLEAN DEFAULT FALSE
);

-- 檔案表
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE
);

-- AI 助理訊息表
CREATE TABLE chat_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    sender VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);