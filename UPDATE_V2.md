# 功能更新说明 v2.0

> **Group 9 – Five Guys** | 更新日期：2026 年 4 月
> 本文档覆盖 v2.0 迭代中新增的全部功能及对应的测试方法。

---

## 总览：本次新增功能

| # | 功能 | 涉及页面 | 角色要求 |
|---|---|---|---|
| 1 | 预警邮件通知（Flask-Mail + Mock fallback） | Alerts | hq_manager / admin |
| 2 | 碳/废弃物记录编辑（24 h 撤回限制） | Carbon / Waste | 全部登录用户 |
| 3 | 数据横向对比（本月 vs 上月 / 本店 vs 区域均值） | Carbon / Waste | 全部登录用户 |
| 4 | 供应商 ESG 评估模块 | /supplier | 查看：全员；编辑：hq_manager / admin |
| 5 | ESG 政策管理 | /policy | 查看：全员；编辑：hq_manager / admin |

---

## 功能 1 — 预警邮件通知

### 功能说明

- 每次触发预警时，系统自动向阈值配置中填写的 `notify_email` 发送邮件。
- 若未配置 SMTP（`.env` 中 `MAIL_SERVER` 为空），自动切换为 **Mock 模式**：邮件内容打印到服务器终端，不实际发送，适合无网络的 VM 演示。
- 支持多个收件地址（逗号分隔）。

### 测试步骤

**Mock 模式测试（无需 SMTP）：**

1. 以 `test_business`（密码 `123456`）登录
2. 左侧导航 → **Alerts**
3. 在 "Alert Thresholds" 表格中找到任意阈值，或点击 **+ Add Threshold** 新增一条：
   - Metric Type：`waste_recycling_rate`
   - Direction：`below`
   - Threshold：`99`（故意设置极高，确保触发）
   - Notify Email：`demo@test.com`（任意地址）
   - Scope：Company
4. 保存后，前往 **Waste Management** 添加一条废弃物记录（回收率低于 99%）
5. 回到终端，查看服务器日志，应看到：
   ```
   [Mail MOCK] Would send to=['demo@test.com'] | Subject: [ESG Alert] waste_recycling_rate ...
   ```

**真实邮件测试（配置 Mailtrap）：**

1. 在 `.env` 中填写 Mailtrap SMTP 配置（见 SETUP.md）
2. 重启服务器
3. 重复上述步骤 3–4
4. 登录 [mailtrap.io](https://mailtrap.io) → Sandboxes → 你的 inbox → 查看收到的邮件

---

## 功能 2 — 记录编辑与撤回

### 功能说明

- 碳排和废弃物记录表格中每行新增 **✏️ 编辑** 按钮，点击弹出编辑 Modal。
- 可修改字段：日期、数值、备注。
- **角色限制**：
  - `store_staff`：仅能编辑/删除 **24 小时内** 创建的记录，超时后按钮操作会返回错误提示。
  - `hq_manager` / `region_manager` / `admin`：不受时间限制。

### 测试步骤

**编辑功能：**

1. 登录 → **Carbon Tracking**
2. 表格中任意一行，点击 **✏️（铅笔图标）** 按钮
3. 修改 Activity Value（如改为 `500`），点击 **Save Changes**
4. 表格自动刷新，数值已更新

**24 小时限制测试（需 store_staff 账号）：**

1. 以 `test_staff`（密码 `123456`）登录
2. 对一条超过 24 小时前的旧记录点击 ✏️ 编辑，保存后应提示：
   ```
   Edit not allowed: more than 24 hours have passed
   ```
3. 对刚刚新建的记录，编辑和删除均正常

---

## 功能 3 — 数据横向对比

### 功能说明

- 碳排和废弃物页面右上角新增 **Compare** 按钮。
- 弹窗展示三个 KPI 卡片：
  - **This Month**：本月该门店/公司的碳排或废弃物总量
  - **Last Month**：上月数据 + 环比变化百分比（▲ 红色 = 增加，▼ 绿色 = 降低）
  - **Region Avg**：本月所在区域所有门店的平均值，并标注本店高于/低于区域均值

### 测试步骤

1. 登录 → **Carbon Tracking**
2. 点击右上角 **Compare** 按钮
3. 弹窗显示三列对比卡片
4. 若以区域经理登录，可先在筛选栏切换不同门店，再点 Compare 查看各门店数据
5. **Waste Management** 页面同理

---

## 功能 4 — 供应商 ESG 评估

### 功能说明

- 新页面：左侧导航 → **Supplier ESG**（路径 `/supplier`）
- 对供应链合作商进行四维 ESG 打分（0–100 分）：
  - 碳管理（Carbon Score）
  - 废弃物回收能力（Waste Score）
  - 社会责任/伦理（Ethics Score）
  - 可持续报告（Reporting Score）
- 系统自动计算 **综合等级（A / B / C / D / F）**：
  - A：均分 ≥ 85；B：≥ 70；C：≥ 55；D：≥ 40；F：< 40
- 页面顶部显示各等级供应商数量汇总卡片
- 每列分数显示进度条（绿色 ≥ 70 / 橙色 ≥ 50 / 红色 < 50）
- 已预置 5 条演示供应商数据

### 测试步骤

**查看：**

1. 任意账号登录 → 左侧 **Supplier ESG**
2. 顶部看到 A/B/C/D/F 各等级数量统计
3. 表格展示 5 家供应商（GreenBean Co.、EcoPack Ltd. 等）的评分和等级

**新增供应商（需 hq_manager 账号）：**

1. 以 `test_business` 登录
2. 右上角 **Add Supplier**
3. 填写名称（必填）、分类、国家、四项评分（0–100）、备注
4. 保存后表格刷新，等级自动计算显示

**编辑/删除：**

1. 表格末列点击 ✏️ 或 🗑️

---

## 功能 5 — ESG 政策管理

### 功能说明

- 新页面：左侧导航 → **ESG Policies**（路径 `/policy`）
- 双栏布局：左侧政策列表，右侧全文展示 / 编辑器
- 政策分类：SDG 12、环境（Environment）、社会（Social）、治理（Governance）、其他
- 状态管理：草稿（Draft）→ 生效（Active）→ 归档（Archived）
- 支持版本号管理和生效日期设置
- 已预置 3 条演示政策

### 测试步骤

**查看政策：**

1. 任意账号登录 → 左侧 **ESG Policies**
2. 左侧列表点击任意政策，右侧显示全文内容、版本、状态、生效日期

**新建政策（需 hq_manager 账号）：**

1. 以 `test_business` 登录
2. 左侧列表右上角点击 **New**
3. 填写标题（必填）、分类、状态、版本、生效日期
4. 在内容框输入政策正文（支持 Markdown 格式）
5. 点击 **Save** → 左侧列表自动刷新并显示新政策

**编辑已有政策：**

1. 在右侧详情页面点击 **Edit** 按钮
2. 修改内容后点击 Save

---

## 演示账号（密码均为 `123456`）

| 用户名 | 角色 | 可访问范围 | 适合演示功能 |
|---|---|---|---|
| `test_business` | 总部 ESG 经理 | 全部 6 家门店 | 所有功能（含编辑供应商/政策） |
| `test_region` | 华北区域经理 | 北京朝阳 + 北京海淀 | 区域数据对比 |
| `test_staff` | 门店员工 | 仅北京朝阳店 | 24 小时撤回限制演示 |

---

## 注意事项

- **供应商 ESG 和 ESG 政策**：若数据库迁移尚未运行，页面自动显示 Mock 演示数据，顶部会有蓝色提示横幅。运行 `python3 database/run_migrations.py` 后切换为真实数据库。
- **邮件通知**：Mock 模式下无需任何配置，邮件内容输出到终端；真实发送需配置 `.env` 中的 `MAIL_*` 变量。
