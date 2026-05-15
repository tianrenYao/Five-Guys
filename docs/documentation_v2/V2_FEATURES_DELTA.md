# v2 Feature Delta — vs. v1 baseline

> 系统文档需要把这些新功能写进去（架构图、数据流、模块说明、API 列表）。用户文档已覆盖（仅业务侧描述），系统文档需补技术侧细节。
>
> **事实来源**：`README.md`、`FEATURES.md`、`backend/` 源码、`database/migrations/`。本文件是给 AI 看的速查清单，写系统文档时请回到源码或 FEATURES.md 校对细节。

---

## 1. Role-specific dashboards

新增四种角色定制的 dashboard 卡片区，位于 KPI summary 下方。

- **Store Staff** — `Open Alerts` 面板（仅本店未读告警）
- **Region Manager** — `Region Leaderboard`（按 recycling rate / YTD 碳强度排名本区域门店）
- **HQ Manager** — `Risk Watch`（高告警店、碳尖峰店、静默无数据店三栏）
- **Admin** — `System Health`（活跃用户数、今日记录数、服务状态 AI/Mail）

**系统文档需要写**：
- 后端聚合查询（在 `backend/routes/dashboard.py` 之类位置）
- 角色分支逻辑（按 `current_user.role` 决定返回哪种聚合）
- 前端渲染（哪个 template，哪段 JS 拉数据）

---

## 2. Navigation grouping (折叠侧边栏)

侧边栏 11 个模块按业务分四组：

- **Reporting** — Dashboard, Reports, Compliance Score
- **Operations** — Carbon Tracking, Waste Management, Training
- **Governance** — Alerts, Anomaly Detection, ESG Management
- **Admin** — User Management, Audit Log

每组可折叠，状态用 `localStorage` 持久化。

**系统文档需要写**：
- 角色 → 可见模块映射表
- 折叠状态持久化机制（前端）

---

## 3. AI / Template toggle for Reports (Dual evaluation path)

报告生成页有 `Use AI to generate evaluation` 开关：

- **AI 模式**：调用 DeepSeek 生成 ESG 分析
- **Template 模式**：使用确定性规则模板
- **降级机制**：AI 不可用时静默 fallback 到 template，并在结果上明确标注来源（`comment_source` 字段）

涉及表字段：`report.comment_source ENUM('ai', 'template')`。迁移脚本：`database/migrations/add_report_comment_source.sql`。

后端：`backend/routes/report.py` 中 `use_ai` 参数 + 重新生成 endpoint。
前端：`frontend/static/js/report.js` 的 evaluation source badge。
PDF 模板：`frontend/templates/pdf/report_template.html` 根据 `comment_source` 条件渲染标题。

**系统文档需要写**：
- 数据流图（前端表单 → 后端路由 → AI/Template 分支 → 持久化 → 重新生成）
- 降级策略与可观测性
- 字段定义与迁移

---

## 4. OCR-assisted bill scanning

Carbon Tracking 表单的 `Scan Bill` 按钮接受 utility-bill 图片或 PDF，OCR 解析后自动预填 category / activity value / date / note。

- **实现**：`backend/routes/ocr.py`，依赖 `pytesseract` + `Pillow` + `pdfplumber`（可选）
- **Mock 回退**：未安装 Tesseract 时返回逼真的 Mock 字典，仍能演示完整 UI 流程
- **Demo Bill 按钮**：直接渲染一张预置的 CityGrid Energy 英文电费账单（13,500 kWh / 2026-03），用于没有真实账单的演示场景
- **字段映射**：电费 → electricity / kWh；燃气 → fuel / m³；交通票据 → transport / km

**系统文档需要写**：

- OCR 服务调用栈（Tesseract → 正则提取 → 字段映射）
- 检测 Tesseract 安装状态并选择真实/Mock 路径的逻辑
- 预填字段映射表与失败处理

---

## 5. ESG Governance (Supplier + Policy)

新增两块独立的治理资产管理：

- **Supplier ESG**：供应商主数据 + 多维度 0/50/100 评分（Carbon / Waste / Ethics / Reporting 等）+ 自动算总分和等级
- **Company Policy**：内部政策文档库，含 title / category / status / effective date / version / content / detail view

**系统文档需要写**：
- 两张表的字段
- 评分聚合逻辑（dimension scores → overall grade）
- 权限：仅 HQ Manager / Admin

---

## 6. Alert threshold configuration & Email notification

Alerts 页面对 HQ Manager 开放 threshold 配置：metric type / condition / threshold value / scope / notification email。Region Manager 只能 review log。

- **触发时机**：每次新增 carbon 或 waste 记录后自动检查所有活跃阈值
- **支持指标**：waste recovery rate (%)、carbon MoM growth (%)、daily waste weight (kg)
- **未读角标**：侧边栏 + 顶栏 Alerts 项显示未读数红角标，前端 JS 每 60 秒轮询刷新
- **邮件模块**：`backend/utils/mail.py` 基于 Flask-Mail，主题示例 `[ESG Alert] Waste Recovery Rate threshold breached — Beijing Chaoyang Store`
- **降级**：未配置 `MAIL_SERVER` 时把完整邮件内容写入 server log（demo 环境的可观测性）
- **当前 SMTP**：Mailtrap sandbox（`sandbox.smtp.mailtrap.io`），便于演示

**系统文档需要写**：

- 阈值表结构 + 索引设计
- 告警触发完整数据流（数据写入 → 规则匹配 → 写 alert log → 触发邮件 → badge 刷新）
- 邮件发送降级策略与日志格式
- 60 秒轮询的前端实现

---

## 7. Anomaly Detection (两阶段架构)

页面 `/admin/anomaly-detection`，仅 admin / hq_manager / region_manager 可访问。

- **统计层**：按 category 分组计算 Z-score；阈值可选 1.5\u03c3 / 2.0\u03c3 / 2.5\u03c3 / 3.0\u03c3。叠加硬规则（碳排 ≤ 0、回收量 > 总重量等）
- **AI 层**：对每个 category 的 Top-3 异常调用 DeepSeek 生成三段式分析：Likely Cause / Risk Category / Recommended Actions + 一句话整体 Finding
- **持久化 Review 工作流**：所有异常写入 `anomaly_review` 表；人工可标记为 Open / Reviewed / False Positive / Resolved，跨次检测保留
- **Top-3 集中展示**：每个 category 前 3 行橙色高亮 + 可展开 AI 详情；超出 Top-3 的旧 AI 数据在下次 AI 调用时自动清理
- **性能**：LLM 输出上限 700 tokens、每条 ~35 词、预计 6-10 秒；DeepSeek 不可用时回退确定性模板
- **UI**：固定高度 480 px 内滚动面板 + Sticky 表头 + 折叠/展开箭头 JS 切换

**系统文档需要写**：

- 两阶段架构图
- `anomaly_review` 表 schema 与状态机
- DeepSeek API 集成与降级路径
- Top-3 集中展示的去重逻辑

---

## 7b. Geographic Visualization Map (新增)

页面 `/map`，所有登录角色可访问，按 `get_accessible_store_ids()` 过滤。

- **底图**：Leaflet 1.9.4 + MarkerCluster + Heat 插件
- **Tile providers**：AutoNavi (中国, 含卫星)、CartoDB Light、OpenStreetMap，可切换
- **左侧栏**：Map Overview KPIs (regions / stores / open alerts / total carbon YTD / tree-offset equiv)、Quick Search、View Mode (Stores ↔ Regions)、Carbon Heatmap toggle、Color By selector (grade / carbon / recovery / alerts)、Filters (grade × region)、Stores Needing Attention Top-N 排行
- **标记着色规则**：
  - 绿色：表现良好
  - 琥珀：回收率偏低 OR 碳排偏高
  - 红色：未读预警 ≥ 3 OR 回收率 < 30%
- **区域聚合**：按 region 计算质心 + 汇总碳排/预警，渲染为大圆 marker
- **后端**：`backend/routes/map.py`，主端点 `/api/map/stores` 返回 geocoded stores + carbon YTD + recovery rate + alert count
- **数据要求**：`store` 表需有 `latitude` / `longitude` 字段；没有坐标的门店不参与渲染

**系统文档需要写**：

- Leaflet 依赖、tile provider 选择策略（境内 AutoNavi 优先）
- ESG grade 着色的具体阈值
- 区域聚合算法（质心计算 + 汇总）
- 与 Dashboard / Anomaly 页面在数据语义上的关系

---

## 8. Audit Log

记录用户/角色/动作/对象/详情/IP/时间，HQ + Admin 可筛选查阅。

**系统文档需要写**：
- 表结构、写入触发点（哪些操作会落 audit log）
- 保留策略
- 检索过滤设计

---

## 9. CSV bulk import / export

支持运营记录批量导入导出。

**系统文档需要写**：
- 支持哪几类数据
- 校验规则（必填字段、格式、跨字段一致性）
- 错误反馈方式

---

## 10. 218-store demonstration dataset + 7-phase backfill

预置 218 家门店（6 家 seed + 212 家由 `database/generate_stores.py` 生成），跨区域分布。

**四类工程化测试组**：

- **spike stores** — 单条巨大 carbon 记录
- **silent stores** — 近期无提交，触发 data-gap 告警
- **high-alert stores** — 多次阈值触发
- **outlier stores** — 回收比异常

**回填工具 `database/backfill_recent_data.py` 的 7 个 phase**（完全幂等，可反复执行）：

1. Phase 1 — 把已有的 4 月 1-7 日 partial 数据 ×4 升级为全月（note 加 `(full)` 标记防重复）
2. Phase 2 — 5 月 / 6 月 carbon + waste 全店覆盖（避开 silent 店、跳过已存在 `(store, date)`）
3. Phase 3 — 5 条 ANOMALY 标记的离群电力记录（≈ 6× baseline）
4. Phase 4 — 8 家店各 3-5 条未读预警（指标轮换：回收率 / 碳排尖峰 / 能耗 / 用水）
5. Phase 5 — 12 条 Sustainability Report（store / region / company 三种 scope 混合）
6. Phase 6 — Apr-28 waste 全店补缺，保证 4 月回收率可计算
7. Phase 7 — 5 家 spike 店在 5 / 6 月各加 1 条 `BACKFILL_PEAK` 高负载电力记录

**命令行参数**：`--from / --to / --seed / --dry-run / --purge-recent / --inject-*`

**回滚**：`python3 database/backfill_recent_data.py --purge-recent`

**系统文档需要写**：

- 测试组定义与样本量
- 7-phase 流程图与幂等性保证机制（note 标记 + `(store_id, date)` 去重集合）
- 数据生成脚本与 schema seed 的关系

---

## 11. User Management

页面 `/admin/users`，`admin` 平台级，`hq_manager` 仅管本公司。

- summary cards（按角色统计） + 全用户表 + 行内编辑
- 创建 / 改 role / 改 region / 改 store / 启用-停用 / 重置密码 / 删除
- 密码使用 `werkzeug` pbkdf2 哈希
- 禁止删除当前登录账户（防自删）
- 所有操作写入 `audit_log`（CREATE / UPDATE / DELETE + IP + 操作人）

**系统文档需要写**：

- 权限矩阵（4 角色 × N 操作 真值表）
- pbkdf2 参数 / 盐策略
- 软删除 vs 硬删除（当前是硬删除）
- audit log 自动写入的 hook 位置

---

## 12. CSV / Excel bulk import & export

位置：carbon 和 waste 工具栏。

- **导出**：`/api/carbon/export-csv`、`/api/waste/export-csv`，与列表共用过滤参数（store_id / date_from / date_to）
- **导入**：`/api/carbon/import`、`/api/waste/import`，pandas 解析 CSV / Excel
- **模板下载**：`/api/carbon/import-template`
- **错误反馈**：行级错误回显（`Row 5: Store XX not found`）
- **审计**：批量结果（成功/失败计数）写入 audit_log

**系统文档需要写**：

- 上传文件大小限制、超时设置
- Excel 与 CSV 的解析路径差异
- 校验规则表（必填字段 / 跨字段一致性）
- 行级错误格式与前端显示

---

## 13. SDG 12 alignment panel

Dashboard 上的独立 panel，显示与 SDG 12 (Responsible Consumption and Production) 对齐的指标。

- **现状**：UI panel 已落地，`company_sdg` 表已就绪
- **未完成**：SDG 进度追踪 UI（数据库表存在但前端尚未做）

**系统文档需要写**：

- `company_sdg` 表 schema
- 现有 panel 渲染逻辑
- 计划中的进度追踪 UI（标 future work）

---

## 14. Compliance Score (ESG scorecard)

页面 `/compliance`，管理 / 总部 / 区域经理可见。

- **综合 0-100 分，5 个维度加权**：
  - 碳管理 30（数据完整性 + 平均强度）
  - 废弃物与回收 25（回收率 + 门店覆盖率）
  - 员工培训 20（覆盖率 + 人均时长）
  - 报告频率 15（年度生成报告数，目标 4）
  - 预警处理 10（已解决预警 / 总预警）
- **等级**：A / B / C / D / F，带彩色徽标
- **明细**：per-维度展开，显示各 metric 的实际值 vs 目标值

**系统文档需要写**：

- 5 维度 + 各 sub-metric 的计算公式
- 权重设计依据（引用 GRI / ISO 14064 / TCFD?）
- 等级分界点

---

## 系统文档章节映射建议

| 新功能 | 建议写入系统文档章节 |
|---|---|
| 1 Role-specific dashboards | §3.3 Frontend Layouts / §3.5 API |
| 2 Navigation grouping | §3.3 Frontend |
| 3 AI / Template toggle | §3.10 LLM Integration（B4 合并精简） |
| 4 OCR scan-bill | §3.10 或新 §3.10.2 |
| 5 ESG Governance | §3.6 / §3.7 Data Models |
| 6 Alert threshold | §3.8 |
| 7 Anomaly Detection | §3.9 |
| 7b Geographic Map | §3.3 Frontend 或新增 §3.12 |
| 8 Audit Log | §3.6 Data Models |
| 9 CSV import/export | §3.5 API |
| 10 Demo dataset + backfill | §3.11 (新增，B5) |
| 11 User Management | §3.6 / 权限章节 |
| 12 CSV import/export | §3.5 API |
| 13 SDG panel | §3.3 Frontend |
| 14 Compliance Score | §3.7 算法章节 |

---

## 测试章节（B6）需要覆盖

REVISION_TODO B6 要求新增 §4 Testing Strategy，至少 1.5 页：

- 测试金字塔（unit / integration / e2e）实际比例
- 单元测试：哪些模块覆盖、用什么框架（pytest? unittest?）
- 集成测试：API 测试方式
- 探索式测试（cite Bach）+ ISTQB 框架引用
- SUS 可用性问卷（cite Brooke）— 用户文档没写，但系统文档要提
- 已知缺陷与已修复缺陷清单
