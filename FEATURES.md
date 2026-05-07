# 企业可持续发展管理平台 — 功能概览

> **Group 9 – Five Guys** | Flask + MySQL + Bootstrap + ECharts
> 演示企业：**瑞幸咖啡（Luckin Coffee）** | 3 个区域，共 6 家门店

---

## ✅ 已完成功能

### 1. 用户认证

- 基于 Session 的登录 / 登出
- 四级角色体系：`admin`（平台管理员）→ `hq_manager`（总部ESG经理）→ `region_manager`（区域经理）→ `store_staff`（门店员工）
- 每个角色只能看到自己权限范围内的数据（公司 / 区域 / 门店）

### 2. 数据看板（Dashboard）

- KPI 概览卡片：总碳排放量、总废弃物量、回收率、活跃门店数
- 月度碳排放趋势折线图（ECharts）
- 废弃物类别分布饼图（ECharts）
- 各区域碳排放对比柱状图（ECharts）
- 所有图表根据当前登录用户的可访问门店自动过滤

### 3. 碳足迹追踪

- 按门店添加 / 删除碳排放记录
- 排放类别：电力（electricity）、交通（transport）、燃料（fuel）
- 内置排放因子库（基于 IPCC / 中国生态环境部 / DEFRA 2023 数据预置）
- 自动计算 CO₂e：活动量 × 排放因子
- 总部/区域经理可切换门店查看
- 支持日期范围筛选
- **扫描账单（OCR）**：上传水电费账单图片或 PDF，自动填入类别、用量、日期、备注

### 4. 废弃物管理

- 按门店添加 / 删除废弃物记录
- 废弃物类别：纸杯盖、塑料包装、咖啡渣、食物残渣、危险废物、普通垃圾、纸板/纸张、电子废物
- 字段：来源类型、产生重量（kg）、回收重量（kg）、处置方式、处置单位
- 月度废弃物统计柱状图 + 回收率折线（ECharts）
- 支持多门店切换和日期范围筛选

### 5. 预警系统

- **阈值配置**（仅 hq_manager 可操作）：设置指标类型、触发方向、阈值数值及作用范围（公司 / 区域 / 门店）
- 支持的指标：废弃物回收率（%）、碳排放环比增长率（%）、日废弃物产生量（kg）
- **自动触发**：每次新增碳排或废弃物记录后自动检查并写入预警日志
- **预警日志**：展示所有触发记录（门店、指标、实际值 vs 阈值、触发时间）
- **未读角标**：侧边栏和顶栏显示未读预警数量红色角标，每 60 秒自动刷新
- 支持单条或一键全部标为已读

### 6. 可持续发展报告

- 可生成月度 / 季度 / 年度 / 自定义时间段的报告，范围支持门店 / 区域 / 全公司
- 报告内容：碳排 KPI 汇总、废弃物 KPI 汇总、主要排放来源、回收率趋势
- AI 评论字段（DeepSeek 接口占位，待接入 API Key）
- **导出 PDF**：WeasyPrint HTML 转 PDF，包含排版、KPI 表格、SDG 对齐章节
- 列表页展示报告状态（草稿 / 已生成 / 已导出）

### 7. 账单 OCR 演示

- 碳追踪页面提供"扫描账单"按钮，可上传电费/燃气账单图片或 PDF
- 若安装了 `tesseract`：执行真实 OCR，通过正则提取字段
- 若未安装：返回逼真的 **Mock 数据**，演示完整交互流程
- "Demo Bill"按钮可预览预渲染的英文电费账单（CityGrid Energy，13,500 kWh，2026年3月）
- 识别字段：排放类别、活动量（kWh / m³ / km）、记录日期、备注

### 8. 基于角色的访问控制（RBAC）

- 所有 API 端点均加有 `@login_required` 和 `@role_required` 装饰器
- 门店级数据隔离：`get_accessible_store_ids()` 对所有查询按 Session 范围过滤
- 侧边栏导航项根据角色动态显示/隐藏

### 9. AI 数据异常检测 [NEW]

- 页面：`/admin/anomaly-detection`，仅 `admin` / `hq_manager` / `region_manager` 可访问
- **两阶段架构**：
  - 统计层：按类别分组的 Z-score 偏离检测（阈值可调 1.5σ / 2.0σ / 2.5σ / 3.0σ）+ 硬规则校验（碳排 ≤ 0、回收量 > 总重量等）
  - AI 层：DeepSeek LLM 为**每个类目的 Top 3 异常**生成三段式分析（Likely Cause / Risk Category / Recommended Actions）+ 一句话整体 Finding
- **持久化 Review 工作流**：所有异常写入 `anomaly_review` 表；人工可标记为 Open / Reviewed / False Positive / Resolved，跨次检测保留
- **Top 3 集中展示**：每个栏目只有前 3 行带橙色高亮 + 可展开的 AI 详情；超出 Top 3 的旧 AI 数据会在下次 AI 调用时自动清理
- **性能控制**：LLM 输出上限 700 tokens、每条约 35 词、预计 6-10 秒；DeepSeek 不可用时自动回退到确定性模板
- UI：固定高度 480px 的内滚动面板 + Sticky 表头 + 折叠/展开箭头 JS 切换

### 10. ESG 合规评分 [NEW]

- 页面：`/compliance`，管理/总部/区域经理可见
- 综合 0-100 分，分 5 个维度加权：
  - 碳管理（30）：数据完整性 + 平均强度
  - 废弃物与回收（25）：回收率 + 门店覆盖率
  - 员工培训（20）：覆盖率 + 人均时长
  - 报告频率（15）：年度生成报告数，目标 4
  - 预警处理（10）：已解决预警 / 总预警
- 输出等级 A / B / C / D / F，带彩色徽标和 per-维度明细

### 11. 地理可视化地图 [NEW]

- 页面：`/map`，支持所有已登录角色（按可访问门店过滤）
- Leaflet 渲染门店标记，按 ESG 表现自动上色：
  - 绿色：表现良好
  - 琥珀：回收率偏低或碳排偏高
  - 红色：未读预警 ≥ 3 或回收率 < 30%
- 区域层级聚合：按 region 计算质心 + 汇总碳排/预警
- 标记弹窗显示 YTD 碳排、废弃物回收率、未读预警数

### 12. 供应商 ESG 评估 [NEW]

- 页面：`/supplier`，CRUD 仅 `hq_manager` / `admin`
- **4 维度 × 4 指标 = 16 项打分卡**：
  - Carbon（披露 / 目标 / 措施 / 认证）
  - Waste（政策 / 回收 / 包装 / 追踪）
  - Ethics（劳工 / 安全 / 工作条件 / 治理）
  - Reporting（报告 / 完整性 / 频率 / 验证）
- 每项 0 / 50 / 100 分，加权聚合得 Overall Grade（A-F）
- 无数据时自动回退到 5 条 Mock 供应商（GreenBean Co. / EcoPack Ltd. 等）便于演示

### 13. ESG 政策管理 [NEW]

- 页面：`/policy`，CRUD 仅 `hq_manager` / `admin`
- 字段：标题、类别（sdg12 / environment / governance / …）、版本号、生效日期、状态（active / draft / archived）、Markdown 正文
- 无数据时回退到 3 条 Mock 政策（Responsible Consumption / Carbon Reduction Roadmap / Supplier Code of Conduct）

### 14. 员工可持续发展培训 [NEW]

- 页面：`/training`，所有登录用户可记录，删除权限限制为经理
- 记录字段：课程名、课程类型（6 类：碳意识 / 废弃物管理 / 能效 / 可持续报告 / 绿色采购 / Other）、门店、受训人、时长、分数、完成日期、状态
- 年度统计卡：总场次、总学时、唯一受训人、平均分，按课程类型分组
- 所有创建/删除记录写入 `audit_log`

### 15. 管理员用户管理 [NEW]

- 页面：`/admin/users`，`admin` 平台级、`hq_manager` 仅管本公司
- 功能：创建用户、改 role / region / store 归属、启用/停用、重置密码、删除
- 密码使用 `werkzeug` pbkdf2 哈希；禁止删除当前登录账户
- 所有操作写入 `audit_log`（CREATE / UPDATE / DELETE + IP + 操作人）

### 16. 审计日志查看 [NEW]

- 页面：`/admin/audit-log`，`admin` 看全平台，`hq_manager` 只看本公司
- 筛选：action（CREATE/UPDATE/DELETE 等）、target_type、起止日期、最多 500 行
- 额外 API `/api/audit/stats` 提供近 7 天各 action 的计数柱状图数据
- 数据源：`audit_log` 表，由各模块关键操作自动写入

### 17. 邮件通知 [NEW]

- 模块：`backend/utils/mail.py`，基于 Flask-Mail
- 预警触发时自动调用 `send_alert_email()`，主题示例："[ESG Alert] Waste Recovery Rate threshold breached — Beijing Chaoyang Store"
- **Mock 回退**：未配置 `MAIL_SERVER` 时把邮件内容写入 server 日志，保证开发环境也能 demo
- 当前配置 Mailtrap sandbox（`sandbox.smtp.mailtrap.io`）方便演示

---

## 🚧 未完成 / 待实现功能

> 下表中已完成项已全部迁移到上方 ✅ 已完成功能（审计日志 / 用户管理 / 邮件通知 / AI 报告评论 均已落地）。

| 功能 | 状态 | 备注 |
|---|---|---|
| **真实 OCR** | 代码已就绪，需装 Tesseract | 未安装时自动回退 Mock 数据 |
| **SDG 进度追踪 UI** | 数据库表已就绪 | `company_sdg` 表存在，前端页面未做 |
| **CSV 导出** | 未开始 | 碳排/废弃物记录导出为 CSV |

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python 3.12 + Flask 3.x |
| 数据库 | MySQL 5.7+（PyMySQL 驱动） |
| 前端 | Bootstrap 5 + Bootstrap Icons + ECharts 5 |
| PDF 导出 | WeasyPrint + Jinja2 HTML 模板 |
| OCR | pytesseract + Pillow + pdfplumber（可选） |
| 认证 | werkzeug pbkdf2 密码哈希 + Flask Session |

## 演示账号（密码均为 `123456`）

| 用户名 | 角色 | 可访问范围 |
|---|---|---|
| `test_business` | 总部 ESG 经理 | 全部 6 家门店，全功能 |
| `test_region` | 华北区域经理 | 北京朝阳店 + 北京海淀店 |
| `test_staff` | 门店员工 | 仅北京朝阳店 |
