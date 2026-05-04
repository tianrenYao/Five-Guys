# 项目部署与更新指南

> 已在 macOS（Apple Silicon / Intel）、Ubuntu 22.04 和 Windows WSL2 上验证。
> Windows 原生用户请使用 WSL2（Ubuntu）或 Git Bash 执行 Shell 命令。
>
> **新成员/新设备快速开始**：按照第一步到第七步顺序执行即可。
> **已有环境更新代码**：只需执行 [拉取最新代码](#拉取最新代码更新) 和 [运行迁移脚本](#第四步b--运行数据库迁移脚本) 两步。

---

## Windows 原生一键配置教程（PowerShell）

> 适用对象：**Windows 10 / 11 原生环境**，不使用 WSL、不使用 Git Bash。
>
> 推荐使用 **PowerShell** 或 **Windows Terminal - PowerShell** 执行以下命令。

### 0. 先安装这 3 个软件

请先手动安装以下软件，并确保安装后重新打开一个新的 PowerShell 窗口：

- **Python 3.10+**：安装时勾选 `Add python.exe to PATH`
- **Git for Windows**：安装完成后可用 `git --version` 检查
- **MySQL Server 8.0+**：安装时记住 root 密码，并确保 MySQL 服务已启动

可用以下命令检查是否安装成功：

```powershell
python --version
git --version
mysql --version
```

如果你的电脑上 `python` 命令不可用，也可以把下面教程中的 `python` 全部替换成：

```powershell
py -3
```

### 1. 拉取项目代码

```powershell
git clone https://github.com/tianrenYao/Five-Guys.git
cd Five-Guys
```

### 2. 复制环境变量模板

```powershell
Copy-Item .env.example .env
notepad .env
```

打开后至少填写这些内容：

```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DB=sustainability_platform

FLASK_SECRET_KEY=任意随机字符串
FLASK_DEBUG=True
FLASK_PORT=5001

DEEPSEEK_API_KEY=你的DeepSeek密钥
```

如果你要测试邮件功能，还要继续填写：

```ini
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=你的Mailtrap用户名
MAIL_PASSWORD=你的Mailtrap密码
MAIL_DEFAULT_SENDER=noreply@esg-platform.com
```

### 3. 一键执行初始化命令

确认 `.env` 保存后，在**项目根目录**直接复制执行下面整段命令：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cmd /c "mysql -u root -p < database\schema.sql"
cmd /c "mysql -u root -p sustainability_platform < database\seed.sql"
python database\init_users.py
python database\run_migrations.py
python -m backend.app
```

执行说明：

- **前两行**：安装 Python 依赖
- **中间两行**：导入数据库结构和演示数据，这两步会要求你输入 MySQL root 密码
- **`init_users.py`**：初始化测试账号密码
- **`run_migrations.py`**：补齐最新数据库字段和新表
- **最后一行**：启动 Flask 服务

### 4. 启动成功后的访问地址

看到类似输出就说明成功：

```text
 * Running on http://127.0.0.1:5001
 * Debugger is active!
```

浏览器打开：

```text
http://localhost:5001
```

### 5. 可直接登录的测试账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| `test_business` | `123456` | 总部 ESG 经理（全功能） |
| `test_region` | `123456` | 区域经理 |
| `test_staff` | `123456` | 门店员工 |

### 6. Windows 常见报错

#### `python 不是内部或外部命令`

说明 Python 没加到 PATH。

解决方法：

- 重新安装 Python，并勾选 `Add python.exe to PATH`
- 或把教程中的 `python` 改为 `py -3`

#### `mysql 不是内部或外部命令`

说明 MySQL 命令行工具没加到 PATH。

解决方法：

- 重新打开 PowerShell 再试一次
- 或把 MySQL 的 `bin` 目录加入系统 PATH
- 常见路径类似：`C:\Program Files\MySQL\MySQL Server 8.0\bin`

#### `Access denied for user 'root'@'localhost'`

说明 `.env` 中的 `MYSQL_PASSWORD` 填错了，或者你导入数据库时输入错了密码。

#### `ModuleNotFoundError: No module named 'weasyprint'`

重新执行：

```powershell
python -m pip install -r requirements.txt
```

#### PDF 导出失败 / WeasyPrint 缺少动态库

Windows 原生环境下，**系统主体功能通常不受影响**，但 PDF 导出依赖可能更严格。

优先尝试：

```powershell
python -m pip install --upgrade pip
python -m pip install weasyprint==62.3
```

如果仍然失败，再考虑改用 WSL2 运行 PDF 导出相关功能。

#### `Address already in use`

说明端口被占用。把 `.env` 中的：

```ini
FLASK_PORT=5001
```

改成例如：

```ini
FLASK_PORT=5002
```

然后重新执行：

```powershell
python -m backend.app
```

### 7. 已有环境更新代码

如果你同学已经成功跑起来过一次，以后更新只要在项目目录执行：

```powershell
git pull
python -m pip install -r requirements.txt
python database\run_migrations.py
python -m backend.app
```

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

## 第四步(C) — 批量生成示例数据（可选）

> 适用场景：演示前需要更多门店让地图、热力图、排行榜看起来更"丰满"；压力测试 API 性能；新成员搭好环境后想快速看到效果。

`schema.sql` + `run_migrations.py` 默认只创建 **18 家精心设计**的演示门店（id 1–18），分布在 5 个大区。如果想要 **几十到上千家**门店的视觉效果，使用：

```bash
python3 database/generate_stores.py --count 500 --seed 2026
```

### 常用命令

```bash
# 推荐演示规模：200 家店，可复现（同 seed 永远生成相同数据）
python3 database/generate_stores.py --count 200 --seed 42

# 极限压测：1000 家店
python3 database/generate_stores.py --count 1000 --seed 1000

# 6 个月历史数据
python3 database/generate_stores.py --count 50 --months 6

# 只预览不写库
python3 database/generate_stores.py --count 30 --dry-run

# 一键清空所有生成数据（id ≥ 100），保留原始 18 家不动
python3 database/generate_stores.py --purge-generated

# 查看完整帮助
python3 database/generate_stores.py --help
```

### 性能参考（单机本地 MySQL 实测）

| 数量 | 写入时间 | 总数据库行数 | API 响应 |
|---|---|---|---|
| 50 | 0.3 秒 | ~1.1k | <50 ms |
| 200 | 1.2 秒 | ~4.5k | <100 ms |
| 500 | 3.4 秒 | ~11k | <100 ms |
| 1000 | ~7 秒 | ~22k | <200 ms |

### 数据特性

- **36 座中国主要城市**（北上广深 + 成渝西安 + 武汉长沙等），真实经纬度
- **3 种规模 × 4 种 ESG 表现** = 12 种门店画像，加 ±8% 随机扰动
- **季节性碳排放**：冬夏用电高 20%，符合真实曲线
- **门店 ID 从 100 起**，永远不会冲突原始 18 家演示店
- **店名自动去重**（重复时自动加 `#2 #3 …` 后缀）
- **可复现**：同 `--seed` 永远生成完全一样的数据
- **0 额外依赖**，复用现有 PyMySQL + python-dotenv

### 工作流建议

```bash
# 演讲前一天
python3 database/generate_stores.py --purge-generated      # 清空之前的测试数据
python3 database/generate_stores.py --count 300 --seed 2026  # 生成稳定 300 家

# 如果生成完不满意（比如颜色分布不好看）
python3 database/generate_stores.py --purge-generated
python3 database/generate_stores.py --count 300 --seed 9999  # 换个 seed 再来

# 演讲当天上 VM 部署，执行同样命令复现完全一致的数据
```

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

---

## UCD 都柏林 VM 生产部署（Nginx + Gunicorn + systemd）

> 适用对象：把项目部署到 UCD 提供的 Ubuntu 22.04 VM 上，通过 80/443 端口对外访问。
> VM 仅开放 22 / 80 / 443 三个端口，应用本身只能监听 `127.0.0.1`，由 Nginx 反向代理。

### 架构总览

```
外部浏览器 ──[80/443]──> Nginx ──[127.0.0.1:5001]──> Gunicorn ──> Flask app ──> MySQL(127.0.0.1:3306)
```

部署模板已放在仓库的 `deploy/` 目录：
- `deploy/nginx-esg.conf` — Nginx 站点配置
- `deploy/esg.service` — systemd 服务单元

### 步骤 1 — SSH 登录并修改密码

```bash
ssh student@<VM_HOSTNAME>
# 默认密码：Ucd-cs-2023!
passwd       # 修改为符合规范的强密码（≥16 位，含中间位置符号）
```

### 步骤 2 — 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git nginx mysql-server \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libcairo2 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    tesseract-ocr
```

### 步骤 3 — 拉取代码并准备虚拟环境

```bash
cd ~
git clone https://github.com/tianrenYao/Five-Guys.git
cd Five-Guys

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 步骤 4 — 配置 MySQL 与导入数据

```bash
sudo mysql_secure_installation        # 设置 root 密码（建议）
sudo mysql -u root -p < database/schema.sql
sudo mysql -u root -p sustainability_platform < database/seed.sql

python database/init_users.py
python database/run_migrations.py
```

### 步骤 5 — 配置 `.env`（生产模式）

```bash
cp .env.example .env
nano .env
```

**关键字段（必须修改）：**

```ini
FLASK_DEBUG=False           # 生产环境务必关闭
FLASK_HOST=127.0.0.1        # 仅本地，由 Nginx 代理
FLASK_PORT=5001

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=<你的MySQL密码>
MYSQL_DB=sustainability_platform

FLASK_SECRET_KEY=<生成一段长随机串>
```

### 步骤 6 — 安装 systemd 服务

```bash
# 把模板复制到系统目录，并把占位符替换为真实路径
sudo cp deploy/esg.service /etc/systemd/system/esg.service
sudo sed -i "s|<PROJECT_PATH>|$HOME/Five-Guys|g" /etc/systemd/system/esg.service

sudo systemctl daemon-reload
sudo systemctl enable --now esg
sudo systemctl status esg          # 检查是否 active (running)
```

### 步骤 7 — 安装 Nginx 反向代理

```bash
# 复制站点配置并替换占位符
sudo cp deploy/nginx-esg.conf /etc/nginx/sites-available/esg
sudo sed -i "s|<VM_HOSTNAME>|$(hostname -f)|g" /etc/nginx/sites-available/esg
sudo sed -i "s|<PROJECT_PATH>|$HOME/Five-Guys|g" /etc/nginx/sites-available/esg

# 启用站点
sudo ln -sf /etc/nginx/sites-available/esg /etc/nginx/sites-enabled/esg
sudo rm -f /etc/nginx/sites-enabled/default

# 测试并重载
sudo nginx -t
sudo systemctl reload nginx
```

### 步骤 8 — 验证访问

在本地浏览器打开：

```
http://<VM_HOSTNAME>/
```

应直接看到登录页（不需要带任何端口号）。

### 步骤 9（可选）— 启用 HTTPS

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d <VM_HOSTNAME>
# 按提示输入邮箱并同意条款，Certbot 会自动改写 Nginx 配置并申请证书
```

完成后 80 端口会自动跳转到 443，所有访问通过 HTTPS 加密。

### 故障排查

| 现象 | 排查命令 |
|---|---|
| 访问 502 Bad Gateway | `sudo systemctl status esg` 查看 Gunicorn 是否在跑 |
| 应用日志 | `sudo journalctl -u esg -n 100 -f` |
| Nginx 错误日志 | `sudo tail -f /var/log/nginx/error.log` |
| 端口监听检查 | `sudo ss -tlnp \| grep -E '80\|5001'` |
| 重启应用 | `sudo systemctl restart esg` |
| 重载 Nginx 配置 | `sudo systemctl reload nginx` |

### 更新代码后的标准流程

```bash
cd ~/Five-Guys
git pull
source venv/bin/activate
pip install -r requirements.txt
python database/run_migrations.py
sudo systemctl restart esg
```
