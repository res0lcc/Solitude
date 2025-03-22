USE diary_app;

-- 检查字段是否存在
SET @exist := (SELECT COUNT(*) 
               FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_SCHEMA='diary_app' 
               AND TABLE_NAME='user' 
               AND COLUMN_NAME='username_changed_at');

-- 如果字段不存在则添加
SET @query := IF(@exist=0,
    'ALTER TABLE user ADD COLUMN username_changed_at DATETIME DEFAULT NULL',
    'SELECT "Column already exists"');

PREPARE stmt FROM @query;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
