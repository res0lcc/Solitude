DROP DATABASE IF EXISTS diary_app;
CREATE DATABASE diary_app DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE diary_app;

-- 用户表
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(512) NOT NULL,
    nickname VARCHAR(80),
    avatar VARCHAR(255) DEFAULT NULL,  -- 改为默认NULL
    is_admin BOOLEAN DEFAULT FALSE,
    username_changed_at DATETIME DEFAULT NULL,
    theme_settings JSON DEFAULT (JSON_OBJECT(
        'primary_color', '#2196F3',
        'accent_color', '#448AFF',
        'card_radius', 8,
        'card_opacity', 100,
        'nav_opacity', 100,  -- 新增
        'drawer_opacity', 100  -- 新增
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 设置表
CREATE TABLE settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    theme_settings JSON DEFAULT (JSON_OBJECT(
        'primary_color', '#2196F3',
        'accent_color', '#448AFF',
        'card_radius', 8,
        'card_opacity', 100,
        'nav_opacity', 100,  -- 新增
        'drawer_opacity', 100,  -- 新增
        'font_family', '975HazyGothic SC'
    )),
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 日记表
CREATE TABLE diary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME DEFAULT NULL,
    weather VARCHAR(20),
    mood VARCHAR(20),
    location VARCHAR(100),
    likes_count INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- 点赞表
CREATE TABLE likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    diary_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (diary_id) REFERENCES diary(id) ON DELETE CASCADE
);

-- 系统配置表
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    theme_color VARCHAR(20) DEFAULT '#333333',
    font_family VARCHAR(50) DEFAULT '975HazyGothic SC',
    custom_css TEXT,
    stats_settings JSON DEFAULT (JSON_OBJECT(
        'show_users', TRUE,
        'show_diaries', TRUE,
        'card_style', 'default'
    )),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    icp VARCHAR(50),
    copyright VARCHAR(200)
);
