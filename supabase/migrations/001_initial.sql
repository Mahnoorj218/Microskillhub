-- MicroSkillHub — Supabase (PostgreSQL) schema
-- Run in: Supabase Dashboard → SQL Editor → New query → Run

-- ---------------------------------------------------------------------------
-- Extensions & enums
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE user_role AS ENUM ('student', 'admin');
CREATE TYPE proficiency_level AS ENUM ('Beginner', 'Intermediate', 'Advanced');
CREATE TYPE task_difficulty AS ENUM ('Beginner', 'Intermediate', 'Advanced');
CREATE TYPE task_status AS ENUM ('active', 'closed');
CREATE TYPE application_status AS ENUM ('pending', 'completed', 'rejected');

-- ---------------------------------------------------------------------------
-- Profiles (linked to Supabase Auth)
-- ---------------------------------------------------------------------------
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role user_role NOT NULL,
    roll_number TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- App tables
-- ---------------------------------------------------------------------------
CREATE TABLE skills (
    skill_id SERIAL PRIMARY KEY,
    skill_name VARCHAR(80) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL
);

CREATE TABLE user_skills (
    user_skill_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    skill_id INT NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    proficiency_level proficiency_level NOT NULL,
    proficiency_percent INT NOT NULL CHECK (proficiency_percent BETWEEN 0 AND 100),
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, skill_id)
);

CREATE TABLE tasks (
    task_id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    difficulty task_difficulty NOT NULL,
    reward_xp INT NOT NULL CHECK (reward_xp > 0),
    status task_status NOT NULL DEFAULT 'active',
    created_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE task_required_skills (
    id SERIAL PRIMARY KEY,
    task_id INT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    skill_id INT NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    required_level proficiency_level NOT NULL
);

CREATE TABLE applications (
    app_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    task_id INT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    status application_status NOT NULL DEFAULT 'pending',
    submission_text TEXT,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    UNIQUE (user_id, task_id)
);

CREATE TABLE experience (
    xp_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    app_id INT NOT NULL REFERENCES applications(app_id) ON DELETE CASCADE,
    xp_earned INT NOT NULL,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Leaderboard helper
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_global_leaderboard()
RETURNS TABLE(name TEXT, role user_role, xp BIGINT)
LANGUAGE sql
STABLE
AS $$
    SELECT
        p.full_name,
        p.role,
        COALESCE(SUM(e.xp_earned), 0)::BIGINT
    FROM profiles p
    LEFT JOIN experience e ON e.user_id = p.id
    WHERE p.role = 'student'
    GROUP BY p.id, p.full_name, p.role
    ORDER BY 3 DESC
    LIMIT 10;
$$;

-- ---------------------------------------------------------------------------
-- Row Level Security (for direct client access; service role bypasses RLS)
-- ---------------------------------------------------------------------------
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE experience ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users manage own skills"
    ON user_skills FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Students manage own applications"
    ON applications FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "Users read own xp"
    ON experience FOR SELECT
    USING (auth.uid() = user_id);

-- Public read for catalog tables
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_required_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read skills" ON skills FOR SELECT USING (true);
CREATE POLICY "Authenticated read active tasks" ON tasks FOR SELECT USING (status = 'active');
CREATE POLICY "Anyone read task requirements" ON task_required_skills FOR SELECT USING (true);

-- ---------------------------------------------------------------------------
-- Seed: master skills
-- ---------------------------------------------------------------------------
INSERT INTO skills (skill_name, category) VALUES
    ('HTML', 'Frontend'),
    ('CSS', 'Frontend'),
    ('JavaScript', 'Frontend'),
    ('PHP', 'Backend'),
    ('MySQL', 'Database')
ON CONFLICT (skill_name) DO NOTHING;
