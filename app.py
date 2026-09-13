#!/usr/bin/env python3
"""
个人简历站 - Flask 后端
前后端分离架构，提供 RESTful API + 后台管理界面
"""
import os
import json
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, flash, session, send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ====== 初始化 ======
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resume.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# ====== 数据库模型 ======

class User(UserMixin, db.Model):
    """管理员用户"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ResumeSection(db.Model):
    """简历区块 - 每个区块对应首页的一个翻页"""
    id = db.Column(db.Integer, primary_key=True)
    section_key = db.Column(db.String(50), unique=True, nullable=False)  # hero, about, experience, skills, projects, education, contact
    title = db.Column(db.String(200), default='')
    subtitle = db.Column(db.String(300), default='')
    content = db.Column(db.Text, default='')
    icon = db.Column(db.String(50), default='')
    sort_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResumeItem(db.Model):
    """简历条目 - 区块内的具体项（工作经验、项目、技能等）"""
    id = db.Column(db.Integer, primary_key=True)
    section_key = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), default='')
    sub_title = db.Column(db.String(300), default='')  # 公司/学校名
    date_range = db.Column(db.String(100), default='')
    description = db.Column(db.Text, default='')
    tags = db.Column(db.String(500), default='')  # JSON array
    icon = db.Column(db.String(100), default='')
    link = db.Column(db.String(500), default='')
    sort_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteConfig(db.Model):
    """站点配置"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default='')
    value_type = db.Column(db.String(20), default='text')  # text, json, html


# ====== 初始化数据 ======

def init_database():
    """创建数据库并插入默认数据"""
    db.create_all()

    # 创建默认管理员
    if not User.query.first():
        admin = User(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    # 初始化区块
    sections = [
        {'key': 'hero', 'title': '个人主页', 'subtitle': '全栈工程师 · 创意开发者', 'sort_order': 1},
        {'key': 'about', 'title': '关于我', 'subtitle': '用代码创造价值', 'sort_order': 2},
        {'key': 'experience', 'title': '工作经历', 'subtitle': '职业发展历程', 'sort_order': 3},
        {'key': 'skills', 'title': '专业技能', 'subtitle': '技术栈 & 工具', 'sort_order': 4},
        {'key': 'projects', 'title': '项目作品', 'subtitle': '精选项目展示', 'sort_order': 5},
        {'key': 'education', 'title': '教育背景', 'subtitle': '学术经历', 'sort_order': 6},
        {'key': 'contact', 'title': '联系我', 'subtitle': '保持联系', 'sort_order': 7},
    ]
    for s in sections:
        if not ResumeSection.query.filter_by(section_key=s['key']).first():
            section = ResumeSection(
                section_key=s['key'],
                title=s['title'],
                subtitle=s['subtitle'],
                sort_order=s['sort_order']
            )
            db.session.add(section)

    # 初始化站点配置
    configs = [
        {'key': 'site_name', 'value': '我的个人简历', 'value_type': 'text'},
        {'key': 'site_description', 'value': '个人简历与作品展示', 'value_type': 'text'},
        {'key': 'site_avatar', 'value': '', 'value_type': 'text'},
        {'key': 'hero_name', 'value': '张三', 'value_type': 'text'},
        {'key': 'hero_typing_words', 'value': '["全栈工程师", "UI/UX 爱好者", "开源贡献者", "终身学习者"]', 'value_type': 'json'},
        {'key': 'hero_bg_style', 'value': 'gradient', 'value_type': 'text'},
        {'key': 'social_github', 'value': 'https://github.com', 'value_type': 'text'},
        {'key': 'social_linkedin', 'value': 'https://linkedin.com', 'value_type': 'text'},
        {'key': 'social_wechat', 'value': '', 'value_type': 'text'},
        {'key': 'social_email', 'value': 'hello@example.com', 'value_type': 'text'},
        {'key': 'about_avatar', 'value': '', 'value_type': 'text'},
        {'key': 'about_intro', 'value': '你好！我是一名热爱技术的全栈开发者，拥有5年Web开发经验。\n\n我专注于构建高性能、用户友好的Web应用。擅长从需求分析到部署上线的全流程开发。\n\n在工作之余，我喜欢参与开源项目、撰写技术博客，并不断探索前沿技术。', 'value_type': 'text'},
        {'key': 'contact_message', 'value': '如果您对我的简历感兴趣，欢迎通过以下方式联系我！', 'value_type': 'text'},
        {'key': 'footer_text', 'value': '© 2026 个人简历站. All Rights Reserved.', 'value_type': 'text'},
    ]
    for c in configs:
        if not SiteConfig.query.filter_by(key=c['key']).first():
            config = SiteConfig(key=c['key'], value=c['value'], value_type=c['value_type'])
            db.session.add(config)

    # 添加示例条目
    if not ResumeItem.query.first():
        examples = [
            # 工作经历
            {'section': 'experience', 'title': '高级全栈工程师', 'sub_title': '某科技有限公司', 'date_range': '2023 - 至今', 'description': '负责公司核心产品的全栈开发\n使用 React + Flask 技术栈重构前端架构\n主导微服务拆分，提升系统可维护性\n团队规模 8 人，负责代码审查和技术方案设计'},
            {'section': 'experience', 'title': '前端开发工程师', 'sub_title': '某互联网公司', 'date_range': '2020 - 2023', 'description': '负责用户端 Web 应用的开发与优化\n使用 Vue3 + TypeScript 构建组件库\n实现首屏加载性能优化 40%'},
            {'section': 'experience', 'title': '初级开发工程师', 'sub_title': '某软件公司', 'date_range': '2018 - 2020', 'description': '参与多个企业级项目的开发\n负责前后端功能模块的开发和维护'},

            # 技能
            {'section': 'skills', 'title': '前端开发', 'sub_title': '', 'description': 'React, Vue3, TypeScript, Next.js, Tailwind CSS', 'tags': '["前端", "框架"]'},
            {'section': 'skills', 'title': '后端开发', 'sub_title': '', 'description': 'Python, Flask, FastAPI, Node.js, Go', 'tags': '["后端", "语言"]'},
            {'section': 'skills', 'title': '数据库 & DevOps', 'sub_title': '', 'description': 'PostgreSQL, Redis, Docker, AWS, CI/CD', 'tags': '["基础设施"]'},
            {'section': 'skills', 'title': '设计工具', 'sub_title': '', 'description': 'Figma, Sketch, Photoshop, Illustrator', 'tags': '["设计"]'},

            # 项目
            {'section': 'projects', 'title': 'AI 智能客服平台', 'sub_title': '全栈开发', 'date_range': '2024', 'description': '基于大语言模型的智能客服系统，支持多轮对话、知识库管理、数据分析。日处理对话 10万+。', 'tags': '["React", "Python", "AI"]', 'link': 'https://github.com'},
            {'section': 'projects', 'title': '电商后台管理系统', 'sub_title': '前端负责人', 'date_range': '2023', 'description': '高可用的电商管理后台，包括商品管理、订单管理、数据看板等功能模块。', 'tags': '["Vue3", "Element Plus"]', 'link': 'https://github.com'},
            {'section': 'projects', 'title': '个人博客系统', 'sub_title': '独立开发', 'date_range': '2022', 'description': '支持 Markdown 编辑、标签分类、全文搜索的静态博客生成器。', 'tags': '["Next.js", "MDX"]', 'link': 'https://github.com'},

            # 教育
            {'section': 'education', 'title': '计算机科学与技术 硕士', 'sub_title': '某知名大学', 'date_range': '2016 - 2018', 'description': '研究方向：Web 性能优化\nGPA: 3.8/4.0\n发表论文 2 篇'},
            {'section': 'education', 'title': '软件工程 学士', 'sub_title': '某理工大学', 'date_range': '2012 - 2016', 'description': 'GPA: 3.6/4.0\n获得国家奖学金\nACM 竞赛省级银奖'},
        ]
        for e in examples:
            item = ResumeItem(
                section_key=e['section'],
                title=e['title'],
                sub_title=e.get('sub_title', ''),
                date_range=e.get('date_range', ''),
                description=e.get('description', ''),
                tags=e.get('tags', '[]'),
                link=e.get('link', ''),
                sort_order=e.get('sort_order', 0)
            )
            db.session.add(item)

    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ====== 认证装饰器 ======

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def api_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            # 简单 token 验证：用 session 方式
            if token == session.get('api_token', ''):
                return f(*args, **kwargs)
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        return jsonify({'error': 'Unauthorized'}), 401
    return decorated_function


# ====== API 路由 ======

# --- 公开 API ---

@app.route('/api/site-config')
def get_site_config():
    """获取站点配置"""
    configs = SiteConfig.query.all()
    data = {c.key: json.loads(c.value) if c.value_type == 'json' else c.value for c in configs}
    return jsonify(data)


@app.route('/api/sections')
def get_sections():
    """获取所有可见区块"""
    sections = ResumeSection.query.filter_by(is_visible=True).order_by(ResumeSection.sort_order).all()
    data = []
    for s in sections:
        items = ResumeItem.query.filter_by(
            section_key=s.section_key, is_visible=True
        ).order_by(ResumeItem.sort_order).all()
        data.append({
            'key': s.section_key,
            'title': s.title,
            'subtitle': s.subtitle,
            'content': s.content,
            'icon': s.icon,
            'items': [{
                'id': item.id,
                'title': item.title,
                'sub_title': item.sub_title,
                'date_range': item.date_range,
                'description': item.description,
                'tags': json.loads(item.tags) if item.tags else [],
                'icon': item.icon,
                'link': item.link
            } for item in items]
        })
    return jsonify(data)


# --- 管理后台 API ---

@app.route('/api/admin/config', methods=['GET', 'PUT'])
@login_required
def admin_config():
    """管理站点配置"""
    if request.method == 'GET':
        configs = SiteConfig.query.all()
        data = {c.key: {'value': json.loads(c.value) if c.value_type == 'json' else c.value,
                        'type': c.value_type} for c in configs}
        return jsonify(data)

    data = request.get_json()
    for key, value in data.items():
        config = SiteConfig.query.filter_by(key=key).first()
        if config:
            config.value = json.dumps(value, ensure_ascii=False) if config.value_type == 'json' else str(value)
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/api/admin/sections', methods=['GET'])
@login_required
def admin_get_sections():
    """获取所有区块（含隐藏）"""
    sections = ResumeSection.query.order_by(ResumeSection.sort_order).all()
    data = []
    for s in sections:
        items = ResumeItem.query.filter_by(section_key=s.section_key).order_by(ResumeItem.sort_order).all()
        data.append({
            'id': s.id,
            'key': s.section_key,
            'title': s.title,
            'subtitle': s.subtitle,
            'content': s.content,
            'is_visible': s.is_visible,
            'items': [{
                'id': item.id,
                'title': item.title,
                'sub_title': item.sub_title,
                'date_range': item.date_range,
                'description': item.description,
                'tags': item.tags,
                'link': item.link,
                'is_visible': item.is_visible,
                'sort_order': item.sort_order
            } for item in items]
        })
    return jsonify(data)


@app.route('/api/admin/section/<section_key>', methods=['PUT'])
@login_required
def admin_update_section(section_key):
    """更新区块"""
    section = ResumeSection.query.filter_by(section_key=section_key).first()
    if not section:
        return jsonify({'error': 'Section not found'}), 404
    data = request.get_json()
    for field in ['title', 'subtitle', 'content', 'is_visible']:
        if field in data:
            setattr(section, field, data[field])
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/api/admin/item', methods=['POST'])
@login_required
def admin_add_item():
    """添加条目"""
    data = request.get_json()
    item = ResumeItem(
        section_key=data['section_key'],
        title=data.get('title', ''),
        sub_title=data.get('sub_title', ''),
        date_range=data.get('date_range', ''),
        description=data.get('description', ''),
        tags=data.get('tags', '[]'),
        link=data.get('link', ''),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': item.id})


@app.route('/api/admin/item/<int:item_id>', methods=['PUT', 'DELETE'])
@login_required
def admin_item(item_id):
    """更新/删除条目"""
    item = db.session.get(ResumeItem, item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'status': 'ok'})

    data = request.get_json()
    for field in ['title', 'sub_title', 'date_range', 'description', 'tags', 'link', 'is_visible', 'sort_order']:
        if field in data:
            setattr(item, field, data[field])
    db.session.commit()
    return jsonify({'status': 'ok'})


# ====== 文件上传 ======

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/admin/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 添加时间戳防止覆盖
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'url': f'/static/uploads/{filename}'})
    return jsonify({'error': 'File type not allowed'}), 400


# ====== 页面路由 ======

@app.route('/')
def index():
    """首页 - SPA"""
    return render_template('index.html')


@app.route('/admin')
@app.route('/admin/')
@login_required
def admin_index():
    """管理后台 - 作为静态文件避免 Jinja2 解析 Vue 模板"""
    return send_from_directory(os.path.join(app.root_path, 'templates'), 'admin/index.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_index'))

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            session['api_token'] = os.urandom(938).hex()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_index'))
        flash('用户名或密码错误', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    session.pop('api_token', None)
    return redirect(url_for('admin_login'))


# ====== 主入口 ======

if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(host='0.0.0.0', port=5000, debug=True)