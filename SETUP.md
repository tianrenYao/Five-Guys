# 从零开始运行指南

> 已在 macOS（Apple Silicon / Intel）和 Ubuntu 22.04 上验证。
> Windows 用户请使用 WSL2（Ubuntu）或 Git Bash 执行 Shell 命令。

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
cryptography          # MySQL 认证（caching_sha2_password 方式必需）
weasyprint==62.3      # PDF 导出（需要 pango 系统库）
Jinja2==3.1.4
pytesseract==0.3.13   # OCR 可选，需额外安装 tesseract 系统包
Pillow==10.3.0        # OCR 图像处理（可选）
pdfplumber==0.11.0    # OCR PDF 解析（可选）
```

一条命令安装全部：

```bash
pip3 install Flask flask-cors PyMySQL werkzeug python-dotenv cryptography \
             weasyprint Jinja2 pytesseract Pillow pdfplumber
```
