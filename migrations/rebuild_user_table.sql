USE diary_app;

-- 临时禁用外键检查
SET FOREIGN_KEY_CHECKS = 0;

-- 备份现有数据
CREATE TEMPORARY TABLE IF NOT EXISTS user_backup AS 
SELECT id, username, password, nickname, avatar, is_admin 
FROM user;

-- 修改用户表
ALTER TABLE user
ADD COLUMN username_changed_at DATETIME DEFAULT NULL;

-- 恢复数据
UPDATE user u
INNER JOIN user_backup ub ON u.id = ub.id
SET u.username = ub.username,
    u.password = ub.password,
    u.nickname = ub.nickname,
    u.avatar = ub.avatar,
    u.is_admin = ub.is_admin;

-- 删除临时表
DROP TEMPORARY TABLE IF EXISTS user_backup;

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;
