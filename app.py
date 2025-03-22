import os
from flask import Flask, render_template, redirect, url_for, jsonify, request, session, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import desc, func
from datetime import datetime
from sqlalchemy import text
from models import User, Diary, SystemConfig, Setting, db
from werkzeug.utils import secure_filename
import random
import string
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate
import time  # 添加 time 模块导入

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'mysql://root:y20051010@localhost/diary_app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
        
        try:
            db.create_all()
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    nickname='管理员',
                    is_admin=True,
                    last_username_change=None,
                    days_until_username_change=0
                )
                admin.set_password('admin123')
                db.session.add(admin)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error in database initialization: {e}")
            raise
        finally:
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
            db.session.commit()

db_initialized = False

@app.before_request
def initialize_db():
    global db_initialized
    if not db_initialized:
        init_db()
        db_initialized = True

@app.before_request
def initialize_user_settings():
    if current_user.is_authenticated and not current_user.settings:
        setting = Setting(
            user_id=current_user.id,
            theme_settings=Setting.get_default_settings()
        )
        db.session.add(setting)
        db.session.commit()

@app.route('/')
def index():
    if not current_user.is_authenticated:
        settings = SystemConfig.query.first()
        stats_settings = settings.stats_settings if settings and settings.stats_settings else {
            'show_users': True,
            'show_diaries': True,
            'card_style': 'default'
        }
        return render_template('index.html',
            user_count=User.query.count() if stats_settings.get('show_users', True) else None,
            diary_count=Diary.query.count() if stats_settings.get('show_diaries', True) else None,
            card_style=stats_settings.get('card_style', 'default'),
            site_info={
                'icp': settings.icp if settings else None,
                'copyright': settings.copyright if settings else None
            }
        )
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        if 'user_id' not in session:
            return render_template('index.html')
        user_id = session['user_id']
        pagination = Diary.query.filter_by(user_id=user_id)\
            .order_by(desc(Diary.created_at))\
            .paginate(page=page, per_page=per_page)
        return render_template('index.html',
            diary_list=pagination.items,
            page=page,
            has_next=pagination.has_next
        )
    else:
        user_count = User.query.count()
        diary_count = Diary.query.count()
        return render_template('index.html',
            user_count=user_count,
            diary_count=diary_count
        )

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            login_user(user)
            session['user_id'] = user.id
            if not user.settings:
                setting = Setting(
                    user_id=user.id,
                    theme_settings=Setting.get_default_settings()
                )
                db.session.add(setting)
                db.session.commit()
            session['theme_settings'] = user.settings.theme_settings
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '用户名或密码错误'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/wall')
def wall():
    page = request.args.get('page', 1, type=int)
    per_page = 3  # 修改为每页显示3条
    pagination = Diary.query.filter_by(is_public=True)\
        .order_by(desc(Diary.created_at))\
        .paginate(page=page, per_page=per_page)
    
    return render_template('wall.html',
        diary_list=pagination.items,
        page=page,
        total_pages=pagination.pages,  # 添加总页数
        has_next=pagination.has_next,
        has_prev=pagination.has_prev,  # 添加是否有上一页
        empty_icon="public",
        empty_message="暂时还没有人写日记呢"
    )

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_diary():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # 移除 title 字段
            new_diary = Diary(
                user_id=current_user.id,
                content=data.get('content'),
                mood=data.get('mood', '开心'),
                location=data.get('location', ''),
                created_at=datetime.strptime(data.get('date') or datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d'),
                is_public=data.get('is_public', False)
            )

            db.session.add(new_diary)
            db.session.commit()

            return jsonify({
                'success': True,
                'diary_id': new_diary.id,
                'message': '日记发布成功！'
            })

        except Exception as e:
            print("错误:", str(e))
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('add.html', today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/edit/<int:diary_id>', methods=['GET', 'POST'])
@login_required
def edit_diary(diary_id):
    diary = Diary.query.get_or_404(diary_id)
    if diary.user_id != current_user.id:
        return redirect(url_for('wall'))
    if request.method == 'POST':
        try:
            data = request.get_json()
            date_str = data.get('date')
            if date_str:
                diary.created_at = datetime.strptime(date_str, '%Y-%m-%d')
            # 移除 title 设置
            diary.content = data.get('content')
            diary.mood = data.get('mood')
            diary.location = data.get('location')
            diary.is_public = data.get('is_public', diary.is_public)
            db.session.commit()
            return jsonify({
                'success': True,
                'diary_id': diary.id
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    return render_template('edit.html', diary=diary)

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            nickname = request.form.get('nickname', '').strip()

            # 格式验证
            if not username or not password or not nickname:
                return jsonify({'success': False, 'message': '所有字段都是必填的'})

            if len(username) < 5 or len(username) > 12:
                return jsonify({'success': False, 'message': '用户名长度必须在5-12位之间'})
            
            if not username.isalnum():
                return jsonify({'success': False, 'message': '用户名只能包含字母和数字'})

            # 检查用户名是否存在
            if User.query.filter_by(username=username).first():
                return jsonify({'success': False, 'message': '用户名已被使用'})

            # 创建新用户
            new_user = User(
                username=username,
                nickname=nickname,
                last_username_change=None,
                days_until_username_change=0
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()

            # 初始化用户设置
            user_settings = Setting(
                user_id=new_user.id,
                theme_settings=Setting.get_default_settings()
            )
            db.session.add(user_settings)
            db.session.commit()

            return jsonify({'success': True, 'message': '注册成功'})

        except Exception as e:
            db.session.rollback()
            print(f"注册错误: {str(e)}")
            return jsonify({'success': False, 'message': '注册失败，请稍后重试'})

    return render_template('create_user.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/check_login')
def api_check_login():
    return jsonify(isLoggedIn=current_user.is_authenticated, userId=current_user.id if current_user.is_authenticated else None)

@app.route('/api/diaries')
def api_diaries():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify([])
        diaries = Diary.query.filter_by(user_id=user_id).order_by(Diary.created_at.desc()).all()
        diaries_list = [{
            "title": diary.title,
            "content": diary.content,
            "created_at": diary.created_at.isoformat()
        } for diary in diaries]
        return jsonify(diaries_list)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/api/diary/<int:diary_id>/toggle_public', methods=['POST'])
def toggle_public(diary_id):
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    diary = Diary.query.get_or_404(diary_id)
    if diary.user_id != session['user_id']:
        return jsonify({'error': '无权限'}), 403
    diary.is_public = not diary.is_public
    db.session.commit()
    return jsonify({'success': True, 'is_public': diary.is_public})

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('profile'))
    return render_template('admin/dashboard.html')

@app.route('/api/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
        } for user in users]
    })

@app.route('/api/admin/diaries')
@login_required
def admin_diaries():
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    diaries = Diary.query.all()
    return jsonify({
        'diaries': [{
            'id': diary.id,
            'title': diary.title,
            'author': diary.author.nickname or diary.author.username,
            'created_at': diary.created_at.isoformat(),
            'is_public': diary.is_public
        } for diary in diaries]
    })

@app.route('/api/admin/settings', methods=['POST'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    config = SystemConfig.query.first()
    if not config:
        config = SystemConfig()
        db.session.add(config)
    config.theme_color = request.form.get('theme_color', '#333333')
    config.font_family = request.form.get('font_family', '975HazyGothic SC')
    config.custom_css = request.form.get('custom_css', '')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    if user_id == current_user.id:
        return jsonify({'error': '不能删除自己的账号'}), 400
    try:
        user = User.query.get_or_404(user_id)
        if user.is_admin:
            return jsonify({'error': '不能删除其他管理员账号'}), 400
            
        # 删除用户的所有日记
        Diary.query.filter_by(user_id=user_id).delete()
        
        # 删除用户的设置
        Setting.query.filter_by(user_id=user_id).delete()
        
        # 最后删除用户
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@app.route('/api/admin/diary/<int:diary_id>', methods=['DELETE'])
@login_required
def admin_delete_diary(diary_id):
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    diary = Diary.query.get_or_404(diary_id)
    db.session.delete(diary)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/diary/<int:diary_id>', methods=['DELETE'])
@login_required
def delete_diary(diary_id):
    try:
        diary = Diary.query.get_or_404(diary_id)
        if diary.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'error': '无权限删除'}), 403
            
        # 删除日记
        db.session.delete(diary)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/diary/<int:diary_id>/restore', methods=['POST'])
@login_required
def restore_diary(diary_id):
    diary = Diary.query.get_or_404(diary_id)
    if diary.user_id != current_user.id:
        return jsonify({'error': '无权限'}), 403
    diary.is_deleted = False
    diary.deleted_at = None
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/diary/<int:diary_id>/delete', methods=['DELETE'])
@login_required
def soft_delete_diary(diary_id):
    diary = Diary.query.get_or_404(diary_id)
    if diary.user_id != current_user.id:
        return jsonify({'error': '无权限'}), 403
    diary.is_deleted = True
    diary.deleted_at = datetime.now()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/diary/<int:diary_id>/delete-permanent', methods=['DELETE'])
@login_required
def permanent_delete_diary(diary_id):
    diary = Diary.query.get_or_404(diary_id)
    if diary.user_id != current_user.id:
        return jsonify({'error': '无权限'}), 403
    db.session.delete(diary)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/mydiary')
@login_required
def mydiary():
    page = request.args.get('page', 1, type=int)
    per_page = 3  # 修改为每页显示3条
    pagination = Diary.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Diary.created_at))\
        .paginate(page=page, per_page=per_page)
    
    return render_template('mydiary.html',
        diary_list=pagination.items,
        page=page,
        total_pages=pagination.pages,  # 添加总页数
        has_next=pagination.has_next,
        has_prev=pagination.has_prev,  # 添加是否有上一页
        empty_title="没有日记",
        empty_subtitle="写下第一篇吧",
        empty_icon="edit",
        empty_text="您还没有写过日记哦",
        empty_button_text="开始写第一篇日记"
    )

@app.route('/trash')
@login_required
def trash():
    deleted_diaries = Diary.query.filter_by(
        user_id=current_user.id,
        is_deleted=True
    ).order_by(desc(Diary.created_at)).all()
    return render_template('trash.html', diaries=deleted_diaries)

@app.route('/api/export/diary', methods=['POST'])
@login_required
def export_diary():
    try:
        data = request.get_json()
        format_type = request.args.get('format', 'json')
        diary_ids = data.get('diaries', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        query = Diary.query.filter_by(user_id=current_user.id, is_deleted=False)
        if diary_ids:
            query = query.filter(Diary.id.in_(diary_ids))
        if start_date:
            query = query.filter(Diary.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Diary.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
        diaries = query.order_by(Diary.created_at).all()
        if format_type == 'json':
            data = [{
                'id': d.id,
                'title': d.title,
                'content': d.content,
                'created_at': d.created_at.isoformat(),
                'mood': d.mood,
                'location': d.location,
                'is_public': d.is_public
            } for d in diaries]
            return jsonify(data)
        elif format_type == 'markdown':
            output = ""
            for d in diaries:
                output += f"# {d.title}\n\n"
                output += f"- 日期：{d.created_at.strftime('%Y-%m-%d')}\n"
                output += f"- 心情：{d.mood}\n"
                output += f"- 位置：{d.location}\n\n"
                output += f"{d.content}\n\n---\n\n"
            return Response(
                output,
                mimetype='text/markdown',
                headers={
                    "Content-Disposition": f"attachment;filename=diary_export_{datetime.now().strftime('%Y%m%d')}.md"
                }
            )
        elif format_type == 'txt':
            output = ""
            for d in diaries:
                output += f"{d.title}\n"
                output += f"日期：{d.created_at.strftime('%Y-%m-%d')}\n"
                output += f"心情：{d.mood}\n"
                output += f"位置：{d.location}\n\n"
                output += f"{d.content}\n\n"
                output += "=" * 50 + "\n\n"
            return Response(
                output,
                mimetype='text/plain',
                headers={
                    "Content-Disposition": f"attachment;filename=diary_export_{datetime.now().strftime('%Y%m%d')}.txt"
                }
            )
        elif format_type == 'html':
            template = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>我的日记导出</title>
                <style>
                    body { max-width: 800px; margin: 0 auto; padding: 20px; font-family: sans-serif; }
                    .diary { margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
                    .diary-title { font-size: 24px; margin-bottom: 10px; }
                    .diary-meta { color: #666; font-size: 14px; margin-bottom: 20px; }
                    .diary-content { line-height: 1.6; }
                </style>
            </head>
            <body>
            '''
            for d in diaries:
                template += f'''
                <div class="diary">
                    <h2 class="diary-title">{d.title}</h2>
                    <div class="diary-meta">
                        <p>日期：{d.created_at.strftime('%Y-%m-%d')}</p>
                        <p>心情：{d.mood}</p>
                        <p>位置：{d.location}</p>
                    </div>
                    <div class="diary-content">
                        {d.content.replace('\n', '<br>')}
                    </div>
                </div>
                '''
            template += '</body></html>'
            return Response(
                template,
                mimetype='text/html',
                headers={
                    "Content-Disposition": f"attachment;filename=diary_export_{datetime.now().strftime('%Y%m%d')}.html"
                }
            )
        else:
            return jsonify({'error': '不支持的导出格式'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        # 获取表单数据
        data = request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        nickname = data.get('nickname', '').strip()
        
        # 基本验证
        if not username or not password or not nickname:
            return jsonify({
                'success': False, 
                'message': '所有字段都是必填的'
            })
            
        # 用户名长度验证
        if len(username) < 5 or len(username) > 12:
            return jsonify({
                'success': False, 
                'message': '用户名长度必须在5-12位之间'
            })
        
        # 用户名格式验证(只允许字母、数字和下划线)
        if not username.isalnum():
            return jsonify({
                'success': False, 
                'message': '用户名只能包含字母和数字'
            })
            
        # 昵称长度验证
        if len(nickname) > 20:
            return jsonify({
                'success': False, 
                'message': '昵称长度不能超过20位'
            })
            
        # 密码强度验证
        if len(password) < 6:
            return jsonify({
                'success': False, 
                'message': '密码长度不能少于6位'
            })
            
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False, 
                'message': '用户名已被使用'
            })

        try:
            # 创建新用户
            new_user = User(
                username=username,
                nickname=nickname,
                last_username_change=None,
                days_until_username_change=0
            )
            new_user.set_password(password)
            
            # 添加默认设置
            user_settings = Setting(
                user_id=new_user.id,
                theme_settings=Setting.get_default_settings()
            )
            
            db.session.add(new_user)
            db.session.add(user_settings)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '注册成功'
            })
            
        except Exception as e:
            db.session.rollback()
            print(f"数据库错误: {str(e)}")
            return jsonify({
                'success': False,
                'message': '注册失败，请稍后重试'
            })

    except Exception as e:
        print(f"注册异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': '系统错误，请稍后重试'
        })

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if 'nickname' in data:
                current_user.nickname = data['nickname']
            if 'theme_settings' in data:
                if not current_user.settings:
                    current_user.settings = Setting(user_id=current_user.id)
                theme_settings = {
                    'primary_color': data['theme_settings']['primary_color'],
                    'accent_color': data['theme_settings']['accent_color'],
                    'card_radius': int(data['theme_settings']['card_radius']),
                    'card_opacity': int(data['theme_settings']['card_opacity']),
                    'nav_opacity': int(data['theme_settings']['nav_opacity'])
                }
                current_user.settings.theme_settings = theme_settings
                session['theme_settings'] = theme_settings
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            print(f"Settings update error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return render_template('settings.html', 
        user=current_user,
        current_settings=current_user.settings.theme_settings if current_user.settings else None,
        can_change_username=current_user.can_change_username,
        days_until_change=current_user.days_until_next_change
    )

@app.route('/api/settings/theme', methods=['POST'])
@login_required
def update_theme():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的数据格式'}), 400

        # 处理用户名更改
        if 'username' in data and data['username'] != current_user.username:
            if not current_user.can_change_username:
                return jsonify({'success': False, 'error': f'需要等待{current_user.days_until_next_change}天后才能修改用户名'}), 400
            
            if len(data['username']) < 5 or len(data['username']) > 12:  # 修改这里
                return jsonify({'success': False, 'error': '用户名长度必须在5-12位之间'}), 400
            
            # 检查用户名是否已存在
            if User.query.filter(User.username == data['username'], User.id != current_user.id).first():
                return jsonify({'success': False, 'error': '用户名已被使用'}), 400
            
            current_user.username = data['username']
            current_user.last_username_change = datetime.now()

        # 处理密码更改
        if 'new_password' in data and data['new_password']:
            if not current_user.check_password(data['current_password']):
                return jsonify({'success': False, 'error': '当前密码错误'}), 400
            current_user.set_password(data['new_password'])

        # 处理昵称
        if 'nickname' in data:
            current_user.nickname = data['nickname']

        # 处理主题设置
        if 'theme_settings' in data:
            if not current_user.settings:
                current_user.settings = Setting(user_id=current_user.id)
            theme_settings = {
                'primary_color': data['theme_settings']['primary_color'],
                'accent_color': data['theme_settings']['accent_color'],
                'card_radius': int(data['theme_settings']['card_radius']),
                'card_opacity': int(data['theme_settings']['card_opacity']),
                'nav_opacity': int(data['theme_settings']['nav_opacity'])
            }
            current_user.settings.theme_settings = theme_settings
            session['theme_settings'] = theme_settings

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Settings update error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings/avatar', methods=['POST'])
@login_required
def update_avatar():
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        if file:
            # 确保上传目录存在
            upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成安全的文件名
            filename = secure_filename(f"{current_user.id}_{int(time.time())}{os.path.splitext(file.filename)[1]}")
            filepath = os.path.join(upload_dir, filename)
            
            # 保存文件
            file.save(filepath)
            
            # 更新数据库中的头像路径
            avatar_url = url_for('static', filename=f'uploads/avatars/{filename}')
            current_user.avatar = avatar_url
            db.session.commit()
            
            return jsonify({
                'success': True,
                'avatar_url': avatar_url
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/fonts/<path:filename>')
def serve_font(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'fonts'), filename)

@app.route('/admin/users')
@login_required
def admin_users_page():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/diaries')
@login_required
def admin_diaries_page():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    diaries = Diary.query.all()
    return render_template('admin/diaries.html', diaries=diaries)

@app.route('/api/admin/user/<int:user_id>', methods=['PATCH'])
@login_required
def admin_update_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    
    try:
        data = request.get_json()
        user = User.query.get_or_404(user_id)
        
        if 'username' in data:
            # 检查用户名是否已存在
            if User.query.filter(User.username == data['username'], 
                               User.id != user_id).first():
                return jsonify({'error': '用户名已存在'}), 400
            user.username = data['username']
            
        if 'nickname' in data:
            user.nickname = data['nickname']
            
        if 'password' in data:
            user.set_password(data['password'])
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user/<int:user_id>/admin', methods=['POST'])
@login_required
def admin_toggle_admin(user_id):
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
    if user_id == current_user.id:
        return jsonify({'error': '不能修改自己的权限'}), 400
        
    try:
        data = request.get_json()
        user = User.query.get_or_404(user_id)
        
        # 如果要设置为管理员,先检查是否已存在其他管理员
        if data['is_admin']:
            existing_admin = User.query.filter(User.is_admin == True, User.id != current_user.id).first()
            if existing_admin:
                return jsonify({'error': '系统只允许存在一位管理员'}), 400
        else:
            # 如果要取消管理员,检查是否是最后一个管理员
            admin_count = User.query.filter(User.is_admin == True).count()
            if admin_count <= 1:
                return jsonify({'error': '必须保留至少一位管理员'}), 400
                
        user.is_admin = data['is_admin']
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user/<int:user_id>/password', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if not current_user.is_admin:
        return jsonify({'error': '无权限'}), 403
        
    try:
        data = request.get_json()
        user = User.query.get_or_404(user_id)
        
        if not data.get('password'):
            return jsonify({'error': '密码不能为空'}), 400
            
        user.set_password(data['password'])
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_username', methods=['POST'])
def check_username():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        # 基本格式验证
        if not username or len(username) < 5 or len(username) > 12:
            return jsonify({'available': False})
        
        if not username.isalnum():
            return jsonify({'available': False})
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        
        return jsonify({
            'available': existing_user is None
        })
        
    except Exception as e:
        print(f"检查用户名错误: {str(e)}")
        return jsonify({'available': False})

if __name__ == '__main__':
    app.run(debug=True, port=5001)