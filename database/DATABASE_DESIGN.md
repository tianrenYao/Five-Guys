# Business Sustainability Management Platform - 数据库设计文档

## 1. 概述

本文档描述平台的数据库设计方案，基于 MySQL 8.0+，字符集 `utf8mb4`。  
相比初步计划中的 4 表设计，改进版扩展为 **10 张表 + 2 个视图**，解决了安全性、可扩展性和数据完整性问题。

## 2. 新旧对比

| 维度 | 旧版（4表） | 新版（10表） |
|---|---|---|
| 密码存储 | 明文 VARCHAR(50) | bcrypt/werkzeug 哈希 VARCHAR(255) |
| 数据精度 | FLOAT | DECIMAL |
| 企业管理 | 无 | `company` 表，支持多企业 |
| 碳排放 | 固定 3 字段 | `emission_factor` 因子表 + `carbon_record` 灵活记录 |
| 垃圾分类 | 固定 2 类型 | `waste_category` 可扩展类别表 |
| 报告功能 | 仅存路径 | 增加类型/状态/日期范围等元数据 |
| SDG 对齐 | 无 | `sdg_goal` + `company_sdg` 关联表 |
| 审计追踪 | 无 | `audit_log` 操作日志表 |
| 索引优化 | 无 | 关键查询字段均有索引 |
| 时间追踪 | 部分 | 所有表含 `created_at` / `updated_at` |

## 3. ER 关系图（文字描述）

```
company  1──N  user
company  1──N  carbon_record
company  1──N  waste_record
company  1──N  report
company  M──N  sdg_goal       (通过 company_sdg)

user     1──N  carbon_record
user     1──N  waste_record
user     1──N  report
user     1──N  audit_log

emission_factor  1──N  carbon_record
waste_category   1──N  waste_record
```

## 4. 各表说明

### 4.1 `company` - 企业/组织表
存储入驻企业信息，所有业务数据通过 `company_id` 实现数据隔离。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | 自增主键 |
| name | VARCHAR(100) | 企业名称 |
| industry | VARCHAR(50) | 所属行业 |
| country | VARCHAR(50) | 所在国家 |
| address | VARCHAR(255) | 企业地址 |
| contact_email | VARCHAR(100) | 联系邮箱 |

### 4.2 `user` - 用户表
支持三种角色：`admin`（平台管理员）、`business`（企业管理者）、`staff`（普通员工）。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | 自增主键 |
| company_id | INT FK | 所属企业 |
| username | VARCHAR(50) UNIQUE | 登录名 |
| password | VARCHAR(255) | 哈希密码 |
| display_name | VARCHAR(50) | 显示名 |
| email | VARCHAR(100) | 邮箱 |
| role | ENUM | admin/business/staff |
| is_active | TINYINT(1) | 是否启用 |
| last_login | DATETIME | 最近登录 |

### 4.3 `emission_factor` - 碳排放因子表
存储各排放源的标准换算系数，数据来源于 IPCC / DEFRA / GHG Protocol。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | 自增主键 |
| category | VARCHAR(50) | 类别：electricity/transport/fuel/commute |
| sub_type | VARCHAR(50) | 子类型：grid_ireland/diesel_car 等 |
| factor | DECIMAL(12,6) | 排放因子 (kgCO2e/单位) |
| unit | VARCHAR(30) | 计量单位 |
| source | VARCHAR(100) | 数据来源 |
| valid_year | YEAR | 适用年份 |

### 4.4 `carbon_record` - 碳排放记录表
每条记录 = 活动量 × 排放因子 → 碳排放量。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | 自增主键 |
| company_id | INT FK | 所属企业 |
| user_id | INT FK | 录入人 |
| factor_id | INT FK | 排放因子 |
| category | VARCHAR(50) | 排放类别 |
| activity_value | DECIMAL(12,4) | 活动量 |
| total_carbon | DECIMAL(12,4) | 碳排放量 (kgCO2e) |
| record_date | DATE | 数据日期 |
| note | VARCHAR(255) | 备注 |

**碳排放计算公式**：`total_carbon = activity_value × emission_factor.factor`

### 4.5 `waste_category` - 垃圾分类类别表
预置 5 种类别，支持后续扩展。

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | 自增主键 |
| name | VARCHAR(50) UNIQUE | 类别名称 |
| is_recyclable | TINYINT(1) | 是否可回收 |

### 4.6 `waste_record` - 垃圾管理记录表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | 自增主键 |
| company_id | INT FK | 所属企业 |
| user_id | INT FK | 录入人 |
| category_id | INT FK | 垃圾类别 |
| weight_kg | DECIMAL(10,2) | 重量 (kg) |
| record_date | DATE | 数据日期 |
| note | VARCHAR(255) | 备注 |

**回收率计算**：`recovery_rate = recyclable_kg / total_kg × 100%`（通过视图自动计算）

### 4.7 `report` - 可持续发展报告表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK | 自增主键 |
| company_id | INT FK | 所属企业 |
| user_id | INT FK | 生成人 |
| title | VARCHAR(150) | 报告标题 |
| report_type | ENUM | monthly/quarterly/annual/custom |
| date_from / date_to | DATE | 覆盖日期范围 |
| content | TEXT | 报告正文 |
| pdf_path | VARCHAR(255) | PDF 文件路径 |
| status | ENUM | draft/generated/exported |

### 4.8 `sdg_goal` - SDG 目标参照表
存储联合国 17 个可持续发展目标，平台预置与项目相关的 4 个（SDG 9/11/12/13）。

### 4.9 `company_sdg` - 企业 SDG 关联表
多对多关系，记录企业关注的 SDG 目标及进展。

### 4.10 `audit_log` - 审计日志表
记录用户的关键操作（登录、增删改、导出等），便于安全审计。

## 5. 视图

### `v_carbon_monthly_summary`
按企业、排放类别、月份汇总碳排放数据，供 Dashboard 折线图/柱状图使用。

### `v_waste_monthly_summary`
按企业、月份汇总垃圾数据并自动计算回收率，供 Dashboard 饼图使用。

## 6. 预置数据

| 数据 | 内容 |
|---|---|
| 企业 | Demo Corporation (Ireland, Technology) |
| 测试账号 | test_business (business), test_staff (staff)，密码均为 123456 |
| SDG | SDG 9, 11, 12, 13 |
| 垃圾类别 | General / Recyclable / Hazardous / Organic / E-Waste |
| 排放因子 | 12 条常用因子（电力、交通、燃油、通勤），来源 IPCC/DEFRA/SEAI 2023 |

## 7. 安全注意事项

1. **密码**：使用 `werkzeug.security.generate_password_hash()` 生成，`check_password_hash()` 验证
2. **SQL 注入**：所有查询使用参数化（Flask-MySQLdb 的 `%s` 占位符）
3. **测试账号密码**：部署时通过 Flask 初始化脚本生成哈希，schema.sql 中为占位符
4. **审计日志**：关键操作自动写入 `audit_log`，不可由普通用户删除

## 8. 索引策略

- `carbon_record`: 按 `(company_id, record_date)` 复合索引 → Dashboard 时间范围查询
- `waste_record`: 按 `(company_id, record_date)` 复合索引 → 同上
- `audit_log`: 按 `(created_at)` 索引 → 日志时间范围查询
- `user`: 按 `(company_id)` 索引 → 企业用户列表查询

## 9. 建表脚本

见 `schema.sql`，可直接在 MySQL 中执行。
