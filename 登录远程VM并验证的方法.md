# Five-Guys ESG Platform — 组员 VM 登录与验证全流程

> **目标读者**：本组成员，用于从零开始登录 UCD 远程 VM 并在网页上验证项目。
> **最后更新**：2026-05-04
> ⚠️ **机密**：此文件含明文密码，已加入 `.gitignore`，**不要** push 到公开仓库。

---

## 全流程一览

| 步骤 | 做什么 | 需要的东西 |
|---|---|---|
| 1 | 检查网络能否直连 VM | `ping` |
| 2 | （只在直连不通时）开 UCD VPN | FortiClient + UCD 账号 + 2FA |
| 3 | SSH 登录 VM | 密码 `zhanglei30` |
| 4 | 浏览器做功能验证 | 浏览器 + 测试账号 |
| 5 | （可选）改代码 + 部署 | git pull / systemctl restart |
| 6 | 出问题排查 | 日志 / view 重建 / fail2ban |

---

## 步骤 1：先测直连（很多情况不用 VPN）

### 1.1 测能不能 ping 通

打开本地终端（Mac Terminal / WSL / Git Bash）：

```bash
ping -c 3 csi6220-1-vm2.ucd.ie
```

**预期 A（直连可达，常见于校园网环境如北工大）**：

```text
64 bytes from 172.19.0.142: icmp_seq=0 ttl=64 time=0.245 ms
64 bytes from 172.19.0.142: icmp_seq=1 ttl=64 time=0.347 ms
```

看到 `time=0.xxx ms`（毫秒以内）→ 网络**直连**，**跳过步骤 2**，直接去步骤 3。

**预期 B（不通）**：

```text
Request timeout
```

或

```text
ping: cannot resolve csi6220-1-vm2.ucd.ie: Unknown host
```

→ 你不在能直连 UCD 内网的环境。必须走步骤 2 开 VPN。

### 1.2 为什么有的网络不用 VPN？

UCD 的 VM 用的是私有 IP（`172.19.0.142`，RFC 1918 网段）。像北工大等学校与 UCD 有教育网专线 / 隧道，能直接路由到这个网段。所以**在校园网环境下**，`ping` 延迟只有 0.2ms（局域网级别），SSH 也不用 VPN。

---

## 步骤 2：（仅步骤 1 不通时）开 UCD VPN

### 2.1 安装 FortiClient VPN（一次性）

- 官网：<https://www.fortinet.com/support/product-downloads>
- 选 **FortiClient VPN**（免费版，不是带 EMS 的付费版）
- Mac / Windows / Linux 都支持

### 2.2 新建 VPN 配置

打开 FortiClient → **Remote Access** → **Configure VPN**：

| 字段 | 值 |
|---|---|
| VPN Type | **SSL-VPN** |
| Connection Name | `UCD` |
| Remote Gateway | `ssl-vpn.ucd.ie` |
| Port | `443` |
| Client Certificate | `None` |
| Authentication | `Prompt on login` |

### 2.3 连接

1. 选 `UCD` → 输入：
    - **Username**：你的 UCD student number（如 `24200123`）
    - **Password**：你的 UCD Connect 密码
2. 弹出 2FA 提示 → 打开 **Microsoft Authenticator** 或邮箱输验证码
3. 看到绿勾 ✅

然后重新跑步骤 1.1 的 `ping`，应该能通。

> 这里输入的"UCD 账号密码 + 2FA 验证码"是 **VPN 登录用**，**不是** SSH 密码。

---

## 步骤 3：SSH 登录 VM

### 3.1 登录命令

```bash
ssh student@csi6220-1-vm2.ucd.ie
```

**首次连接**会弹这个（输入 `yes` 回车）：

```text
The authenticity of host 'csi6220-1-vm2.ucd.ie (172.19.0.142)' can't be established.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

### 3.2 输密码

```text
student@csi6220-1-vm2.ucd.ie's password:
```

输入（**不会回显**，正常打完回车）：

```text
zhanglei30
```

### 3.3 登录成功

```text
Welcome to Ubuntu 22.04 LTS (GNU/Linux 5.15.0-... x86_64)

...

student@csi6220-1-vm2:~$
```

### 3.4 sudo 密码

```text
[sudo] password for student:
```

**还是** `zhanglei30`。

---

## 步骤 4：浏览器功能验证

### 4.1 打开网站

```text
http://csi6220-1-vm2.ucd.ie/
```

⚠️ 注意：**协议是 http，不是 https**。

### 4.2 测试账号（三种角色）

| 用户名 | 密码 | 角色 | 可见数据范围 |
|---|---|---|---|
| `test_business` | `123456` | HQ ESG Manager | **全部 218 家店**（推荐做验收） |
| `test_region` | `123456` | Region Manager | 仅 North Region 的店 |
| `test_staff` | `123456` | Store Staff | 仅 Beijing Chaoyang 店 |

### 4.3 12 项功能验证清单

用 **`test_business / 123456`** 登录后逐项测：

- [ ] **Dashboard**：4 张 KPI 卡 + Monthly Carbon Trend + Carbon by Category + Waste Composition + SDG 12 面板都有数据
- [ ] **Store Map**：200+ 彩色 marker，点 marker 有迷你趋势图
- [ ] **Carbon Tracking**：记录列表 >2000 条，新增表单可用
- [ ] **Waste Management**：记录 >2600 条
- [ ] **Reports**：3 份（Jan 2026 / Feb 2026 / 2026 Q1）
- [ ] **Alerts**：40+ 未读预警
- [ ] **Training**：3 条培训记录
- [ ] **ESG Management**：5 家供应商 + 3 条政策
- [ ] **Compliance Score**：选 2026 点 Calculate，能出分
- [ ] **Anomaly Detection**：能跑 AI 异常检测
- [ ] **User Management**（admin 菜单）：3 个用户
- [ ] **Audit Log**：能看到登录等操作记录

### 4.4 界面验证

- [ ] 左侧导航栏**固定一屏高**，滚动主内容时不动
- [ ] Logout 按钮在左下角永远可见
- [ ] Luckin + Company logo 在侧栏顶部
- [ ] Welcome 页有背景大图

### 4.5 角色切换验证

- [ ] 切 `test_region`：Dashboard 数据缩到 North Region
- [ ] 切 `test_staff`：Dashboard 数据缩到 Beijing Chaoyang 一家店

---

## 步骤 5：修改代码 + 部署

### 5.1 本地改代码 + push（在 Mac 上）

```bash
cd "/path/to/Five-Guys"
git add .
git commit -m "fix: xxx"
git push origin main
```

### 5.2 VM 拉取

SSH 登录 VM 后：

```bash
cd ~/Five-Guys
git pull
```

### 5.3 判断要不要重启服务

| 改动类型 | 重启命令 | 浏览器刷新 |
|---|---|---|
| 只改 `.css` / `.html` / `.js` / `.png` | **不需要** | `Cmd+Shift+R` 强刷 |
| 改了 `.py` | `sudo systemctl restart esg` | `Cmd+Shift+R` 强刷 |
| 改了 Nginx 配置 | `sudo systemctl reload nginx` | 正常刷 |
| 改了 DB schema | 手动跑 SQL | 看情况 |

### 5.4 看日志

```bash
sudo systemctl status esg              # 服务状态
sudo journalctl -u esg -f              # 实时日志，Ctrl+C 退出
sudo journalctl -u esg -n 100 --no-pager  # 最近 100 行
```

---

## 步骤 6：常见问题排查

### 6.1 `ssh ... Connection closed by 172.19.0.142 port 22`

ping 通但 SSH 立即关闭 = **fail2ban 封了你的 IP**（最常见）。

**确认方法**：跑

```bash
ssh -v student@csi6220-1-vm2.ucd.ie 2>&1 | head -40
```

看到最后一行是 `kex_exchange_identification: Connection closed by remote host` 就是 fail2ban。

**解封三选一**：

- **A. 等 10 分钟**（默认 bantime）自动解封
- **B. 用手机热点换 IP** 连上 VM，然后：

    ```bash
    sudo fail2ban-client status sshd
    sudo fail2ban-client unban --all
    ```

- **C. 让其他网络环境的组员** 帮你登录 VM，跑同样的 `unban --all` 命令

**解封后立刻做两件事防再次被封**：

**① Mac 端：配置 SSH 只用密码，别盲试 7 种密钥**

```bash
cat >> ~/.ssh/config << 'EOF'

Host csi6220-1-vm2.ucd.ie
    User student
    PreferredAuthentications password
    PubkeyAuthentication no
    IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config
```

之后跑 `ssh csi6220-1-vm2.ucd.ie` 就行（不用带 `student@`）。

**② VM 端：放宽 fail2ban（只需做一次，所有组员受益）**

```bash
sudo tee /etc/fail2ban/jail.d/ssh-tolerant.local > /dev/null << 'EOF'
[sshd]
enabled = true
maxretry = 10
findtime = 10m
bantime = 5m
EOF

sudo systemctl restart fail2ban
sudo fail2ban-client status sshd
```

### 6.1b known_hosts 旧指纹冲突

如果 `-v` 输出里有 `Host key verification failed` 或 `REMOTE HOST IDENTIFICATION HAS CHANGED`：

```bash
ssh-keygen -R csi6220-1-vm2.ucd.ie
ssh-keygen -R 172.19.0.142
ssh student@csi6220-1-vm2.ucd.ie   # 再试，输 yes 接受新指纹
```

### 6.2 `ssh ... Operation timed out` / `No route to host`

**完全连不上**。回到步骤 1，用 `ping` 诊断。如果 ping 也不通，必须开 VPN（步骤 2）。

### 6.3 `Permission denied` 连续报错

密码输错了。确认是 `zhanglei30`（全小写、无空格、无引号）。输错 5 次可能被 fail2ban 封 10 分钟。

### 6.4 浏览器打不开 `http://csi6220-1-vm2.ucd.ie/`

按顺序排查：

1. **网络不通** → `ping` 验证 → 必要时开 VPN
2. **浏览器自动跳了 https** → 地址栏改回 `http://`
3. **Gunicorn 挂了** → SSH 进 VM 跑 `sudo systemctl restart esg`
4. **Nginx 挂了** → `sudo systemctl restart nginx`

### 6.5 Dashboard 图表空白（曾经出过一次）

数据库 view 丢了。SSH 进 VM：

```bash
mysql -u root -pFiveGuys2026! sustainability_platform -e \
  "SELECT COUNT(*) AS view_cnt FROM information_schema.views WHERE table_schema='sustainability_platform';"
```

应该 `view_cnt = 4`。少于 4 需重建 view（联系部署负责人）。

### 6.6 静态图片 404 / 403

```bash
chmod o+x /home/student
chmod -R o+rX /home/student/Five-Guys/frontend/static/
sudo systemctl reload nginx
```

### 6.7 需要从零重建数据库（最后手段）

⚠️ **会删光所有数据**，只在开发环境或出错无法修时用：

```bash
cd ~/Five-Guys
source venv/bin/activate

mysql -u root -pFiveGuys2026! sustainability_platform < database/schema.sql
mysql -u root -pFiveGuys2026! sustainability_platform < database/seed.sql
python database/init_users.py
python database/run_migrations.py
python database/generate_stores.py --year 2026 --months 4

# ★ 关键：验证 view 都建好了，避免 Dashboard 图表空白
mysql -u root -pFiveGuys2026! sustainability_platform -e \
  "SELECT COUNT(*) AS view_cnt FROM information_schema.views WHERE table_schema='sustainability_platform';"
# 期望 view_cnt = 4

sudo systemctl restart esg
```

---

## 附录 A：全部密码一览（明文）

| 用途 | 用户名 | 密码 |
|---|---|---|
| UCD VPN（仅直连不通时需要） | 你的 UCD student number | 你的 UCD Connect 密码 + 2FA 验证码 |
| SSH 登录 VM（student 账号）+ sudo | `student` | `zhanglei30` |
| MySQL root | `root` | `FiveGuys2026!` |
| 应用登录 — HQ Manager | `test_business` | `123456` |
| 应用登录 — Region Manager | `test_region` | `123456` |
| 应用登录 — Store Staff | `test_staff` | `123456` |

---

## 附录 B：项目路径与服务概览

- **项目代码路径**：`/home/student/Five-Guys`
- **Python 虚拟环境**：`/home/student/Five-Guys/venv`
- **后端服务**：`systemd` 管理，服务名 `esg.service`
- **后端框架**：Flask + Gunicorn（监听 `127.0.0.1:5000`）
- **反向代理**：Nginx（监听公网 `80`，转发到 Gunicorn）
- **数据库**：MySQL 8.0，database 名 `sustainability_platform`
- **静态文件**：Nginx 直接从 `/home/student/Five-Guys/frontend/static/` 提供
- **VM 内网 IP**：`172.19.0.142`
- **公网 hostname**：`csi6220-1-vm2.ucd.ie`
- **开放端口**：仅 `22`（SSH）、`80`（HTTP）、`443`（HTTPS 预留）

完整部署流程见仓库根目录 `SETUP.md`。

---

## 附录 C：验收演示脚本（给老师看）

11 步演示顺序，全程应无 500 错误：

1. 展示 Welcome 页（背景图 + logo）
2. 登录 `test_business`
3. Dashboard：4 张 KPI 卡 + 4 张图 + SDG 面板
4. Map：缩放到中国，200+ marker，点 marker 看 popup
5. Carbon Tracking：新增一条记录
6. Reports：打开 2026 Q1 报告
7. Alerts：展示未读预警
8. Compliance Score：选 2026 Calculate 出分
9. Anomaly Detection：跑一次 AI 检测
10. 切 `test_region`：数据过滤到 North Region
11. 切 `test_staff`：数据过滤到 Beijing Chaoyang

---

## 附录 D：联系

部署出问题或忘记密码，联系本组部署负责人。
