# web日记本

一个简单但功能完整的在线日记系统。

## 功能特点

- 用户注册和登录
- 日记的创建、编辑和删除
- 支持记录心情和位置
- 日记公开/私密设置
- 日记墙功能
- 个性化界面设置
  - 主题色配置
  - 导航栏透明度
  - 侧边栏透明度
  - 卡片圆角和透明度
- 响应式设计，支持移动端
- 管理后台

## 项目目录

```
c:\project\
├── app.py               # Flask 主程序
├── models.py            # 数据库模型
├── create_db.sql        # 数据库创建脚本
├── requirements.txt     # 项目依赖列表
├── README.md            # 使用说明
├── templates\           # 页面模板
│   ├── base.html        # 基础模板
│   ├── index.html       # 首页
│   ├── login.html       # 登录页面
│   ├── profile.html     # 个人中心页面
│   ├── wall.html        # 日记墙页面
│   ├── add.html         # 写日记页面
│   ├── edit.html        # 编辑日记页面
│   └── create_user.html # 用户注册页面
└── static\
    └── css\
        └── mdui.min.css # 自定义样式
```

## 开发环境搭建

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+
- Node.js 14+ (用于前端构建)

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 数据库配置

```bash
# 创建数据库
mysql -u root -p < create_db.sql

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置数据库连接信息
```

## 部署到服务器

### 1. 拉取代码

```bash
git clone https://github.com/res0lcc/daynote/git
cd project
```

### 2. 配置环境

按照开发环境搭建中的步骤安装依赖和配置数据库。

### 3. 配置环境变量

在项目根目录下创建 `.env` 文件，并添加以下内容：

```
DATABASE_URI=mysql://<username>:<password>@<host>/<database_name>
SECRET_KEY=your_secret_key
```

### 4. 运行项目

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 运行Flask应用
flask run --host=0.0.0.0 --port=5000
```

### 5. 配置生产环境

建议使用 `gunicorn` 和 `nginx` 来部署生产环境。

#### 使用 `gunicorn` 运行应用

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 配置 `nginx`

在 `/etc/nginx/sites-available/` 目录下创建一个新的配置文件，例如 `diary_app`：

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
sudo ln -s /etc/nginx/sites-available/diary_app /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 注意事项

- 示例中 session 中存储用户信息较简单，实际部署请完善会话管理和密码安全处理等。
- 请确保 MySQL 服务已开启，并正确配置数据库连接。

## 贡献

欢迎提交 Issue 和 Pull Request！