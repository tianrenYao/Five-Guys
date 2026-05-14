# Documentation v2 — Revision TODO

> **目的**：在保留 v1 (`docs/documentation/`) 不动的前提下，对 v2 (`docs/documentation_v2/`) 两份文档逐项修订，覆盖 v2 平台新功能并补齐符合行业规范的测试章节。
>
> **协作约定**：每完成一项 TODO 即停下，等待用户审核确认后再做下一项。审核维度 = 内容准确性 + 页数预算 + LaTeX 编译能否通过。

---

## 0. Setup（已完成）

- [x] 创建 `docs/documentation_v2/` 目录
- [x] 复制 v1 `*.tex` 与 `refs.bib`
- [x] 调整 `\graphicspath`（user.tex / system.tex）以复用 v1 的 `images/` 与 `figures/`，不重复占空间
- [ ] **首次编译验证**（用户在本地跑一次 `pdflatex -> bibtex -> pdflatex x2`，确认 v2 能复现 v1 的 PDF 形态）— **待用户确认**

---

## A. 用户文档（Group_9_user_documentation.tex，目标 ≤10 页）

> v1 当前 ≈ 9 页。预算余量 ≈ 1 页。下面 7 项做完后总页数应在 9.5–10。

### A1 · §1 Abstract — 加 v2 概览句 [HIGH] [size XS]
- **位置**：当前 .tex line 73–75
- **动作**：在 Abstract 末尾追加 1–2 句，提及"role-specific dashboards、demo dataset of 218 stores、CSV import/export、OCR-assisted bill input"
- **页数影响**：+0
- **审核点**：措辞是否与现有学术语调一致；不夸大功能

### A2 · §2.2 Test Accounts — 加 `test_admin` [HIGH] [size XS]
- **位置**：line 93–105 表格
- **动作**：表格新增一行 `testadmin / 123456 / Admin / Platform-wide administration including user mgmt and audit log`
- **页数影响**：+0（同表格内）
- **审核点**：账号字符串与实际登录页提示一致

### A3 · §2.3 Navigation — 提一句侧边栏分组 [LOW] [size XS]
- **位置**：line 108
- **动作**：在末尾加一句"Navigation items are organised into collapsible groups (Reporting / Operations / Governance / Admin) with state persisted across pages."
- **页数影响**：+0
- **审核点**：是否描述准确

### A4 · §3 Role and Feature Overview — 微调矩阵补 v2 页面 [MEDIUM] [size S]
- **位置**：line 120–134 表格
- **动作**：在 HQ Manager / Admin 行的 "Main Operational Pages" 列加上 "Risk Watch dashboard"，在 Region 行加上 "Region Leaderboard"，Store Staff 行加上 "Open Alerts panel"
- **页数影响**：+0（同表格内）
- **审核点**：与 §4.1 描述对齐

### A5 · §4.1 Dashboard — 增补"Role-Specific Cards"段 [HIGH] [size M]
- **位置**：line 139–147（Dashboard Review 子节末尾）
- **动作**：新增 1 段（约 80 词）+ 1 张组合截图（占位 placeholder，由本组成员后补）：四种角色看到的子卡片差异 — HQ Risk Watch / Region Leaderboard / Staff Open Alerts / Admin System Health
- **页数影响**：+0.3
- **审核点**：是否需要先准备 1 张 4-in-1 截图；占位待补图标记清楚

### A6 · §4 共享流程其它子节精简 [MEDIUM] [size S]
- **位置**：line 150–204（Carbon / Waste / Reports / Training 4 个子节）
- **动作**：每子节最末段砍 30–40 词冗余话（例如重复出现的 "feeds dashboards, reports, and compliance" 这类总括句保留一处即可）
- **页数影响**：−0.4 ~ −0.5
- **审核点**：精简后是否仍能让用户理解关键操作步骤

### A7 · §7 HQ/Admin Guide — Supplier+Policy 合并 [MEDIUM] [size S]
- **位置**：line 276–296
- **动作**：把 "Supplier ESG Assessment" 与 "Company Policy Management" 两子节合并为 "ESG Governance (Supplier + Policy)" 一节，文字压缩到原来的 70%；保留两张截图但改为并排小图
- **页数影响**：−0.3
- **审核点**：视觉上仍能区分两个功能

### A8 · §8（新章）Hands-On Tutorial for New Users [HIGH] [size L]
- **位置**：在 §7 末尾、§Conclusion 之前
- **动作**：全新章节，1 页：
  - §8.1 Test Environment（URL + 浏览器 + 4 个账号速查）
  - §8.2 Common Task Walkthroughs：4 角色 × 4 个常见任务的步骤化演练（小表格，每行 1 任务，列：Role / Task / Steps 1-2-3 / Expected Outcome）= 16 行
  - §8.3 Demo Data Cheat Sheet：218 stores 总数 + spike / silent / alert / outlier 各组的 store ID 提示（让新用户知道在哪能看到"有数据"的页面）
  - **不写**测试方法学、bug 模板（那些归系统文档）
- **页数影响**：+1.0
- **审核点**：表格密度是否过高；任务选择是否覆盖关键场景

### A9 · Conclusion 微调 [LOW] [size XS]
- **位置**：line 319–320
- **动作**：在末尾加一句"New users may follow Section 8 as a guided walkthrough."
- **页数影响**：+0
- **审核点**：与新增 §8 互相引用一致

### A10 · 编译 + 校页 [HIGH] [size XS]
- **动作**：pdflatex 编译，确认页数 ≤10、所有图正确显示、新加的引用没断
- **审核点**：用户本地编译验收

---

## B. 系统文档（Group_9_system_documentation.tex，目标 ≤20 页）

> v1 当前 ≈ 18–19 页。预算余量 ≈ 1.5 页。下面 9 项做完后总页数应在 19.5–20。

### B1 · §Abstract — 加 v2 概览句 [HIGH] [size XS]
- **位置**：line 79–83
- **动作**：在 Abstract 第二段末追加一句关于 v2 三项亮点：role-specific dashboards / demo data backfill tool / formal testing strategy
- **页数影响**：+0
- **审核点**：与新增 §3.3 / §3.11 / §4 的描述前后一致

### B2 · §3.3 Dashboard — 增补 Role-Specific Layouts 段 [HIGH] [size M]
- **位置**：line 187–190
- **动作**：在现有两段后追加 1 段（约 100 词）+ 小表格列出 4 个新 API：
  - `/api/dashboard/staff-view`、`/region-leaderboard`、`/risk-watch`、`/system-health`
  - 描述各自返回什么 widget 给前端
- **页数影响**：+0.3
- **审核点**：API 路径与代码 (`backend/views/dashboard.py`) 一致

### B3 · §3.10.1 Anomaly Detection — 一句 Top-3 LLM workflow [LOW] [size XS]
- **位置**：line 335 段末
- **动作**：在 Z-score + rule-based 描述后追加一句："To control LLM cost, deep AI commentary is generated only for the top-3 anomalies per category, and a persistent `anomaly_review` table tracks human triage status (Open / Reviewed / False Positive / Resolved) across runs."
- **页数影响**：+0
- **审核点**：与 `FEATURES.md §9` 描述一致

### B4 · §3.10 Advanced Functions — 合并精简 User/Audit/OCR [MEDIUM] [size S]
- **位置**：line 379–388
- **动作**：把 §3.10.2 (User Mgmt) §3.10.3 (Audit) §3.10.4 (OCR) 三段从各 1 整段缩到各 0.5 段；删除重复的 "scope-restricted" 类总括语
- **页数影响**：−0.4
- **审核点**：核心信息（密码哈希、不可变审计、OCR fallback）不丢失

### B5 · §3.11 Database/Migration/Deployment — 增补 Demo Data Generation [HIGH] [size M]
- **位置**：line 390–393
- **动作**：在现有内容后追加 1 段（约 120 词）+ 1 张表格描述 `database/backfill_recent_data.py` 的 7 个 phases；强调 idempotent + dry-run + purge-recent
- **页数影响**：+0.4
- **审核点**：phase 描述与脚本输出一致

### B6 · §4（新章）Testing Strategy and Methodology [HIGH] [size XL]
- **位置**：在 §3 Technical Implementation 末尾、§5 (原 §4) Use of Generative AI 之前
- **动作**：全新章节，1.5 页：
  - §4.1 Scope and Objectives（功能 + RBAC 边界 + 可用性，4–5 行）
  - §4.2 Internal Testing — 4 人按模块分工小表格 + 每人产出 = 用例清单 + bug 报告
  - §4.3 External Peer Testing — 三层方法学：
    - **Scenario-Based UAT**（60% 投入，4 角色 × 5 用例 = 20 条脚本，引 ISTQB FL Syllabus v4.0）
    - **Exploratory Testing with SBTM**（30% 投入，3 charters × 30-min sessions，引 Bach）
    - **System Usability Scale (SUS)**（10% 投入，10 题量表，引 Brooke 1996）
  - §4.4 Bug Tracking and Feedback Templates（2 个代码块：Bug Report 模板 + Improvement 模板）
  - §4.5 Test Deliverables（用例清单 / 缺陷日志 / SUS 汇总分 / 迭代报告）
- **页数影响**：+1.5
- **审核点**：方法学引文是否准确；模板字段是否实用；总长是否真的能压在 1.5 页

### B7 · §5 Groupwork — 5 人传记每人精简一段 [MEDIUM] [size S]
- **位置**：line 425–458
- **动作**：每人当前 3 段（角色 / 中期 / 后期），缩到 2 段（合并中期+后期）；保留"Specific contributions / Notable technical work"那段不动
- **页数影响**：−0.5
- **审核点**：每人 specific contributions 列表保留完整，不删个人成就

### B8 · §6 Conclusion — 缩短 [LOW] [size XS]
- **位置**：line 460–463
- **动作**：从 2 段缩到 1 段（约 80 词）；删除"Although there is room for future extension..."这类套话
- **页数影响**：−0.2
- **审核点**：仍能体现项目总结

### B9 · §Bibliography — 加 3 条测试方法学引文 [HIGH] [size S]
- **位置**：line 465–513
- **动作**：在现有 8 条参考文献末尾追加：
  - ISTQB, *Certified Tester Foundation Level Syllabus v4.0*, 2023.
  - J. Bach, *Exploratory Testing Explained*, 2003.
  - J. Brooke, "SUS: A Quick and Dirty Usability Scale," in *Usability Evaluation in Industry*, 1996, pp. 189–194.
- **页数影响**：+0.1
- **审核点**：引文格式与现有 IEEE-style 一致；§4 中 \cite 命令对应

### B10 · 编译 + 校页 [HIGH] [size XS]
- **动作**：pdflatex + bibtex + pdflatex x2 编译，确认页数 ≤20、目录正确、所有 \cite 解析、所有图存在
- **审核点**：用户本地编译验收

---

## C. 收尾

### C1 · 重命名 PDF 为提交规范名（最后一步）
- 提交规范：`9_user_draft.pdf`、`9_system_draft.pdf`
- 当前编译产出：`Group_9_user_documentation.pdf`、`Group_9_system_documentation.pdf`
- **建议**：编译验收完毕后，手动复制并改名（不修改 .tex 内的 Filename 字段，因为标题块仍可写"Group 9 — Five Guys"）

### C2 · 提交前检查清单
- [ ] 用户文档页数 ≤10
- [ ] 系统文档页数 ≤20
- [ ] 文件名为 `9_user_draft.pdf` / `9_system_draft.pdf`
- [ ] PDF 中所有图清晰可见、不被截断
- [ ] 所有引文标记 `[1]…[N]` 正常解析
- [ ] 测试账号在文档中与登录页提示一致（`test_admin / test_business / test_region / test_staff`，密码 `123456`）
- [ ] 由 1 名组员代表上传 Moodle（截止：第 11 周周五午夜前）

---

## 任务总览（用于状态追踪）

| ID | 任务 | 优先级 | 体量 | 页数变动 | 状态 |
|---|---|---|---|---|---|
| 0 | Setup（已完成） | — | — | — | ✅ |
| A1 | User Abstract 加 v2 句 | HIGH | XS | +0 | ✅ |
| A2 | User §2.2 加 test_admin | HIGH | XS | +0 | ✅ |
| A3 | User §2.3 加分组折叠 | LOW | XS | +0 | ✅ |
| A4 | User §3 矩阵补 v2 页面 | MEDIUM | S | +0 | ⏳ |
| A5 | User §4.1 加 Role-Specific Cards | HIGH | M | +0.3 | ⏳ |
| A6 | User §4 共享流程精简 | MEDIUM | S | −0.4 | ⏳ |
| A7 | User §7 Supplier+Policy 合并 | MEDIUM | S | −0.3 | ⏳ |
| A8 | User §8（新）Hands-On Tutorial | HIGH | L | +1.0 | ⏳ |
| A9 | User Conclusion 微调 | LOW | XS | +0 | ⏳ |
| A10 | User 编译校页 | HIGH | XS | — | ⏳ |
| B1 | System Abstract 加 v2 句 | HIGH | XS | +0 | ⏳ |
| B2 | System §3.3 加 Role-Specific Layouts | HIGH | M | +0.3 | ⏳ |
| B3 | System §3.10.1 一句 Top-3 LLM | LOW | XS | +0 | ⏳ |
| B4 | System §3.10 合并精简 | MEDIUM | S | −0.4 | ⏳ |
| B5 | System §3.11 加 Demo Data Generation | HIGH | M | +0.4 | ⏳ |
| B6 | System §4（新）Testing Strategy | HIGH | XL | +1.5 | ⏳ |
| B7 | System §5 Groupwork 精简 | MEDIUM | S | −0.5 | ⏳ |
| B8 | System Conclusion 缩短 | LOW | XS | −0.2 | ⏳ |
| B9 | System Bibliography 加 3 条 | HIGH | S | +0.1 | ⏳ |
| B10 | System 编译校页 | HIGH | XS | — | ⏳ |
| C1 | 重命名为 9_*_draft.pdf | — | XS | — | ⏳ |
| C2 | 提交前检查 | — | XS | — | ⏳ |

**图例**：⏳ pending · 🛠 in progress · ✅ done · ⚠ blocked

**预计净页数变动**：
- 用户文档：+1.3 −0.7 = **净 +0.6 页**（9 → 9.6 页，符合 ≤10 限制）
- 系统文档：+2.3 −1.1 = **净 +1.2 页**（19 → 20.2 页，**临界，B6 需严格控制 1.5 页内**）

---

## 执行建议顺序

1. **先做 A 段（用户文档）**：体量小、可快速验证 v2 setup 工作正常
2. **再做 B1–B5（系统文档增补）**：v2 新功能补齐
3. **B6 单独啃**：测试章节是最大块，建议拆成 4.1+4.2 一轮、4.3+4.4+4.5 一轮
4. **B7–B9（精简类）放最后**：最后看页数余量再精简，避免提前砍多了又得加回
5. **B10 / A10 编译验收**
6. **C 提交收尾**

> 建议每个 ⏳ 任务做完后我把 .tex diff 简要贴出，等你确认 ✅ 后我把对应行的 ⏳ 改为 ✅ 并继续下一项。

