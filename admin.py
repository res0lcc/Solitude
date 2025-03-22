from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # 检查是否已存在管理员账号
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("管理员账号已存在，正在更新密码...")
            admin.password = generate_password_hash('admin')
        else:
            print("正在创建管理员账号...")
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                nickname='管理员',
                is_admin=True
            )
            db.session.add(admin)
        
        try:
            db.session.commit()
            print("管理员账号创建/更新成功！")
            print("用户名: admin")
            print("密码: admin")
        except Exception as e:
            db.session.rollback()
            print(f"错误: {str(e)}")

if __name__ == '__main__':
    create_admin_user()
