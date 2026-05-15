# Documentation v2 — Style & LaTeX Conventions

> 本笔记用于在不同 conversation 之间共享 v2 文档（user + system）的写作与排版约定。新会话开场让 AI 先读本文件即可同步上下文。

---

## 1. 文档定位

| 文档 | 路径 | 受众 | 页数预算 |
|---|---|---|---|
| 用户文档 | `docs/documentation_v2/Group_9_user_documentation.tex` | end-user / evaluator | ≤10 页（当前 11，待组员评审） |
| 系统文档 | `docs/documentation_v2/Group_9_system_documentation.tex` | 开发者 / 维护者 / 审计 | ≤20 页 |

提交文件名规范：`9_user_draft.pdf` / `9_system_draft.pdf`（最后一步重命名）。

---

## 2. 编译流程

```bash
cd docs/documentation_v2
pdflatex -interaction=nonstopmode Group_9_user_documentation.tex
bibtex Group_9_user_documentation
pdflatex -interaction=nonstopmode Group_9_user_documentation.tex
pdflatex -interaction=nonstopmode Group_9_user_documentation.tex
```

系统文档同上，把文件名替换即可。

页数检查：`pdfinfo Group_9_*.pdf | grep Pages`。

---

## 3. `\new{}` 高亮规则（重要）

- v2 新增的内容用 `\new{...}` 包裹，编译后会在 PDF 中以淡黄色背景高亮，便于评审定位差异。
- **绝对不要** 把 `\new{}` 放进以下位置，否则编译会爆 fragile-command 错误：
  - `\caption{...}` 内部
  - `\section{...}` / `\subsection{...}` 标题
  - `\label{...}` / `\ref{...}` 参数
  - `\cite{...}` 参数
- **同样不要把 `\cite` / `\ref` / `\label` 放进 `\new{}` 内部**（反向同源 fragile 问题，2026-05-14 R1 编译两次复现）。处理办法：
  - 把含引用的句子拆出 `\new{}`，或
  - 改写成纯文本指代（如 `Table~\ref{tab:x}` → "the table below"，已用过的 `\cite{owasp2021}` → "the OWASP guidance referenced above"），或
  - 整张 float 表格不要包 `\new{}`，靠表内 `\rowcolor{yellow!40}` 标黄即可。
- 如果某句的一部分必须高亮、另一部分必须出现在 caption / 标题里，**拆成两条独立语句**：标题/caption 用纯文本，旁边正文段落用 `\new{}` 高亮。
- **`\new{}` 单块不要过长（< ~900 字符为佳）**。`soul` 的 `\hl` 内部缓冲在长段+复杂内容时会爆 `Package soul Error: Reconstruction failed`（2026-05-14 R2 §3.4 carbon CSV 长段实测）。处理办法：把长段拆成 2-3 个 `\new{...}` 段落，每段独立 `\hl`。
- **`\new{}` 内部避免嵌套 LaTeX 引号**（`` ` ``、`` `` ``、`'`、`''`）和反引号字符。soul 的字符重建对引号嵌套敏感。需要举例时改用单层 LaTeX 引号或纯文本。
- **`\textsubscript{}` / `\textsuperscript{}` 也是 fragile**，不能在 `\new{}` 内部使用（2026-05-14 R3 §3.9 `kgCO\textsubscript{2}e` 实测）。改写为纯文本（`kg CO2e`、`CO2-eq`）或者把整句拆出 `\new{}`。
- **下划线全部用 `\_` 转义**。即便 `\texttt{}` 内部也要转义：`\texttt{seed\_demo\_data.py}` 而不是 `\texttt{seed\_demo_data.py}`，否则 LaTeX 会把第二个 `_` 解释为数学下标导致 `Missing $ inserted`（R3 §3.11 实测）。

---

## 4. 图片放置

- 图片源：`docs/documentation_v2/images/`，通过 `\graphicspath{{images/}}` 引入。
- 文件命名：小写 + 下划线（`carbon_tracking.png`、`dashboard_hq_riskwatch.png`）。复合图按用途明确命名，避免 `image1.png` 这种。
- 浮动放置：用 `[H]`（来自 `float` 宏包）强制放置在写的位置；只有当 `[H]` 导致大量空白页时才退回 `[!ht]`。
- 多图组合：用 `\includegraphics ... \\[0.4em] \includegraphics ...` 上下堆叠，比 `subfigure` 更稳定。
- 宽度统一：单张主截图 `0.60–0.65\textwidth`；堆叠组合中每张 `0.85–0.92\textwidth`；缩略示意图 `0.45–0.55\textwidth`。

---

## 5. 写作语调

- **避免 AI 套句**：少用 "It is important to note that..."、"Furthermore,..."、"In addition to..." 这类衔接。
- **少用嵌套括号**：括号里的解释能改成从句就改。
- **句子长度上限 ~25 词**：超过就拆。
- **主动语态优先**：`Region managers review alert logs` 优于 `Alert logs can be reviewed by region managers`。
- **\rolelabel{}** 用于在正文里标注角色（Store Staff / Region Manager / HQ Manager / Admin），系统文档同样适用。

---

## 6. 常用 LaTeX 片段（v2 已用）

```latex
% 化学式下标
CO\textsubscript{2}e

% Z-score 阈值（用 \, 控制空格）
1.5\,$\sigma$

% 高亮 v2 新内容
\new{this is new in v2}

% 内联代码 / API 路径 / 按钮名
\texttt{Generate Report}
\emph{Add Record}      % 按钮 / 字段名建议用 emph

% 跨节引用
Section~\ref{sec:alerts-config}
Figure~\ref{fig:carbon}
\cite{gri_standards}

% 角色标签
\rolelabel{Store Staff}
```

---

## 7. 图片资产备注

- 所有 v2 截图都已就位（含 §3.6 Store Map `map_overview.png`）。
- 命名建议：避免中文文件名+空格（LaTeX 会出 unicode 问题），如有截图保存时是 `截屏xxx.png` 这种，落地到 `images/` 前重命名为 ASCII（例：`map_overview.png`）。

---

## 8. 已踩过的坑

1. **侧边栏图、login 截图、alert badge 小图** 这类「用户上手即知」的截图能删则删——读者不需要看见即可理解。
2. **同一张截图重复用** 要警惕：删除冗余出现，靠 `\ref{}` 互相指向。
3. **`subsection` 嵌 `figure[H]`** 当文字短、图片大时，`[H]` 会把图压到下一页留下大空白；这时把段落和图合并成一个 paragraph + figure 紧贴的结构能避免。
4. **大表 `[H]`** 容易在前一页留空白；如果表本身不可压缩，考虑把它周围的过渡段并入，或者用 `[!ht]` 放宽。

---

## 9. 参考文献

- 文件：`docs/documentation_v2/refs.bib`
- 引用风格：IEEE-style（`[1]`、`[2]`...）
- 关键已有条目：`un_sdg12`、`gri_standards`、`iso_14064`、`tcfd_2017`、`sasb_standards`、`bs_8001` 等
- 系统文档评估时需补：`ISTQB Foundation Level Syllabus v4.0`、`Bach Exploratory Testing`、`Brooke SUS scale`（见 REVISION_TODO B9）

---

## 10. 测试账号 (与代码 seed 一致)

| Username | Password | Role |
|---|---|---|
| `test_admin` | `123456` | Admin |
| `test_business` | `123456` | HQ Manager |
| `test_region` | `123456` | Region Manager |
| `test_staff` | `123456` | Store Staff |

文档里出现的账号字符串必须与登录页提示和后端 seed 完全一致。
