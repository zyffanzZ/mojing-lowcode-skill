# 占位符约定（脱敏规范）

> 本技能面向其他 AI/开发者复用，**不得包含任何真实环境敏感信息**。以下占位符统一定义，遇到真实值一律替换。

## 1. 占位符清单

| 占位符 | 含义 | 示例值（仅供理解格式，非真实数据） |
|---|---|---|
| `{{DB_HOST}}` | 数据库主机 | 如 `203.0.113.10` |
| `{{DB_PORT}}` | 数据库端口 | `3306` |
| `{{DB_USER}}` | 数据库账号 | `root` |
| `{{DB_PASSWORD}}` | 数据库密码 | `{{DB_PASSWORD}}`（不写明文） |
| `{{DB_NAME}}` | 业务库名 | `mojing_cloud` |
| `{{PLATFORM_URL}}` | 平台访问地址 | `http://{{DB_HOST}}:9801/online/...` |
| `{{FORM_CODE}}` | 表单 code | `FormXXX`（仅示例编号，以你的平台为准） |
| `{{LIST_CODE}}` | 列表 code | `ListXXX` |
| `{{LIST_HEAD_ID}}` | 列表 head id | `{{LIST_HEAD_ID}}`（在 `onl_list_head` 查） |
| `{{UNIT_ID_1}}` … `{{UNIT_ID_N}}` | 真实单位（部门）ID | `{{UNIT_ID_1}}` |
| `{{UNIT_NAME_1}}` … | 真实单位名称 | `{{UNIT_NAME_1}}` |
| `{{USER_ID_1}}` … | 真实用户/账号 ID | `{{USER_ID_1}}` |
| `{{SQL_CODE}}` | SQL 管理编码 | `SQL001`（仅示例编号） |
| `{{TABLE_NAME}}` | 业务表名 | `nsm_ipv6_project`（表结构可保留） |

## 2. 替换规则

1. **数据库连接**：脚本/说明里连接参数一律用 `{{DB_HOST}}` 等占位符，并在注释写明"替换为你自己的环境值"。
2. **单位/用户 ID**：SQL 示例里的具体 ID 用 `{{UNIT_ID_1}}` 或文字说明"取真实单位 ID"；单位名称用 `{{UNIT_NAME_1}}`。
3. **表单/列表编号**：真实项目的 Form/List 编号不属于敏感凭据，但属于项目内部标识——统一用 `{{FORM_CODE}}/{{LIST_CODE}}` 或保留结构说明"示例编号，实际以你的平台为准"。
4. **账号密码**：任何明文密码不写，用 `{{DB_PASSWORD}}`。
5. **文件路径/附件**：附件存储路径结构可保留（如 `files/ipv6_plan/`），具体文件名脱敏。

## 3. 交付给使用者时的说明模板

> 本 Skill 的示例均来自"IPv6 整改任务管理"项目的真实踩坑，连接信息与 ID 已全部替换为占位符。使用时请：
> 1. 将 `{{DB_HOST}}/{{DB_PORT}}/{{DB_USER}}/{{DB_PASSWORD}}/{{DB_NAME}}` 替换为你的环境值；
> 2. 将 `{{UNIT_ID_1}}` 等替换为你的真实单位 ID（`SELECT id, depart_name FROM sys_depart` 可查）；
> 3. 表单/列表 code 以你的平台实际存在为准（`onl_form_head` / `onl_list_head` 可查）。
