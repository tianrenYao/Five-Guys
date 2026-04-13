# 项目部署与更新指南

> 已在 macOS（Apple Silicon / Intel）、Ubuntu 22.04 和 Windows WSL2 上验证。
> Windows 原生用户请使用 WSL2（Ubuntu）或 Git Bash 执行 Shell 命令。
>
> **新成员/新设备快速开始**：按照第一步到第七步顺序执行即可。
> **已有环境更新代码**：只需执行 [拉取最新代码](#拉取最新代码更新) 和 [运行迁移脚本](#第四步b--运行数据库迁移脚本) 两步。

---

## 前置条件

确认以下工具已安装：

| 工具 | 最低版本 | 检查命令 |
|---|---|---|
| Python | 3.10+ | `python3 --version` |
| MySQL | 5.7+ | `mysql --version` |
| Git | 任意版本 | `git --version` |
| Homebrew（仅 macOS） | 任意版本 | `brew --version` |

---

## 第一步 — 拉取代码

```bash
git clone <仓库地址>
cd <项目文件夹>
```

---

## 第二步 — 安装 Python 依赖

```bash
pip3 install -r requirements.txt
```

> 如果遇到 SSL 超时或网络错误，切换国内镜像源：
>
> ```bash
> pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

**WeasyPrint（PDF 导出）需要系统级依赖，先安装：**

```bash
# macOS
brew install pango

# Ubuntu / Debian
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b
```

> **OCR 为可选功能。** 若需要真实账单识别（非 Mock 演示）：
>
> ```bash
> # macOS
> brew install tesseract
>
> # Ubuntu
> sudo apt-get install -y tesseract-ocr
> ```

---

## 第三步 — 配置环境变量

复制示例文件并填写你的 MySQL 信息：

```bash
cp .env.example .env
```

打开 `.env`，修改以下内容：

```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DB=sustainability_platform

FLASK_SECRET_KEY=任意随机字符串
FLASK_DEBUG=True
FLASK_PORT=5001
```

> ⚠️ macOS 上 `5000` 端口通常被 AirPlay 接收器占用，建议使用 `5001`。

---

## 第四步 — 创建数据库并导入数据

首先确保 MySQL 服务正在运行：

```bash
# macOS（Homebrew 安装的 MySQL）
brew services start mysql

# Ubuntu
sudo systemctl start mysql
```

然后导入建表脚本和演示数据（会提示输入 MySQL 密码）：

```bash
# 建表和视图（会自动创建数据库）
mysql -u root -p < database/schema.sql

# 导入演示数据（6 家门店，2026年1-4月记录、预警、报告）
mysql -u root -p sustainability_platform < database/seed.sql
```

> **提示：** `schema.sql` 已包含 `CREATE DATABASE IF NOT EXISTS`，首次运行会自动建库，无需手动创建。

---

## 第五步 — 初始化测试账号密码

```bash
python3 database/init_users.py
```

成功后输出：

```
  [OK] test_business → hash updated
  [OK] test_region → hash updated
  [OK] test_staff → hash updated

All passwords set. You can now log in with password: 123456
```

---

## 第六步 — 启动服务器

```bash
python3 -m backend.app
```

正常启动输出：

```
 * Running on http://127.0.0.1:5001
 * Debugger is active!
```

浏览器访问 **http://localhost:5001**

---

## 第七步 — 登录测试

| 用户名 | 密码 | 角色 |
|---|---|---|
| `test_business` | `123456` | 总部 ESG 经理（全功能） |
| `test_region` | `123456` | 华北区域经理 |
| `test_staff` | `123456` | 门店员工（朝阳店） |

---

## 常见问题排查

### `Access denied for user 'root'@'localhost'`

`.env` 中的 `MYSQL_PASSWORD` 密码填写有误，请核对后重试。

### `cryptography package is required`

```bash
pip3 install cryptography
```

### `ModuleNotFoundError: No module named 'weasyprint'`

```bash
pip3 install weasyprint

# macOS 还需要：
brew install pango
```

### 端口被占用（Address already in use）

修改 `.env` 中的 `FLASK_PORT` 为其他值（例如 `5002`）。

### MySQL 未安装或未启动

```bash
# macOS
brew install mysql
brew services start mysql

# Ubuntu
sudo apt-get install mysql-server
sudo systemctl start mysql
```

### Linux 上 WeasyPrint PDF 导出失败

```bash
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 \
    libharfbuzz0b libcairo2 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

---

## 依赖清单汇总

```text
Flask==3.1.0
flask-cors==5.0.1
PyMySQL==1.1.1
werkzeug==3.1.3
python-dotenv==1.1.0
Flask-Mail==0.10.0    # 邮件通知（v2.0 新增）
cryptography          # MySQL 认证（caching_sha2_password 方式必需）
weasyprint==62.3      # PDF 导出（需要 pango 系统库）
Jinja2==3.1.4
pytesseract==0.3.13   # OCR 可选，需额外安装 tesseract 系统包
Pillow==10.3.0        # OCR 图像处理（可选）
pdfplumber==0.11.0    # OCR PDF 解析（可选）
```

一条命令安装全部：

```bash
pip3 install -r requirements.txt
```

---

## 拉取最新代码（更新）

已有本地环境的成员，更新代码后只需执行以下两步：

```bash
# 1. 拉取最新代码
git pull

# 2. 安装新增依赖（v2.0 新增了 Flask-Mail）
pip3 install -r requirements.txt

# 3. 运行数据库迁移脚本（见下方说明）
python3 database/run_migrations.py
```

---

## 第四步(B) — 运行数据库迁移脚本

> 适用场景：代码更新后需要同步数据库结构变更，或在新设备上首次部署。

### 使用方法

在**项目根目录**执行（任意操作系统通用）：

```bash
python3 database/run_migrations.py
```

脚本会自动读取 `.env` 中的数据库配置，**无需手动输入密码**。

### 脚本特性

- **幂等性**：可重复执行，已存在的表/列会自动跳过（显示 `⏩ skip`），不会报错
- **跨平台**：macOS / Ubuntu / Windows WSL2 均可直接运行
- **清晰输出**：每步操作显示 `✅` 成功 / `⏩` 跳过 / `⚠️` 警告 / `❌` 错误

### 预期输出示例

```
✅ Connected to MySQL [localhost:3306] — database: sustainability_platform

=== Migration 1: notify_email ===
  ✅ add notify_email to alert_threshold

=== Migration 2: supplier table ===
  ✅ create supplier table

=== Migration 3: esg_policy table ===
  ✅ create esg_policy table

=== Seed: sample suppliers ===
  ✅ supplier: GreenBean Co.
  ✅ supplier: EcoPack Ltd.
  ...

✅ All migrations complete!
```

如果是已运行过的环境，输出会显示：

```
  ⏩ already exists — skip: add notify_email to alert_threshold
  ⏩ already exists — skip: create supplier table
  ...
✅ All migrations complete!
```

### 常见错误

| 错误信息 | 原因 | 解决方法 |
|---|---|---|
| `Cannot connect to database` | `.env` 配置有误或 MySQL 未启动 | 检查 `MYSQL_PASSWORD`；确认 MySQL 服务运行中 |
| `PyMySQL not installed` | 依赖未安装 | `pip3 install PyMySQL` |
| `❌ create supplier table: ...` | 外键引用的表不存在 | 先运行 `mysql -u root -p < database/schema.sql` |

---

## 邮件通知配置（可选）

v2.0 新增了预警邮件通知功能。**不配置也能正常运行**（自动切换为 Mock 模式，邮件内容打印到终端）。

### Mock 模式（默认，无需配置）

`.env` 中不填写 `MAIL_SERVER`，系统触发预警时在终端打印：

```
[Mail MOCK] Would send to=['xxx@example.com'] | Subject: [ESG Alert] ...
Body: Carbon emissions at Store X exceeded threshold ...
```

### 真实发送模式 — 推荐使用 Mailtrap（演示用）

[Mailtrap](https://mailtrap.io) 是专为开发/演示设计的邮件沙箱，邮件不会真正发出，全部拦截在 Mailtrap 网页收件箱，**演示效果极佳**。

**注册步骤：**

1. 访问 [mailtrap.io](https://mailtrap.io) → 用 GitHub/Google 一键注册（免费）
2. 进入 **Email Testing → Sandboxes → 点击你的 inbox**
3. 点击 **SMTP Settings**，选择 **Other** 集成方式
4. 复制显示的 Host、Port、Username、Password

**在 `.env` 中添加：**

```ini
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<Mailtrap 页面上的 Username>
MAIL_PASSWORD=<Mailtrap 页面上的 Password>
MAIL_DEFAULT_SENDER=noreply@esg-platform.com
```

**验证：**

重启服务器后，在 Alerts 页面触发一条预警，登录 Mailtrap 即可在收件箱看到邮件。

### 其他 SMTP 服务（自用邮箱）

| 服务 | MAIL_SERVER | MAIL_PORT | 备注 |
|---|---|---|---|
| Gmail | `smtp.gmail.com` | `587` | 需开启两步验证并生成 App Password |
| QQ 邮箱 | `smtp.qq.com` | `587` | 需在 QQ 邮件设置中开启 SMTP 并获取授权码 |
| 163 邮箱 | `smtp.163.com` | `465` | `MAIL_USE_TLS=False`，改用 SSL |
| Outlook | `smtp.office365.com` | `587` | 使用账号密码直接登录 |
