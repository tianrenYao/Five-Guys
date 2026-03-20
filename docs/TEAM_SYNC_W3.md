# Group 9 - Five Guys 项目同步文档（Week 3）

> 更新日期：2026-03-20 | 编写：Liu Haopu

---

## 一、项目概览

### 我们在做什么？
一个**面向企业的商业可持续发展管理平台**（Web 应用），帮助企业：
- 追踪碳排放数据（用电、交通、燃油、通勤）
- 管理垃圾分类和回收数据
- 自动生成可持续发展报告（支持 PDF 导出）

### 为什么做这个？
- 课程要求：围绕**可持续发展主题**做一个完整软件项目
- 对齐联合国 SDG 目标（SDG 9/11/12/13）
- 必须部署到虚拟机，支持爱尔兰远程测试

### 技术栈（已确定，不能改）
| 层级 | 技术 |
|---|---|
| 前端 | HTML + CSS + JavaScript + Bootstrap 5 + ECharts |
| 后端 | Python Flask |
| 数据库 | MySQL |
| PDF导出 | ReportLab |

> ⚠️ 老师要求不能用 Vue / React / Next.js 等新框架，只能用已学技能。

---

## 二、当前进度

### ✅ 已完成的工作（由 Liu Haopu 完成）

**1. 数据库设计（完整版）**
- 10 张数据表 + 2 个查询视图
- 包含：企业表、用户表、碳排放因子表、碳排放记录表、垃圾类别表、垃圾记录表、报告表、SDG目标表、企业-SDG关联表、操作审计日志表
- 密码采用哈希加密存储，非明文
- 预置了 12 条碳排放因子（来自 IPCC/DEFRA 2023 标准）
- 预置了 5 种垃圾类别、4 个 SDG 目标
- 文件位置：`database/schema.sql`、`database/DATABASE_DESIGN.md`

**2. 后端 API（Flask，共 22 个接口）**
| 模块 | 接口数 | 功能 |
|---|---|---|
| 认证 | 4 | 登录、登出、获取当前用户信息 |
| Dashboard | 4 | 年度汇总、碳排放趋势、分类占比、垃圾构成 |
| 碳排放 | 4 | 排放因子查询、记录增删、日期筛选 |
| 垃圾管理 | 5 | 类别查询、记录增删、日期筛选、月度统计 |
| 报告 | 5 | 生成、列表、详情、PDF导出、删除 |

**3. 前端页面（5 个完整页面）**
- `login.html` - 登录页（带测试账号提示）
- `dashboard.html` - 数据大盘（4 个指标卡 + 3 个 ECharts 图表 + SDG 展示）
- `carbon.html` - 碳排放录入 + 记录列表 + 日期筛选
- `waste.html` - 垃圾管理录入 + 记录列表 + 月度统计图
- `report.html` - 报告生成 + 报告列表 + 预览 + PDF 导出

**4. 已通过本地测试**
- 所有 API 均可正常调用
- 测试账号：`test_business / 123456`（企业管理员）、`test_staff / 123456`（员工）
- 示例数据：9 条碳排放记录 + 9 条垃圾记录

### 📂 项目文件结构
```
项目文件/
├── .env.example          ← 环境变量模板（MySQL密码等）
├── .gitignore            ← Git忽略规则
├── README.md             ← 项目说明和启动指南
├── requirements.txt      ← Python依赖包
├── database/
│   ├── schema.sql        ← 数据库建表脚本
│   └── DATABASE_DESIGN.md ← 数据库设计文档
├── backend/
│   ├── app.py            ← Flask主程序入口
│   ├── config.py         ← 配置文件
│   ├── init_db.py        ← 数据库初始化脚本
│   ├── routes/           ← 5个路由模块（auth/dashboard/carbon/waste/report）
│   └── utils/            ← 工具（数据库连接/权限验证）
├── frontend/
│   ├── static/css/       ← 全局样式
│   ├── static/js/        ← 5个页面对应的JS文件
│   └── templates/        ← 6个HTML模板
└── docs/                 ← 项目文档
```

---

## 三、WP 分工与16周时间线

### 整体时间线
| 阶段 | 时间 | 内容 | 关键里程碑 |
|---|---|---|---|
| WP1 需求设计 | W1-W4（3月） | 需求分析、架构设计、原型图 | M1：设计文档终版 |
| WP2 后端开发 | W5-W8（4月初） | 数据库+后端接口 | M2：后端完成；M3：中期报告(W9) |
| WP3 前端框架 | W9-W12 | 前端基础组件 | - |
| WP4 前端模块 | W9-W12 | 三大业务模块前端 | M4：前端完成 |
| WP5 集成测试 | W13-W16 | 测试+优化+部署 | M5：平台可远程访问 |
| WP6 文档交付 | W17-W18 | 文档+汇报+验收 | M6：最终交付 |

### 各 WP 负责人
| WP | Manager | Contributors |
|---|---|---|
| WP1 需求设计 | You Haoyang | Liu Haopu, Li Sihang |
| WP2 后端开发 | Liu Haopu | Yao Tianren, Li Sihang, Lu Yu'an |
| WP3 前端框架 | Li Sihang | You Haoyang |
| WP4 前端模块 | Li Sihang | 全员 |
| WP5 集成测试 | Lu Yu'an | Liu Haopu, You Haoyang, Li Sihang |
| WP6 文档交付 | Liu Haopu | You Haoyang, Yao Tianren |

---

## 四、⚡ 本周（W3-W4）每个人的具体任务

> 目标：完成 WP1 的核心交付物，同时把项目推到 GitHub

### @You Haoyang（WP1 Manager）
**写需求规格说明书**，包含：
1. 平台核心用户是谁（企业管理者 + 普通员工）
2. 每个模块的功能需求清单：
   - 碳排放追踪：哪些数据要录入？怎么计算？怎么展示？
   - 垃圾管理：哪些分类？怎么统计回收率？
   - 报告生成：报告包含什么内容？支持什么格式？
3. 非功能需求（远程可访问、支持主流浏览器、固定测试账号）

**输出格式**：Word 文档，放到 `docs/` 文件夹  
**截止时间**：W4 初（下周前完成）

---

### @Li Sihang
**画前端原型图**（5 个页面的布局草图），包含：
1. 登录页
2. Dashboard（数据大盘）
3. 碳排放追踪页
4. 垃圾管理页
5. 报告生成页

> 💡 可以参考我已经写好的前端页面来画，但原型图需要展示你的 UI 设计思路。

**工具**：Figma（免费）/ draw.io / PPT 都行  
**输出格式**：截图或 PDF，放到 `docs/` 文件夹  
**截止时间**：W4 初

---

### @Yao Tianren（GitHub 仓库 Owner）
**任务 1：在 GitHub 上初始化仓库**
- 仓库地址：https://github.com/tianrenYao/Five-Guys.git
- 创建 README.md（可以直接用我写好的）
- 设置 `.gitignore`（已写好）
- 邀请所有组员为 Collaborator

**任务 2：写技术选型文档**
- 为什么选 Flask 而不是 Spring Boot？
- 为什么选 MySQL？
- 为什么用 Bootstrap + ECharts 而不是 Vue/React？
- 部署环境是什么（虚拟机 OS、Python 版本、MySQL 版本）

**输出格式**：Markdown 文件 `docs/tech_stack.md`  
**截止时间**：W4 初

---

### @Lu Yu'an
**写架构设计文档**，包含：
1. 系统架构图（前端 → Flask 后端 → MySQL，画个简单的框图就行）
2. 数据库 ER 图（可以根据 `database/DATABASE_DESIGN.md` 来画）
3. 模块关系图（3 个业务模块如何和公共模块交互）
4. API 接口概览表（我已经写了 22 个接口，整理成表格即可）

**工具**：draw.io / Visio / PPT  
**输出格式**：文档 + 图片，放到 `docs/` 文件夹  
**截止时间**：W4 初

---

### @Liu Haopu（我）
- ✅ 已完成：数据库设计 + 后端 + 前端 + 本地测试
- 本周：审核大家的 WP1 文档，协调 Git 推送

---

## 五、Git 使用说明

### 基本原则
1. **老师会看 Git 提交记录来评判每个人的贡献**，所以每个人必须用自己的 Git 账号提交自己负责的内容
2. 先在本地做好，确认没问题后再推送
3. Commit message 要写清楚做了什么

### 如何开始
```bash
# 1. 克隆仓库
git clone https://github.com/tianrenYao/Five-Guys.git
cd Five-Guys

# 2. 配置你的 Git 用户名（重要！用你自己的名字）
git config user.name "你的名字拼音"
git config user.email "你的邮箱"

# 3. 创建你的分支
git checkout -b feature/你的任务名

# 4. 做完改动后提交
git add .
git commit -m "WP1: 简短描述你做了什么"
git push origin feature/你的任务名

# 5. 在 GitHub 上创建 Pull Request，合并到 main
```

### Commit Message 示例
```
WP1: Add requirements specification document
WP1: Add frontend wireframe prototypes
WP1: Add tech stack selection document
WP1: Add system architecture design document
WP2: Add database schema and design document
WP2: Add Flask backend with auth, carbon, waste, report APIs
WP3: Add frontend base template and login page
```

---

## 六、如何本地运行项目（想体验的同学看这里）

### 前提条件
- Python 3.10+
- MySQL 8.0+

### 步骤
```bash
# 1. 克隆仓库后进入项目目录
cd Five-Guys

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 创建 .env 文件（复制模板，填入你的 MySQL 密码）
cp .env.example .env
# 编辑 .env，修改 MYSQL_PASSWORD

# 4. 在 MySQL 中执行建表脚本
mysql -u root -p < database/schema.sql

# 5. 初始化测试账号和示例数据
python3 backend/init_db.py

# 6. 启动服务
python3 backend/app.py

# 7. 打开浏览器访问 http://localhost:5001
# 登录：test_business / 123456
```

---

## 七、现有框架的改进方向（后续可以做的）

| 方向 | 说明 | 优先级 |
|---|---|---|
| UI 美化 | 调整颜色、布局、图标，让界面更专业 | 中 |
| 数据导入 | 支持 CSV/Excel 批量导入碳排放和垃圾数据 | 高 |
| 图表丰富 | Dashboard 增加更多图表类型（雷达图、热力图） | 中 |
| 用户管理 | 管理员可以增删用户、修改密码 | 低 |
| 邮件通知 | 报告生成后发送邮件通知 | 低 |
| 多语言支持 | 英文/中文切换 | 低 |
| 数据导出 | 支持 CSV 导出碳排放和垃圾数据 | 中 |
| SDG 评分 | 根据碳排放和回收率自动计算 SDG 达标情况 | 中 |

---

## 八、有问题找谁？

| 问题 | 找谁 |
|---|---|
| 代码/技术问题 | Liu Haopu |
| GitHub 仓库权限 | Yao Tianren |
| 项目需求不清楚 | You Haoyang |
| 前端/UI 问题 | Li Sihang |
| 测试/部署问题 | Lu Yu'an |

---

**请大家在 W4 初之前完成各自的任务，有问题随时在群里说！** 🚀
