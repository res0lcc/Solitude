# Solitude - 个人日记系统

一个使用 Flask + MDUI 开发的个人日记系统。专注于写作体验，提供简洁优雅的界面。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-blue.svg)

## 项目简介

Solitude 是一个专注于写作体验的个人日记应用，提供简洁优雅的界面和流畅的操作体验。

## 功能特性

### 已实现功能
- 📝 日记管理
  - 创建、删除日记
  - 支持心情和位置标记
  - 日记内容自动保存
  - 日记分页浏览
  
- 🌏 日记墙
  - 公开日记展示
  - 支持日记转发分享
  
- 🎨 界面定制
  - 主题颜色切换
  - 卡片样式自定义
  - 界面样式调节
  
- 🛡️ 安全特性
  - 密码加密存储
  - 操作权限控制

### 计划功能
- 📱 移动端适配优化
- 📊 数据统计分析
- 🔍 日记全文搜索
- 📥 数据导入导出
- 🌙 深色模式支持
- ⚡ 性能优化提升

## 技术栈

### 后端
- Flask: Web框架
- SQLAlchemy: ORM框架
- Flask-Login: 用户认证
- Flask-Migrate: 数据库迁移
- MySQL: 数据库

### 前端
- MDUI: UI框架
- JavaScript: 交互逻辑
- CSS3: 样式布局

## 项目结构

```
solitude/
├── app.py              # 应用主入口
├── models.py           # 数据模型
├── requirements.txt    # 项目依赖
├── static/             # 静态资源
│   ├── css/            # 样式文件
│   ├── js/             # JavaScript文件
│   ├── fonts/          # 字体文件
│   └── uploads/        # 上传文件目录
├── templates/          # 模板文件
│   ├── base.html       # 基础模板
│   ├── login.html      # 登录页面
│   ├── mydiary.html    # 我的日记
│   ├── wall.html       # 日记墙
│   └── ...
└── migrations/         # 数据库迁移文件
```

## 使用教程

### 环境要求
- Python 3.8+
- MySQL 5.7+
- pip

## 安装依赖
```python
pip install requirement.txt
```

### 配置数据库
创建MySQL数据库
```sql
CREATE DATABASE diary_app DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

修改配置文件中的数据库连接信息(app.py)
```python
SQLALCHEMY_DATABASE_URI = 'mysql://用户名:密码@localhost/diary_app'
```

### 初始化数据库
```bash
flask db upgrade
```

## 创建管理员账号
```python
python admin.py
```

## 默认管理员账号
- 用户名: admin
- 密码: admin

### 运行系统
```bash
python app.py
```

### 访问系统
浏览器访问 http://localhost:5001

## 部署到服务器

### 1. 配置环境变量

在项目根目录下创建 `.env` 文件，并添加以下内容：

```
DATABASE_URI=mysql://<username>:<password>@<host>/<database_name>
SECRET_KEY=your_secret_key
```

### 2. 配置生产环境

建议使用 `gunicorn` 和 `nginx` 来部署生产环境。

#### 使用 `gunicorn` 运行应用

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 配置 `nginx`

在 `/etc/nginx/sites-available/` 目录下创建一个新的配置文件，例如 `solitude`：

```
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置并重启 `nginx`：

```bash
sudo ln -s /etc/nginx/sites-available/solitude /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```



## 贡献指南
1. Fork 本仓库
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

## 开源协议
本项目采用 MIT 协议开源。

## 联系方式
作者邮箱: 2926957031@qq.com