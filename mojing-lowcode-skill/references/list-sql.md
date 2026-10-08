# 列表 custom_sql 实操（数据源 / 统计 / 卡片 / 按钮）

> 列表数据源 = `onl_list_basic.custom_sql`。平台把该 SQL 包一层做分页/查询，所以 SQL 内**禁 `select *`、结尾不加分号**；排序写进 SQL 内部（`ORDER BY ... DESC`），"自定义 SQL 排序"栏留空。

## 1. 内置变量（数据隔离）

| 变量 | 含义 | 用法 |
|---|---|---|
| `#{departMainId}` | 当前登录**部门 ID** | 单位端隔离：`p.org_name = '#{departMainId}'`（**带引号**） |
| `#{currentUser}` | 当前用户 ID | 如 `create_by = '#{currentUser}'` |

- 平台无独立数据权限功能，隔离全靠 SQL 变量。
- 单位名称显示：`org_name` 存部门 ID，要显示名称必须 join：`LEFT JOIN sys_depart d ON d.id = p.org_name`，取 `d.depart_name`。

## 2. "主记录 + 拆分记录"统计模式（一任务多单位）

下发任务 = 1 条主记录（`org_name` 逗号串）+ N 条拆分记录（`org_name` = 单个单位 ID）。列表/统计用 `LIKE '%,%'` 区分：

```sql
-- 主记录：任务头（管理端列表只显示这些）
WHERE p.org_name LIKE '%,%'
-- 拆分记录：各责任单位（统计对象）
WHERE c.org_name NOT LIKE '%,%'
```

管理端任务列表 SQL（已验证，含统计子查询）：

```sql
SELECT
  p.id,
  p.submit_status,
  p.project_name,
  p.publish_time,
  p.plan_finish_time,
  CONCAT(LENGTH(TRIM(BOTH ',' FROM p.org_name)) - LENGTH(REPLACE(TRIM(BOTH ',' FROM p.org_name), ',', '')) + 1, '家单位') AS unit_total_text,
  CONCAT(
    (SELECT COUNT(*) FROM nsm_ipv6_project c WHERE c.project_name = p.project_name AND c.del_flag = 0 AND c.org_name NOT LIKE '%,%' AND c.submit_status = 'submitted'),
    '/',
    (SELECT COUNT(*) FROM nsm_ipv6_project c WHERE c.project_name = p.project_name AND c.del_flag = 0 AND c.org_name NOT LIKE '%,%')
  ) AS fill_ratio,
  CONCAT(
    (SELECT COUNT(*) FROM nsm_ipv6_project c WHERE c.project_name = p.project_name AND c.del_flag = 0 AND c.org_name NOT LIKE '%,%' AND c.project_status = 'finished'),
    '/',
    (SELECT COUNT(*) FROM nsm_ipv6_project c WHERE c.project_name = p.project_name AND c.del_flag = 0 AND c.org_name NOT LIKE '%,%')
  ) AS finish_ratio,
  (
    SELECT COUNT(*) FROM nsm_ipv6_project c
    WHERE c.project_name = p.project_name AND c.del_flag = 0
      AND c.org_name NOT LIKE '%,%' AND c.project_status != 'finished'
      AND c.plan_finish_time IS NOT NULL AND c.plan_finish_time < NOW()
  ) AS overdue_count,
  CASE
    WHEN p.submit_status = 'draft' THEN '未下发'
    WHEN (SELECT COUNT(*) FROM nsm_ipv6_project c
          WHERE c.project_name = p.project_name AND c.del_flag = 0
            AND c.org_name NOT LIKE '%,%' AND (c.project_status != 'finished' OR c.project_status IS NULL)) > 0 THEN '进行中'
    ELSE '已结束'
  END AS task_state
FROM nsm_ipv6_project p
WHERE p.del_flag = 0 AND p.org_name LIKE '%,%'
ORDER BY p.create_time DESC
```

- 若平台查询把条件拼 SQL 末尾报"未知列 task_state"，外层包一层：`SELECT 列名... FROM (上述SQL) t ORDER BY t.create_time DESC`（不能 `SELECT *` 开头）。
- task_state 值为中文 → **不配数据转换/字典**（值是 CASE 中文，不是字典编码）。

## 3. 单位端列表（数据隔离 + 状态推导 + 最新进展）

```sql
SELECT
  p.id,
  p.id AS project_id,
  p.project_name,
  p.rectify_target,
  p.target_type,
  p.publish_time,
  p.plan_finish_time,
  p.plan_finish_time AS require_finish_time,
  p.submit_status,
  p.project_status,
  CASE WHEN p.material_status = 'not_submitted' THEN '待补充'
       WHEN p.material_status = 'finished' THEN '已补充'
       ELSE '无' END AS material_status,
  CASE WHEN p.project_status = 'finished' THEN '已完成'
       WHEN NOW() > p.plan_finish_time AND p.project_status <> 'finished' THEN '逾期'
       WHEN p.project_status = 'wait_fill' THEN '待填报'
       WHEN p.project_status = 'rectifying' THEN '整改中'
       ELSE '待填报' END AS task_state,
  (SELECT c.current_progress FROM nsm_ipv6_progress c
    WHERE c.project_id = p.id AND c.del_flag = 0
      AND c.current_progress IS NOT NULL AND TRIM(c.current_progress) <> ''
    ORDER BY c.create_time DESC LIMIT 1) AS latest_progress
FROM nsm_ipv6_project p
WHERE p.del_flag = 0 AND p.org_name = '#{departMainId}'
ORDER BY p.create_time DESC
```

要点：
- **SQL 必须 SELECT 出 `p.id`、`p.project_name`、`p.plan_finish_time AS require_finish_time`、`submit_status/project_status/material_status`**——按钮出参 `${id}/${project_name}/${require_finish_time}` 和显隐条件都依赖这些列（漏列会取空/全显）。
- "取最新一条"子查询**必须加空值过滤**（完成类操作会插空正文记录顶掉有值进度，见 `batch-subform.md` 关联问题）。

## 4. 统计卡片配置

- 卡片"自定义 sql" = **SQL 条件片段**（非 this. 表达式），引用列表 SQL SELECT 出的列名（含 CASE 别名）。
- **"全部"卡片不能填任何条件**（连 `1=1` 都报错）；只有状态类卡片填条件。
- 例：进行中任务卡 `task_state = '进行中'`；逾期任务卡 `overdue_count > 0`。

## 5. 查询条件

- 名称/关键字类：配在文本列（`包含`）。
- 状态下拉：若值是 CASE 中文 → 用**静态字典**（名称=值=待填报/整改中/已完成）；若值是字典编码 → 用字典（dynamicKey）。
- 类型筛选：配在真实字段上（如 `target_type` + 字典 `ipv6_target_type`），别误配到别的列。

## 6. 按钮显隐（列表按钮）

- **语法**：行内变量直接写变量名，**不加 `this.`**（`this.` 是列显示格式化用的）；内置属性前后加 `$$`（如 `$username$=='1'`）。
- 例：`project_status == 'wait_fill'`、`material_status == 'not_submitted'`、`submit_status != 'draft'`。
- 前提：列表 SQL 必须 SELECT 出该列（隐藏列也要输出，否则全行判空 → 按钮错显）。
- 打开方式：`addData`（新增）/`editData`（编辑，按 id 加载）/`viewData`（只读查看）；出参配置见 `events-groovy.md`。

## 7. 列表头按钮 vs 行内按钮

- **行内按钮**（操作列）：能取当前行数据，`agentValue=${行内列名}` 有效。
- **列表头按钮**：**取不到行数据**，`agentValue=${xxx}` 只能取页面入参/上下文。需要行数据时走入参链路（见 events-groovy.md §跨页传参）。
