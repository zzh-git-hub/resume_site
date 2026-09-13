# 个人简历站 - Personal Resume Website

一个基于 Python Flask 的现代化个人简历网站，具有营销风格的上下翻页动画、打字机效果和完整的管理后台。

## ✨ 功能特性

### 前端展示
- **上下翻页动画** — CSS `scroll-snap-type` 实现的页面级滚动，类似营销站的浏览体验
- **打字机效果** — Hero 区域循环展示多个标题词，带删除再输入动画
- **粒子动态背景** — Canvas 粒子系统，鼠标悬停产生交互效果
- **右侧导航圆点** — 随滚动自动高亮当前区块，点击快速跳转
- **滚动进度条** — 顶部渐变进度条显示浏览进度
- **Reveal 动画** — 区块进入视口时渐入上滑
- **键盘导航** — 上下方向键切换区块
- **深色炫酷主题** — 紫蓝渐变、毛玻璃效果、动态光晕

### 管理后台
| 功能 | 说明 |
|------|------|
| 基本信息 | 站点名称、Hero 名称、打字机词、个人简介、页脚文字 |
| 区块内容 | 7个区块的标题、副标题、可见性开关 |
| 条目管理 | 增删改工作经历、技能、项目、教育信息 |
| 社交链接 | GitHub、LinkedIn、微信、邮箱 |

### 技术栈
| 层 | 技术 |
|---|------|
| 后端 | Python Flask + SQLAlchemy + SQLite |
| 前端 | Pure HTML/CSS/JS + Vue 3 (CDN, 仅管理后台) |
| 认证 | Flask-Login + Werkzeug 密码哈希 |
| API | RESTful JSON API |

## 🚀 快速开始

### 环境要求
- Python 3.10+
- pip

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/resume-site.git
cd resume-site

# 安装依赖
pip install flask flask-sqlalchemy flask-login flask-wtf bcrypt email-validator

# 启动
cd resume_site
python app.py
```

### 访问
| 页面 | 地址 |
|------|------|
| 首页 | http://localhost:5000 |
| 管理后台 | http://localhost:5000/admin |

### 默认管理员
- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 首次部署请务必修改默认密码！

## 📁 项目结构

```
resume_site/
├── app.py                  # Flask 主程序
├── static/                 # 静态资源
│   └── uploads/            # 上传文件
├── templates/
│   ├── index.html          # 首页 (7区块翻页 + 打字机 + 粒子)
│   └── admin/
│       ├── index.html      # 管理后台 (Vue 3 SPA)
│       └── login.html      # 管理员登录页
└── instance/
    └── resume.db           # SQLite 数据库 (自动创建)
```

### 数据库初始化
首次运行时自动完成：
- 创建 7 个默认区块（主页、关于、经历、技能、项目、教育、联系）
- 创建示例条目（3条工作经历、4项技能、3个项目、2条教育）
- 创建 14 项站点配置
- 创建默认管理员账号

## 🔌 API 接口

### 公开接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/site-config` | 获取所有站点配置 |
| GET | `/api/sections` | 获取所有可见区块及条目 |

### 管理接口 (需登录)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/PUT | `/api/admin/config` | 获取/更新站点配置 |
| GET | `/api/admin/sections` | 获取所有区块(含隐藏) |
| PUT | `/api/admin/section/<key>` | 更新区块 |
| POST | `/api/admin/item` | 添加条目 |
| PUT | `/api/admin/item/<id>` | 更新条目 |
| DELETE | `/api/admin/item/<id>` | 删除条目 |
| POST | `/api/admin/upload` | 上传图片 |

## 🎨 自定义

### 修改主题色
编辑 `templates/index.html` 中的 CSS 变量 `#667eea` (主色) 和 `#764ba2` (辅色)。

### 添加区块
在 `app.py` 的 `init_database()` 函数中添加新的 `ResumeSection`。

### 修改打字机词汇
登录管理后台 → 基本信息 → 打字机循环词，或直接修改数据库中的 `site_config` 表。

## 📝 License

MIT License