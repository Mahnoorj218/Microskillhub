-- ============================================================================
-- LEGACY: MySQL schema (deprecated)
-- Use Supabase instead: ../supabase/migrations/001_initial.sql
-- Setup guide: ../SUPABASE_SETUP.md
-- ============================================================================
-- Database: microskillhub
-- Target: MySQL / phpMyAdmin Import
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `microskillhub` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `microskillhub`;

-- ----------------------------------------------------------------------------
-- Table 1: users
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('student', 'admin') NOT NULL,
    `roll_number` VARCHAR(30) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `unique_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 2: skills
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `skills` (
    `skill_id` INT AUTO_INCREMENT,
    `skill_name` VARCHAR(80) NOT NULL,
    `category` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`skill_id`),
    UNIQUE KEY `unique_skill_name` (`skill_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 3: user_skills
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_skills` (
    `user_skill_id` INT AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    `proficiency_level` ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL,
    `proficiency_percent` INT NOT NULL,
    `added_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_skill_id`),
    CONSTRAINT `fk_user_skills_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_user_skills_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`skill_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 4: tasks
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `tasks` (
    `task_id` INT AUTO_INCREMENT,
    `title` VARCHAR(150) NOT NULL,
    `description` TEXT NOT NULL,
    `difficulty` ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL,
    `reward_xp` INT NOT NULL,
    `status` ENUM('active', 'closed') DEFAULT 'active',
    `created_by` INT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`task_id`),
    CONSTRAINT `fk_tasks_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 5: task_required_skills
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `task_required_skills` (
    `id` INT AUTO_INCREMENT,
    `task_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    `required_level` ENUM('Beginner', 'Intermediate', 'Advanced') NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_req_skills_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_req_skills_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`skill_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 6: applications
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `applications` (
    `app_id` INT AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `task_id` INT NOT NULL,
    `status` ENUM('pending', 'completed', 'rejected') DEFAULT 'pending',
    `submission_text` TEXT DEFAULT NULL,
    `applied_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `reviewed_at` DATETIME DEFAULT NULL,
    PRIMARY KEY (`app_id`),
    CONSTRAINT `fk_applications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_applications_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 7: experience (xp)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `experience` (
    `xp_id` INT AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `app_id` INT NOT NULL,
    `xp_earned` INT NOT NULL,
    `awarded_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`xp_id`),
    CONSTRAINT `fk_experience_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_experience_app` FOREIGN KEY (`app_id`) REFERENCES `applications` (`app_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- DATA INSERTION
-- ============================================================================

-- 1. Insert 1 Admin User
-- Note: '$2y$10$e0MYzXy6K4Y... (truncated)' is a standard bcrypt hash of 'admin123'
INSERT INTO `users` (`full_name`, `email`, `password_hash`, `role`, `roll_number`) 
VALUES (
    'System Administrator', 
    'admin@microskillhub.com', 
    '$2y$10$M9m3nfe.Uv7D2G1G7FpPHePjbeunvQ8S6Z5.t5x8/S9Z98a96hZre', 
    'admin', 
    'ADMIN-001'
);

-- 2. Insert 5 Required Skills
INSERT INTO `skills` (`skill_name`, `category`) VALUES
('HTML', 'Frontend'),
('CSS', 'Frontend'),
('JavaScript', 'Frontend'),
('PHP', 'Backend'),
('MySQL', 'Database');

-- 3. Insert 2 Active Tasks (Created by Admin ID: 1)
INSERT INTO `tasks` (`title`, `description`, `difficulty`, `reward_xp`, `status`, `created_by`) VALUES
(
    'Build a Responsive Navbar', 
    'Create a fully responsive website navigation header using modern CSS layouts (Flexbox/Grid) that cleanly collapses into a burger menu on mobile screens.', 
    'Intermediate', 
    150, 
    'active', 
    1
),
(
    'User Registration Backend Script', 
    'Write a PHP backend script that processes a registration form, validates email formats, hashes user passwords safely, and saves records into a MySQL database.', 
    'Advanced', 
    300, 
    'active', 
    1
);

-- 4. Insert Required Skills for the Tasks
-- Task 1 (Navbar) requires HTML (Intermediate) and CSS (Intermediate)
INSERT INTO `task_required_skills` (`task_id`, `skill_id`, `required_level`) VALUES
(1, 1, 'Intermediate'), -- Task 1 requires HTML
(1, 2, 'Intermediate'); -- Task 1 requires CSS


-- Task 2 (Registration Backend) requires PHP (Advanced) and MySQL (Intermediate)
INSERT INTO `task_required_skills` (`task_id`, `skill_id`, `required_level`) VALUES
(2, 4, 'Advanced'),
(2, 5, 'Intermediate');

SHOW TABLES;