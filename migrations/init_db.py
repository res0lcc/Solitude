from flask import Flask
from models import db, User, Setting, SystemConfig
from werkzeug.security import generate_password_hash

def init_db():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:y20051010@localhost/diary_app'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 创建管理员账号
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                nickname='管理员',
                is_admin=True,
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            
            # 创建管理员设置
            admin_settings = Setting(
                user_id=admin.id,
                theme_settings=Setting.get_default_settings()
            )
            db.session.add(admin_settings)
        
        # 创建系统配置
        system_config = SystemConfig.query.first()
        if not system_config:
            system_config = SystemConfig(
                theme_color='#2196F3',
                font_family='975HazyGothic SC',
                stats_settings={
                    'show_users': True,
                    'show_diaries': True,
                    'card_style': 'default'
                }
            )
            db.session.add(system_config)
        
        db.session.commit()
        print('数据库初始化完成')

if __name__ == '__main__':
    init_db()
