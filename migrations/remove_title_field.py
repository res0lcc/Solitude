from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db

def upgrade():
    # 删除 title 字段
    db.engine.execute('ALTER TABLE diary DROP COLUMN title')

def downgrade():
    # 如果需要回滚，重新添加 title 字段
    db.engine.execute('ALTER TABLE diary ADD COLUMN title VARCHAR(100)')
