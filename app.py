import os
from flask import Flask, render_template, redirect, url_for, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import desc, func
from datetime import datetime
from sqlalchemy import text
from models import User, Diary, Like, SystemConfig, Setting, db
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'mysql://root:y20051010@localhost/diary_app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        # 首先禁用外键约束
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
        
        try:
            # 创建所有表
            db.create_all()
            
            # 创建管理员账号
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    nickname='管理员',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
            
            # 创建系统配置
            config = SystemConfig.query.first()
            if not config:
                config = SystemConfig(
                    theme_color='#2196F3',
                    font_family='975HazyGothic SC',
                    custom_css='',
                    stats_settings={
                        'show_users': True,
                        'show_diaries': True,
                        'card_style': 'default'
                    }
                )
                db.session.add(config)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error in database initialization: {e}")
            raise
        finally:
            # 恢复外键约束
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

@app.route('/profile')
@login_required
def profile():
    if current_user.is_admin and request.args.get('admin') != '0':
        return redirect(url_for('admin_dashboard'))
    return render_template('profile.html', user=current_user)

@app.route('/wall')
def wall():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Diary.query.filter_by(is_public=True)\
        .order_by(desc(Diary.created_at))\
        .paginate(page=page, per_page=per_page)
    return render_template('wall.html',
        diary_list=pagination.items,
        page=page,
        has_next=pagination.has_next,
        empty_title="还没有日记",
        empty_subtitle="来写第一篇吧",
        empty_icon="public",
        empty_text="还没有人来写日记呢",
        empty_button_text="来写第一篇日记吧"
    )

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_diary():
    if request.method == 'POST':
        try:
            data = request.get_json()
            date_str = data.get('date')
            if not date_str:
                date_str = datetime.now().strftime('%Y-%m-%d')
            new_diary = Diary(
                title=data.get('title'),
                content=data.get('content'),
                mood=data.get('mood'),
                location=data.get('location'),
                created_at=datetime.strptime(date_str, '%Y-%m-%d'),
                is_public=data.get('is_public', False),
                user_id=current_user.id
            )
            db.session.add(new_diary)
            db.session.commit()
            return jsonify({
                'success': True,
                'diary_id': new_diary.id
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
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
            diary.title = data.get('title')
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
            if request.is_json:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                nickname = data.get('nickname')
                captcha = data.get('captcha')
            else:
                username = request.form.get('username')
                password = request.form.get('password')
                nickname = request.form.get('nickname')
                captcha = request.form.get('captcha')
            if captcha != session.get('captcha'):
                return jsonify({'error': '验证码错误', 'success': False})
            new_user = User(
                username=username,
                nickname=nickname
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e), 'success': False})
    captcha = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
    session['captcha'] = captcha
    img = Image.new('RGB', (120, 30), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    fnt = ImageFont.load_default()
    for i, char in enumerate(captcha):
        d.text((10 + i * 20, 10), char, font=fnt, fill=(0, 0, 0))
    img.save('captcha.png')
    return render_template('create_user.html', captcha_img='captcha.png')

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

@app.route('/api/diary/<int:diary_id>/like', methods=['POST'])
def like_diary(diary_id):
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    user_id = session['user_id']
    diary = Diary.query.get_or_404(diary_id)
    like = Like.query.filter_by(user_id=user_id, diary_id=diary_id).first()
    if like:
        db.session.delete(like)
        diary.likes_count -= 1
    else:
        like = Like(user_id=user_id, diary_id=diary_id)
        db.session.add(like)
        diary.likes_count += 1
    db.session.commit()
    return jsonify({
        'success': True,
        'likes_count': diary.likes_count,
        'is_liked': like is not None
    })

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
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify({'error': '不能删除管理员账号'}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

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
    diary = Diary.query.get_or_404(diary_id)
    if diary.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': '无权限删除'}), 403
    db.session.delete(diary)
    db.session.commit()
    return jsonify({'success': True})

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
    per_page = 10
    pagination = Diary.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Diary.created_at))\
        .paginate(page=page, per_page=per_page)
    return render_template('mydiary.html',
        diary_list=pagination.items,
        page=page,
        has_next=pagination.has_next,
        empty_title="没有日记",
        empty_subtitle="写下第一篇吧",
        empty_icon="edit",
        empty_text="您还没有写过日记哦",
        empty_button_text="开始写第一篇日记"
    )

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if 'username' in data and data['username'] != current_user.username:
                user = User.query.get(current_user.id)
                if not user.can_change_username:
                    days_left = user.days_until_username_change
                    return jsonify({
                        'success': False,
                        'error': f'需要等待{days_left}天后才能修改用户名'
                    }), 403
                if User.query.filter_by(username=data['username']).first():
                    return jsonify({'success': False, 'error': '用户名已被使用'}), 400
                user.username = data['username']
                user.username_changed_at = datetime.now()
            if 'nickname' in data:
                current_user.nickname = data['nickname']
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            print(f"Error in settings: {str(e)}")
            return jsonify({'error': str(e)}), 500
    user = User.query.get(current_user.id)
    return render_template('settings.html',
        user=user,
        can_change_username=user.can_change_username,
        days_until_change=user.days_until_username_change
    )

@app.route('/api/settings/profile', methods=['POST'])
@login_required
def update_profile():
    try:
        user = User.query.get(current_user.id)
        if 'nickname' in request.form:
            user.nickname = request.form.get('nickname')
        
        # 我们不再处理头像上传
        # if 'avatar' in request.files:
        #     file = request.files['avatar']
        #     if file and allowed_file(file.filename):
        #         filename = secure_filename(file.filename)
        #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #         user.avatar = filename

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings/theme', methods=['POST'])
@login_required
def update_theme():
    try:
        data = request.get_json()
        user = User.query.get(current_user.id)
        if not user.settings:
            user.settings = Setting(user_id=user.id)
        user.settings.update_theme_settings(data)
        db.session.commit()
        session['theme_settings'] = user.settings.theme_settings
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings/update', methods=['POST'])
@login_required
def update_all_settings():
    try:
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"avatar_{current_user.id}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                relative_path = os.path.join('uploads', 'avatars', filename)
                current_user.avatar = relative_path
        theme_settings = {
            'primary_color': request.form.get('theme_color', '#2196F3'),
            'accent_color': request.form.get('accent_color', '#448AFF'),
            'card_radius': int(request.form.get('card_radius', 8)),
            'card_opacity': int(request.form.get('card_opacity', 100))
        }
        setting = Setting.query.filter_by(user_id=current_user.id).first()
        if not setting:
            setting = Setting(user_id=current_user.id)
            db.session.add(setting)
        setting.theme_settings = theme_settings
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)