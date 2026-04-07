# Project Proposal 分工任务书

> **提交要求**：PDF 格式，约 2 页，第 5 周周五午夜前上传 Moodle  
> **时间节点**：各人初稿 → W4 周三前提交 → Liu Haopu 周四汇总 → 周五定稿提交  
> **语言**：英文，专业简洁  
> **提交方式**：写好后放到项目 `docs/` 目录下，文件命名见末尾

---

## 总览

| 部分 | 负责人 | 预计篇幅 | 初稿截止 |
|---|---|---|---|
| ① Project Overview（问题/愿景/收益） | You Haoyang | ~1/3 页 | W4 周三 |
| ② Deliverables（交付物清单） | Yao Tianren | ~1/6 页 | W4 周三 |
| ③ Success Criteria（SMART 标准） | Liu Haopu | ~1/4 页 | W4 周四 |
| ④ Project Plan & Timeline + 甘特图 | Lu Yu'an | ~1/2 页 | W4 周三 |
| ⑤ Software Attributes（软件质量属性） | Li Sihang | ~1/3 页 | W4 周三 |
| ⑥ Resource Requirements（资源需求） | Yao Tianren | ~1/6 页 | W4 周三 |
| **汇总排版 + 审校** | **Liu Haopu** | — | **W4 周五前** |

---

## ① Project Overview — @You Haoyang

**你需要写 3 段话（英文），总共约 150-200 词：**

### Part A: Problem（问题重述）

描述我们要解决的核心问题。要点：

- 企业缺乏统一工具来追踪碳排放、管理垃圾分类数据、生成合规的可持续发展报告
- 目前企业依赖手动 Excel 记录，容易出错、无法可视化趋势、难以对齐联合国 SDG 目标
- 中小企业没有预算购买商业 ESG 软件

> ⚠️ **重要**：这部分必须紧扣 Moodle 上的 Problem Statement，确保每一条最低要求都被提及。如果 Problem Statement 有具体措辞，请直接引用或改写。

### Part B: Vision（愿景）

描述项目成功后的理想状态：

- 一个一站式 Web 平台，企业通过简单的数据录入即可自动计算碳足迹、统计垃圾分类回收率
- 支持自动生成月度/季度/年度可持续发展报告，一键导出 PDF
- 支持远程浏览器访问，教授可在爱尔兰直接测试

### Part C: Benefits（收益）

列出 4-5 条具体好处：

- 减少人工统计时间（自动计算碳排放量 = 活动值 × 排放因子）
- 提高数据准确性（数据库约束 + 标准排放因子）
- 数据可视化（ECharts 趋势图、饼图、柱状图）
- 自动对齐 SDG 目标（SDG 9/11/12/13）
- 支持 PDF 导出，便于企业合规汇报

### 参考资料
- Moodle 上的 Problem Statement（必读）
- 项目 `README.md` 中的 Core Modules 部分

---

## ② Deliverables — @Yao Tianren

**你需要写一个交付物清单（英文），每条一句话描述，约 80-100 词：**

列出项目最终交付的所有产品：

1. **Web Application** — 功能完整的企业可持续发展管理平台（碳排放追踪 + 垃圾管理 + 报告生成），支持浏览器访问
2. **Database** — MySQL 数据库（10 张表 + 2 个视图）及数据库设计文档
3. **Source Code Repository** — GitHub 仓库，包含完整源代码、提交历史和分支管理
4. **User Manual** — 用户操作手册，包含系统功能说明和操作截图
5. **Test Report** — 测试报告，包含功能测试、集成测试结果和缺陷记录
6. **Deployment Guide** — 部署文档，包含虚拟机环境配置和远程测试指南

---

## ③ Success Criteria (SMART) — @Liu Haopu

> 这部分由我来写，其他人不需要管。

写 5 条符合 SMART 原则的成功标准：

| # | Success Criterion | S | M | A | R | T |
|---|---|---|---|---|---|---|
| SC1 | 在第 8 周前完成后端全部 22 个 API 的开发，通过 Postman 集成测试 | ✓ | ✓ | ✓ | ✓ | ✓ |
| SC2 | 在第 12 周前完成前端 5 个业务页面并集成 ECharts 可视化，在 Chrome/Firefox 正常显示 | ✓ | ✓ | ✓ | ✓ | ✓ |
| SC3 | 在第 14 周前部署到大学虚拟机，教授可从爱尔兰远程浏览器访问并测试 | ✓ | ✓ | ✓ | ✓ | ✓ |
| SC4 | 系统支持 2 种角色权限控制，密码哈希加密存储，所有 API 需认证后访问 | ✓ | ✓ | ✓ | ✓ | — |
| SC5 | 报告模块支持月/季/年三种周期，自动汇总数据并导出 PDF | ✓ | ✓ | ✓ | ✓ | — |

---

## ④ Project Plan & Timeline — @Lu Yu'an

**你需要写 2 部分（英文），总共约 200-250 词 + 一张甘特图：**

### Part A: Development Methodology（开发方法，2-3 句话）

参考以下内容改写：

> We adopt an **incremental development** approach, dividing the project into 6 Work Packages (WP1–WP6) delivered sequentially. Each WP has a designated Manager responsible for quality and deadlines. Progress is tracked via GitHub branches and weekly team meetings.

### Part B: Gantt Chart（甘特图）

用以下数据画一张甘特图。推荐工具：**draw.io**（免费）/ Excel / Google Sheets / Mermaid。

| Work Package | Task | Start | End | Manager |
|---|---|---|---|---|
| WP1 Requirements & Design | 需求分析、架构设计、提案 | W1 | W5 | You Haoyang |
| WP2 Backend Development | 数据库设计、Flask API 开发 | W4 | W9 | Liu Haopu |
| WP3 Frontend Framework | 基础组件、页面布局、路由 | W6 | W10 | Li Sihang |
| WP4 Frontend Modules | 碳追踪/垃圾管理/报告页面 | W8 | W12 | Li Sihang |
| WP5 Integration & Testing | 集成测试、性能优化、部署 | W12 | W16 | Lu Yu'an |
| WP6 Documentation & Delivery | 用户手册、演示、答辩准备 | W15 | W18 | Liu Haopu |

**里程碑（在甘特图上标注）：**
- **M1 (W5)**: Design documents finalized
- **M2 (W9)**: Backend development complete
- **M3 (W9)**: Mid-term review
- **M4 (W12)**: Frontend development complete
- **M5 (W16)**: Platform deployed and remotely accessible
- **M6 (W18)**: Final delivery and presentation

> ⚠️ 甘特图是**重要的加分项**，请务必做好。最终输出为图片（PNG/SVG），我会插入到提案 PDF 中。

### 参考资料
- 项目文件 `docs/TEAM_SYNC_W3.md` 中的时间线部分
- `Group_9_Five Guys.docx` 中的 WP 描述

---

## ⑤ Software Attributes — @Li Sihang

**你需要针对以下 8 个属性，每个写 1-2 句话（英文），总共约 150-200 词：**

| 属性 | 写什么 | 参考要点 |
|---|---|---|
| **Functionality** | 平台覆盖哪些功能 | 碳追踪、垃圾管理、报告生成三大模块，22 个 REST API |
| **Performance** | 如何保证响应速度 | 前端 ECharts 渲染、MySQL 索引优化查询、CDN 加载静态资源 |
| **Maintainability** | 代码如何易于维护 | Flask Blueprint 模块化架构、前后端分离、代码注释和文档 |
| **Reliability** | 如何保证稳定性 | 数据库外键约束保证数据完整性、API 统一错误处理返回标准 JSON |
| **Security** | 如何保护数据安全 | Werkzeug 密码哈希、Session 认证、角色权限控制、SQL 参数化防注入 |
| **Efficiency** | 如何高效利用资源 | 数据库连接池复用、Bootstrap/ECharts 使用 CDN 减少服务器负载 |
| **Usability** | 用户体验如何 | Bootstrap 响应式布局、直观的表单和图表、测试账号一键体验 |
| **Remote Testing** | 如何支持远程测试 | 部署到大学虚拟机，提供公网 URL + 测试账号 + 操作手册 |

### 参考资料
- 项目 `README.md` 和 `README_CN.md`
- 直接运行项目体验（参考 `docs/DATABASE_SETUP_GUIDE.md`）

---

## ⑥ Resource Requirements — @Yao Tianren

**和 ② 一起写，总共约 80-100 词：**

### Team（团队）

| Member | Role |
|---|---|
| You Haoyang | Requirements Analyst & WP1 Manager |
| Liu Haopu | Technical Lead, Backend Developer & WP2/WP6 Manager |
| Li Sihang | Frontend Developer & WP3/WP4 Manager |
| Lu Yu'an | QA Engineer, Deployment & WP5 Manager |
| Yao Tianren | Backend Contributor & Repository Manager |

### Technology Stack（技术栈）

- **Backend**: Python 3.10+, Flask 3.x
- **Database**: MySQL 8.0+
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, ECharts 5
- **PDF Export**: ReportLab
- **Version Control**: Git + GitHub
- **Deployment**: University-provided Virtual Machine (Linux)

### Cost（成本）

> All tools and frameworks used are open-source and free. Hosting is provided by the university's virtual machine infrastructure. No additional budget is required.

---

## 文件命名与提交

### 各人初稿文件名

| 负责人 | 文件名 |
|---|---|
| You Haoyang | `docs/proposal_part1_overview.md` |
| Yao Tianren | `docs/proposal_part2_deliverables.md`（含 Part 6 Resource） |
| Liu Haopu | `docs/proposal_part3_criteria.md` |
| Lu Yu'an | `docs/proposal_part4_timeline.md` + 甘特图图片 |
| Li Sihang | `docs/proposal_part5_attributes.md` |

### 提交流程

```
1. 各人写好自己的部分 → git add → git commit → git push
2. Liu Haopu 拉取所有人的内容
3. 汇总到一个文档 → 统一格式和排版 → 导出 PDF
4. 最终文件：docs/Group9_Project_Proposal.pdf
5. 上传到 Moodle
```

### Git Commit Message 示例

```
WP1: Add project overview section for proposal
WP1: Add deliverables and resource requirements for proposal
WP1: Add project timeline and Gantt chart for proposal
WP1: Add software attributes section for proposal
```

---

## 注意事项

1. **语言**：全部用英文写，语言要专业简洁，不要口语化
2. **篇幅**：控制在自己负责部分的预计篇幅内，提案总共只有 2 页
3. **Problem Statement**：You Haoyang 写 Overview 时必须参考 Moodle 上的 Problem Statement
4. **甘特图**：Lu Yu'an 的甘特图是重要加分项，请认真做
5. **截止时间**：W4 周三前把初稿推到 GitHub，Liu Haopu 周四汇总，周五提交

**有任何问题请在群里随时沟通！**
