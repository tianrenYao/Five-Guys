# 企业可持续发展管理平台

> Group 9 - Five Guys | 大学软件工程课程项目

一个面向企业的可持续发展管理 Web 平台，帮助企业追踪碳排放、管理垃圾分类、自动生成可持续发展报告，对齐联合国可持续发展目标（SDG 9、11、12、13）。

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | HTML5、CSS3、JavaScript、Bootstrap 5、ECharts 5 |
| 后端 | Python 3.10+、Flask 3.x |
| 数据库 | MySQL 8.0+ |
| PDF 导出 | ReportLab |

## 项目结构

```
├── backend/
│   ├── app.py              # Flask 主应用
│   ├── config.py           # 配置管理
│   ├── init_db.py          # 数据库初始化脚本
│   ├── routes/
│   │   ├── auth.py         # 认证接口（登录/登出）
│   │   ├── carbon.py       # 碳排放追踪接口
│   │   ├── waste.py        # 垃圾管理接口
│   │   ├── report.py       # 报告生成接口
│   │   └── dashboard.py    # 数据大盘接口
│   └── utils/
│       ├── db.py           # 数据库连接工具
│       └── auth_helper.py  # 权限验证装饰器
├── frontend/
│   ├── static/
│   │   ├── css/style.css   # 全局样式
│   │   └── js/             # 各页面 JavaScript
│   └── templates/          # Jinja2 HTML 模板
├── database/
│   ├── schema.sql          # 完整数据库建表脚本
│   └── DATABASE_DESIGN.md  # 数据库设计文档
├── docs/                   # 项目文档（WP 交付物）
├── requirements.txt        # Python 依赖
└── .gitignore
```

## 快速开始

### 1. 创建 MySQL 数据库

```bash
mysql -u root -p < database/schema.sql
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 MySQL 密码
```

### 3. 安装 Python 依赖

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

### 4. 初始化测试账号和示例数据

```bash
python3 backend/init_db.py
```

### 5. 启动应用

```bash
python3 backend/app.py
```

在浏览器中访问 `http://localhost:5001`。

### 测试账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| test_business | 123456 | 企业管理员 |
| test_staff | 123456 | 普通员工 |

## 核心功能模块

### 1. 碳排放追踪
- 支持 4 大类排放源：用电、交通运输、燃油消耗、员工通勤
- 内置 IPCC/DEFRA 2023 标准排放因子（12 条）
- 自动计算碳排放量（活动值 × 排放因子）
- 按日期筛选、分类统计

### 2. 垃圾管理
- 5 大垃圾类别：纸张、塑料、有害废物、食物废弃物、电子废弃物
- 区分可回收/不可回收
- 自动计算回收率
- 月度统计图表

### 3. 可持续发展报告
- 支持月度/季度/年度/自定义周期报告
- 自动汇总碳排放和垃圾数据
- 对齐联合国 SDG 目标
- 支持 PDF 导出

## API 接口概览

| 模块 | 接口数 | 说明 |
|---|---|---|
| 认证 | 4 | 登录、登出、获取当前用户、登录页 |
| 数据大盘 | 4 | 年度汇总、碳排放趋势、分类占比、垃圾构成 |
| 碳排放 | 4 | 排放因子查询、记录列表、新增、删除 |
| 垃圾管理 | 5 | 类别查询、记录列表、新增、删除、月度统计 |
| 报告 | 5 | 列表、生成、详情、PDF导出、删除 |
| **合计** | **22** | |

## 数据库设计

共 10 张表 + 2 个视图：

| 表名 | 说明 |
|---|---|
| company | 企业信息 |
| user | 用户账号（密码哈希存储） |
| emission_factor | 碳排放因子（预置 12 条） |
| carbon_record | 碳排放记录 |
| waste_category | 垃圾类别（预置 5 种） |
| waste_record | 垃圾记录 |
| report | 可持续发展报告 |
| sdg_goal | 联合国 SDG 目标（预置 4 个） |
| company_sdg | 企业-SDG 关联 |
| audit_log | 操作审计日志 |

详细设计见 `database/DATABASE_DESIGN.md`。

## 团队分工

| 成员 | 主要职责 |
|---|---|
| You Haoyang | WP1 - 需求分析与架构设计 |
| Liu Haopu | WP2 - 数据库与后端开发 / WP6 - 文档交付 |
| Li Sihang | WP3 - 前端框架 / WP4 - 前端业务模块 |
| Lu Yu'an | WP5 - 集成测试与部署 |
| Yao Tianren | WP2 贡献者 / 仓库管理 |

## 许可证

本项目为课程作业，仅供学习使用。
