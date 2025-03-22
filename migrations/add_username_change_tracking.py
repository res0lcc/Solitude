from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db

def upgrade():
    # 在 user 表中添加新字段
    db.engine.execute('''
        ALTER TABLE user 
        ADD COLUMN last_username_change DATETIME NULL,
        ADD COLUMN days_until_username_change INT DEFAULT 0
    ''')

def downgrade():
    # 删除添加的字段
    db.engine.execute('''
        ALTER TABLE user 
        DROP COLUMN last_username_change,
        DROP COLUMN days_until_username_change
    ''')
