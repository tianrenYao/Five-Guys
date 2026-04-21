# 用户文档协作说明（给继续用 AI 完善文档的队友）

这份说明文档是给继续完善 `9_user_draft.tex` 的队友使用的。

目标不是从零开始重写，而是：

- 在现有框架上继续补全
- 根据真实页面补截图
- 把“提示型草稿”逐步变成“正式提交版用户文档”
- 在需要时借助 AI 提高写作效率，但避免写错功能或权限

---

## 1. 当前相关文件说明

当前与用户文档直接相关的文件主要有这几个：

## 1.1 主文档文件

- `docs/documentation/9_user_draft.tex`

这是当前的**用户文档主文件**。

里面已经有：

- 英文正文框架
- 分角色章节结构
- 共享工作流章节
- 中文提示信息（方便队友继续写）
- 部分截图说明和写作说明

你们后续主要就是在这个文件上继续修改。

---

## 1.2 截图执行清单

- `docs/documentation/9_user_screenshot_checklist.md`

这是已经整理好的**截图执行清单**，内容包括：

- 用哪个账号截图
- 每张图优先级高不高
- 图文件命名建议
- 每张图应该截到什么范围
- 两个队友怎么分工截图

如果你们准备开始截页面图，先看这个文件。

---

## 1.3 系统文档（参考，不是本次主要修改对象）

- `docs/documentation/9_system_draft.tex`

这个文件主要是系统文档，不是用户文档。

它可以用来参考：

- 模块名称怎么统一表达
- 某些功能的正式英文说法
- 哪些功能已经确认存在

但是**不要把系统实现细节直接搬到用户文档里**。

---

## 2. 当前文档状态

目前 `9_user_draft.tex` 已经不是空架子，而是一个**详细协作底稿**：

- 正文主体是英文
- 给队友的提示信息是中文
- 结构已经较完整
- 当前编译后约 9 页

也就是说，你们后面最主要的工作不是“重新规划结构”，而是：

- 把提示型内容改写得更正式
- 把建议截图变成真实插图
- 把重复或过长的提示删掉
- 做最后的排版收尾

---

## 3. 如何编译 tex 文件

## 3.1 用户文档必须优先使用 XeLaTeX

由于 `9_user_draft.tex` 里现在包含中文提示信息，所以这份文档目前应该用：

```bash
xelatex -interaction=nonstopmode -halt-on-error 9_user_draft.tex
```

运行目录：

```bash
docs/documentation
```

也就是完整流程一般是：

```bash
cd docs/documentation
xelatex -interaction=nonstopmode -halt-on-error 9_user_draft.tex
xelatex -interaction=nonstopmode -halt-on-error 9_user_draft.tex
```

建议跑两遍，因为 LaTeX 的目录、引用、超链接等常常要第二遍才稳定。

---

## 3.2 为什么不能继续默认用 pdflatex

因为这份用户文档里已经加入了中文提示，例如：

- 给队友的写作提示
- 建议截图说明

这些内容在当前环境下如果用 `pdflatex`，很容易报中文相关错误。

所以目前：

- `9_user_draft.tex` -> 用 `xelatex`
- `9_system_draft.tex` -> 仍可继续用 `pdflatex`

---

## 3.3 编译成功后会得到什么

编译成功后会生成：

- `9_user_draft.pdf`
- `9_user_draft.aux`
- `9_user_draft.out`
- `9_user_draft.log`

真正需要看的主要是：

- `9_user_draft.tex`（源文件）
- `9_user_draft.pdf`（结果）
- `9_user_draft.log`（出错时查看）

像 `.aux` / `.out` 这些辅助文件不用手动编辑。

---

## 4. 你们接下来主要需要做哪些更改

## 4.1 第一类：把“提示型文档”逐步改成“正式文档”

现在 `9_user_draft.tex` 里面有很多中文提示块，形式大概像：

- 给队友的写作提示：……
- 建议截图说明：……

这些内容的作用是帮助你们继续写，不是最终提交时必须全部保留。

所以后续建议这样处理：

### 第一阶段

先保留这些提示，边写边补内容。

### 第二阶段

把每一节补完整后，逐步删除不再需要的提示。

### 第三阶段

只保留少量真的有助于排版和插图说明的内容，最终让 PDF 看起来像正式提交版。

---

## 4.2 第二类：补真实截图

这是当前最重要的工作之一。

请优先参考：

- `9_user_screenshot_checklist.md`

推荐优先补这些高价值页面：

- Login
- Dashboard
- Carbon Tracking
- Waste Management
- Reports
- Alerts
- ESG Management (Supplier)
- User Management

如果页数允许，再补：

- Training
- Policy Management
- Compliance Score
- Audit Log
- Anomaly Detection

---

## 4.3 第三类：把每一节写得更像“用户手册”

请特别注意：

用户文档写的是：

- 用户看到什么
- 用户能做什么
- 用户怎么操作
- 用户会得到什么结果

不要写成：

- 后端怎么实现
- 数据库怎么设计
- 权限装饰器怎么工作
- 模型怎么算分

这些内容属于系统文档，不属于用户文档。

---

## 5. 修改时优先顺序建议

如果时间有限，建议按下面顺序推进：

## 第一优先级

- 把高优截图补上
- 把每个角色章节写顺
- 保证“Store Staff / Region Manager / HQ Manager / Admin”都被覆盖

## 第二优先级

- 优化 Dashboard / Reports / Alerts / ESG Management 的正文表达
- 删除明显重复的提示块
- 把截图插图和 caption 补完整

## 第三优先级

- 微调版式
- 压页数
- 精修语言
- 删除多余协作提示

---

## 6. 每个部分该怎么继续写

## 6.1 Abstract

当前已经有基础内容。

后续只需要：

- 让语气更正式
- 去掉明显的“这是草稿”口吻
- 保留对角色化使用的概括

不需要写太长。

---

## 6.2 Getting Started

这里重点补：

- welcome / login / dashboard 之间的关系
- 登录后的进入流程
- sidebar 的 role-based 差异

可以继续扩展的点：

- 用户第一次进入系统的操作顺序
- 通用页面布局（sidebar + top bar + content area）
- 常见交互模式（form、table、modal、alert）

---

## 6.3 Shared Core Workflows

这是用户文档最重要的一部分之一。

这里已经有：

- Dashboard
- Carbon Tracking
- Waste Management
- Reports
- Training
- ESG Management Entry Point

你们要做的是把每节写得更完整，尤其是：

- 一段用途说明
- 一段操作说明
- 一段结果说明
- 配 1 张合适截图

---

## 6.4 Store Staff / Region Manager / HQ Manager / Admin

这些章节已经搭好了。

重点不是再重新分结构，而是：

- 让每个角色的“能做什么”写得更具体
- 把不同角色之间的权限差异写清楚
- 不要把 HQ/Admin 的功能误写给普通员工

注意：

### Store Staff

重点写：

- carbon
- waste
- report
- training

### Region Manager

重点写：

- alerts review
- compliance review
- anomaly review
- regional dashboard usage

### HQ Manager

重点写：

- alert thresholds
- supplier ESG
- policy management
- user management
- audit log

### Admin

可短写。

因为它和 HQ Manager 高度重合，不需要重复写太长。

---

## 7. 哪些内容不要乱改

下面这些内容如果不确定，不要随便改：

## 7.1 角色权限边界

当前大体边界是：

- `store_staff`：自己门店的操作型功能
- `region_manager`：区域级查看和管理型监控
- `hq_manager`：公司级治理和管理功能
- `admin`：更高层级的管理权限

如果不确定某个页面是否真的对某个角色开放，请先查：

- `frontend/templates/base.html`
- 对应页面的 route 限制

不要主观猜。

---

## 7.2 模块名称

请尽量保持和系统里实际显示一致，比如：

- Dashboard
- Carbon Tracking
- Waste Management
- Reports
- Training
- ESG Management
- Alerts
- Compliance Score
- Anomaly Detection
- User Management
- Audit Log

不要自己乱起新名字。

---

## 7.3 过度技术化表达

用户文档不要写太多类似：

- weighted aggregation
- blueprint routing
- database migration
- API fallback strategy

这些在系统文档里可以写，在用户文档里应尽量弱化。

---

## 8. 如果继续用 AI，建议怎么用

## 8.1 正确用法

推荐让 AI 做这些事情：

- 把一段提示改写成更自然的英文用户手册段落
- 帮你把一个页面操作过程写成 4--6 步
- 帮你润色角色章节
- 帮你把 caption 写得更正式
- 帮你压缩页数或合并重复内容

---

## 8.2 不推荐直接让 AI 做的事情

不要直接让 AI：

- 凭空猜页面功能
- 凭空猜角色权限
- 自己发明新模块
- 重写整个文档而不看现有结构

因为这样最容易把真实项目写错。

---

## 8.3 推荐给 AI 的提问方式

可以直接把下面这种上下文一起发给 AI：

```text
This is a user documentation draft for a web-based ESG platform.
Please keep the document in English.
Conversation and guidance can be in Chinese.
Do not invent features.
Only describe user-facing behaviour based on the provided text.
Help me rewrite this section into a polished user-manual style paragraph.
```

然后再把当前章节的草稿贴进去。

---

## 8.4 推荐给 AI 的具体任务例子

### 例子 1：润色段落

```text
Please rewrite the following paragraph into a concise but formal user-manual style paragraph in English. Keep all existing functions and do not invent new details.
```

### 例子 2：补操作步骤

```text
Please turn this page description into 5 clear user steps for a user documentation section. Keep it practical and non-technical.
```

### 例子 3：压缩页数

```text
Please shorten this section by about 25% without removing the key workflow and permission details.
```

### 例子 4：生成图注

```text
Please write a formal figure caption for a screenshot of the Alerts page showing both threshold configuration and alert logs.
```

---

## 9. 截图插入时建议怎么做

## 9.1 图文件放哪里

建议统一放在：

```text
docs/documentation/figures/
```

比如：

- `userdoc_hq_dashboard_overview.png`
- `userdoc_staff_carbon_table_form.png`
- `userdoc_hq_users_table.png`

---

## 9.2 插图时注意

- 图片宽度尽量统一
- 一页不要塞太多大图
- caption 用英文
- 插图位置尽量靠近对应小节

---

## 9.3 如果版面不够

优先保留：

- Login
- Dashboard
- Carbon
- Waste
- Reports
- Alerts
- Supplier ESG
- User Management

其他图可以缩短或删掉。

---

## 10. 最终提交前检查清单

在准备最终提交版前，请逐项检查：

## 文本检查

- 是否仍有太多“给队友的写作提示”残留在正式版里
- 是否有明显重复段落
- 是否有写错角色权限的地方
- 是否有把系统实现内容写进用户文档的地方

## 截图检查

- 图是否清晰
- 图是否匹配对应角色
- 图是否和正文描述一致
- 图文件命名是否统一

## 编译检查

- 是否使用 `xelatex` 成功编译
- PDF 是否页数合理（目标不超过 10 页）
- 是否有严重溢出或空白页

---

## 11. 当前建议的工作分工

如果两个人继续协作，建议这样分：

## 队友 A

负责：

- login
- dashboard
- carbon
- waste
- reports
- training

## 队友 B

负责：

- alerts
- supplier ESG
- policy management
- compliance score
- anomaly detection
- user management
- audit log

最后再一起统一：

- Abstract
- Role overview
- Conclusion
- 全文语气
- 图片排版

---

## 12. 一句话总结

不要从零重写。

正确做法是：

- 基于 `9_user_draft.tex` 继续补
- 按 `9_user_screenshot_checklist.md` 去截图
- 用 AI 帮忙润色、压缩、改写
- 但所有功能和权限都必须以现有项目真实实现为准

如果后面你们还需要，我可以继续补一个：

- `用户文档 figure 插图模板说明`
- 或者 `把 9_user_draft.tex 里的高优先级截图占位直接插进去`
