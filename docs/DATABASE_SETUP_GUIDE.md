# 数据库环境搭建指南（适用于所有操作系统）

> 当你需要在本地运行项目代码时，按照本指南操作。
> 如果你只是写文档，不需要看这个。

---

## 一、安装 MySQL

### macOS

**方式 1：Homebrew（推荐）**
```bash
# 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 MySQL
brew install mysql

# 启动 MySQL 服务
brew services start mysql

# 设置 root 密码（第一次安装必须执行）
mysql_secure_installation
# 按提示设置密码，其他选项按 Y 即可
```

**方式 2：官方安装包**
1. 访问 https://dev.mysql.com/downloads/mysql/
2. 选择 macOS → DMG Archive → 下载
3. 双击 DMG 安装，安装过程中会提示设置 root 密码（**记住这个密码！**）
4. 安装完成后，在「系统设置 → MySQL」中确认服务已启动

### Windows

**方式 1：MySQL Installer（推荐）**
1. 访问 https://dev.mysql.com/downloads/installer/
2. 下载 `mysql-installer-community-x.x.x.msi`（选大的那个）
3. 运行安装程序，选择「Developer Default」
4. 安装过程中设置 root 密码（**记住这个密码！**）
5. 安装完成后，MySQL 服务会自动启动

**方式 2：手动配置**
1. 下载 MySQL ZIP 包解压
2. 添加 `mysql/bin` 到系统 PATH 环境变量
3. 初始化：`mysqld --initialize --console`（记下临时密码）
4. 启动服务：`mysqld --install` → `net start mysql`
5. 登录修改密码：`mysql -u root -p` → `ALTER USER 'root'@'localhost' IDENTIFIED BY '你的新密码';`

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install mysql-server -y
sudo systemctl start mysql
sudo systemctl enable mysql

# 设置 root 密码
sudo mysql_secure_installation
```

---

## 二、验证 MySQL 安装

打开终端（macOS/Linux）或 CMD/PowerShell（Windows），执行：

```bash
mysql -u root -p
```

输入你刚才设置的密码。如果看到 `mysql>` 提示符，说明安装成功。输入 `exit` 退出。

---

## 三、导入项目数据库

### 1. 克隆项目（如果还没有）
```bash
git clone https://github.com/tianrenYao/Five-Guys.git
cd Five-Guys
```

### 2. 执行建表脚本
```bash
mysql -u root -p < database/schema.sql
```
输入你的 MySQL root 密码。成功后不会有任何输出（没有报错就是成功了）。

### 3. 验证数据库是否创建成功
```bash
mysql -u root -p -e "USE sustainability_platform; SHOW TABLES;"
```

你应该看到 10 张表：
```
+--------------------------------------+
| Tables_in_sustainability_platform    |
+--------------------------------------+
| audit_log                            |
| carbon_record                        |
| company                              |
| company_sdg                          |
| emission_factor                      |
| report                               |
| sdg_goal                             |
| user                                 |
| waste_category                       |
| waste_record                         |
+--------------------------------------+
```

---

## 四、配置项目环境变量

### 1. 复制环境变量模板
```bash
cp .env.example .env
```

### 2. 编辑 .env 文件

用任意文本编辑器打开 `.env`，修改以下内容：

```ini
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码    ← 改成你自己的密码
MYSQL_DB=sustainability_platform
FLASK_SECRET_KEY=any-random-string-here
FLASK_DEBUG=True
FLASK_PORT=5001
```

> ⚠️ **重要**：`.env` 文件包含密码，已被 `.gitignore` 忽略，**不会被提交到 Git**。每个人需要自己创建。

---

## 五、安装 Python 依赖

### 前提：确保有 Python 3.10+
```bash
python3 --version
# 如果没有，去 https://www.python.org/downloads/ 下载安装
```

### 安装依赖包
```bash
pip3 install -r requirements.txt
```

如果你用的是 Anaconda：
```bash
pip install -r requirements.txt
```

---

## 六、初始化测试数据

```bash
python3 backend/init_db.py
```

正确输出应该是：
```
==================================================
Sustainability Platform - Database Initialization
==================================================

Connected to MySQL: localhost:3306
Database: sustainability_platform

[1/2] Initializing test accounts...
  Updated password hash for: test_business
  Updated password hash for: test_staff
[2/2] Inserting sample data...
  Inserted 9 sample carbon records
  Inserted 9 sample waste records

Done! You can now run: python3 backend/app.py
Then visit: http://localhost:5001
Login with: test_business / 123456
```

---

## 七、启动项目

```bash
python3 backend/app.py
```

看到以下输出说明启动成功：
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5001
```

打开浏览器访问 **http://localhost:5001**

### 测试账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| test_business | 123456 | 企业管理员 |
| test_staff | 123456 | 普通员工 |

---

## 常见问题

### Q1: `mysql` 命令找不到
- **macOS**：`export PATH="/usr/local/mysql/bin:$PATH"`，或在 `.zshrc` 中添加
- **Windows**：把 `C:\Program Files\MySQL\MySQL Server 8.0\bin` 添加到系统 PATH

### Q2: 端口 5001 被占用
编辑 `.env`，把 `FLASK_PORT=5001` 改成其他端口（如 5002、8080）。

### Q3: `Access denied for user 'root'@'localhost'`
`.env` 文件中的 `MYSQL_PASSWORD` 和你的 MySQL 实际密码不一致，检查并修正。

### Q4: `ModuleNotFoundError: No module named 'flask'`
Python 依赖没装。执行 `pip3 install -r requirements.txt`。

### Q5: macOS 上端口 5000 被 AirPlay Receiver 占用
这是正常的。我们的项目默认使用 5001 端口，不受影响。如果 5001 也被占用，改 `.env` 中的端口号。

### Q6: 重新初始化数据库（想清空重来）
```bash
mysql -u root -p < database/schema.sql    # 重建所有表
python3 backend/init_db.py                # 重新插入测试数据
```

---

## 完整命令速查（从零到运行）

```bash
# 1. 克隆代码
git clone https://github.com/tianrenYao/Five-Guys.git
cd Five-Guys

# 2. 建数据库
mysql -u root -p < database/schema.sql

# 3. 配置环境
cp .env.example .env
# 编辑 .env，填入你的 MySQL 密码

# 4. 装依赖
pip3 install -r requirements.txt

# 5. 初始化数据
python3 backend/init_db.py

# 6. 启动
python3 backend/app.py

# 7. 浏览器打开 http://localhost:5001
# 登录：test_business / 123456
```
