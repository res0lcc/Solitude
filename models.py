from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    nickname = db.Column(db.String(80), nullable=True)  # 保持与数据库一致
    avatar = db.Column(db.String(255), nullable=True, default=None)  # 确保默认值为 None
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # 修改默认值为False
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))  # 添加创建时间字段
    username_changed_at = db.Column(db.DateTime, nullable=True, default=None)
    theme_settings = db.Column(db.JSON, default=lambda: {
        'primary_color': '#2196F3',
        'accent_color': '#448AFF',
        'card_radius': 8,
        'card_opacity': 100
    })
    settings = db.relationship('Setting', backref='owner', uselist=False)
    last_username_change = db.Column(db.DateTime, nullable=True)
    days_until_username_change = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def can_change_username(self):
        if not self.last_username_change:
            return True
        days_since_change = (datetime.now() - self.last_username_change).days
        return days_since_change >= 30

    @property
    def days_until_next_change(self):
        if not self.last_username_change:
            return 0
        days_since_change = (datetime.now() - self.last_username_change).days
        if days_since_change >= 30:
            return 0
        return 30 - days_since_change

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    theme_settings = db.Column(db.JSON, default=lambda: {
        'primary_color': '#2196F3',
        'accent_color': '#448AFF',
        'card_radius': 8,
        'card_opacity': 100,
        'nav_opacity': 100,
        'drawer_opacity': 100,
        'font_family': '975HazyGothic SC'
    })

    @staticmethod
    def get_default_settings():
        return {
            'primary_color': '#2196F3',
            'accent_color': '#448AFF',
            'card_radius': 8,  # 改为整数
            'card_opacity': 100,  # 改为整数
            'nav_opacity': 100,
            'drawer_opacity': 100,
            'font_family': '975HazyGothic SC'
        }

    def update_theme_settings(self, new_settings):
        # 确保数值类型正确
        if 'card_radius' in new_settings:
            new_settings['card_radius'] = int(new_settings['card_radius'])
        if 'card_opacity' in new_settings:
            new_settings['card_opacity'] = int(new_settings['card_opacity'])
        self.theme_settings.update(new_settings)

class Diary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 删除 title 字段
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_public = db.Column(db.Boolean, default=False)
    weather = db.Column(db.String(20))
    mood = db.Column(db.String(20))  # 添加心情字段
    location = db.Column(db.String(100))  # 添加位置字段
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref=db.backref('diaries', lazy=True))  # 添加关系

# 删除 Like 模型
# class Like(db.Model):
#     整个类删除

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theme_color = db.Column(db.String(20), default="#333333")
    font_family = db.Column(db.String(50), default="975HazyGothic SC")
    custom_css = db.Column(db.Text)
    stats_settings = db.Column(db.JSON, default={
        'show_users': True,
        'show_diaries': True,
        'card_style': 'default'
    })
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    icp = db.Column(db.String(50))
    copyright = db.Column(db.String(200))
