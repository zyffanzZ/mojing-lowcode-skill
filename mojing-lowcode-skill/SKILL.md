---
name: mojing-lowcode-skill
description: 魔镜（MoJing/儒松·维保保/JeecgBoot 系）低代码平台的在线开发操作技能。用户提到"魔镜/表单设计/列表设计/在线开发/关联弹窗/下发表单/SQL 数据源/按钮出参/事件脚本/Groovy/批量子表/在线列表/Listxxxx/Formxxxx"，或需要在 MoJing 平台（如 118.x.x.x:9801/online/...）配置表单、列表、字典、ER、SQL、事件、跨页传参、任务下发拆分、填报闭环、造数/清理数据时使用。覆盖：表单 JSON（html_json）结构与控件配置、relationSelect 关联弹窗、列表 custom_sql 与统计卡片、#{departMainId}/#{currentUser} 数据隔离、按钮出参/入参声明跨页传参、onFormMounted/onFormBeforeSubmit 事件 JS、按钮级 Groovy、批量子表加载、主记录+拆分记录任务下发模式、平台踩坑规避与数据库造数/修复。
---

# MoJing 低代码平台操作（魔镜）

在儒松/魔镜（JeecgBoot 系）在线开发平台配置表单、列表、SQL、事件并处理"任务下发→单位填报→闭环监控"类业务。本技能沉淀了真实项目（卫健委 IPv6 整改、年度考核）中验证过的正确配置方式与踩坑规避。

## 1. 平台对象模型（先读）

平台配置实体（在线开发模块）：
- **数据库设计**：建表/改字段/建字典/建 ER，改表后必须"同步到物理库"
- **表单设计**（`/online/form/OnlFormList`）：表单 JSON 存 `onl_form_head.html_json`，含 `list[]`（控件树）+ `config`（事件/布局）
- **列表设计**（`/online/list/OnlListPageList`）：`onl_list_head` + `onl_list_basic.custom_sql`（数据源 SQL）
- **SQL 管理**：命名 SQL 编码（如 SQL001），供表单 JS 用 `executeSqlByCode` 调用
- **ER 模型**：主表字段选**主键(id)**，子表字段选**关联字段(如 project_id)**，绝不能选子表主键

详细对象模型、字段含义、控件字典见 `references/platform-model.md`。

## 2. 通用工作流（每个任务都按此走）

1. **探查**：先连库/查页面配置确认现状（onl_form_head / onl_list_basic 的 JSON 与 SQL），不动手猜。数据库连接信息用占位符，见 `references/placeholders.md`。
2. **定位修改点**：改表单 JSON 走 `html_json`；改列表数据源走 `custom_sql`；改按钮/事件在设计器里手动配（**源码导入不执行按钮事件**）。
3. **小步验证**：每步改完用页面原始 SQL 重跑验证数据口径，或用 F12/查库确认。
4. **交付**：表单类任务交付修改后完整 JSON（可复制回设计器）；涉及已保存配置的同步更新数据库。

## 3. 核心能力导航

| 想做什么 | 读哪个文件 |
|---|---|
| 表单 JSON 结构 / 控件配置 / 隐藏字段 / 按钮 / 布局 | `references/form-design.md` |
| relationSelect 关联弹窗（选单位弹窗）完整配置 | `references/relation-select.md` |
| 列表 custom_sql / 统计子查询 / 卡片 / 查询条件 / 按钮显隐 | `references/list-sql.md` |
| 事件 JS（onFormMounted 等）/ 按钮级 Groovy / 出参入参跨页传参 | `references/events-groovy.md` |
| 批量子表（batch）加载与"多子表串数据"坑 | `references/batch-subform.md` |
| "任务下发→单位填报→闭环"业务模式（主/拆分记录、状态机、统计口径） | `references/ipv6-business.md` |
| 平台坑清单 / 排查套路（快速定位） | `references/troubleshooting.md` |
| 敏感信息如何替换为占位符 | `references/placeholders.md` |
| 直接操作数据库（造数/清理/迁移/软删） | `scripts/db_helper.py`（模板） |

## 4. 最高频结论（勿重试踩坑）

1. **表单级事件（Gy新增后 等）不触发**；按钮级「新增后/更新后」事件才生效，且**必须手动配**（源码导入不执行）。
2. **按钮显隐条件**：行内变量直接写变量名（`project_status == 'rectifying'`），**不加 `this.`**；前提是列表 SQL 必须 SELECT 出该列（隐藏列也要输出）。
3. **出参格式**（手册 4.4.4）：`{"id":"","arguments":[{"paramName":"...","agentValue":"${...}"}]}`；`paramName` 必须与表单字段 `model` 完全一致；列表按钮才能取行数据（列表头按钮取不到）。
4. **跨页传参**：源列表按钮出参 arguments → 目标列表「入参声明」声明同名参数 → 目标 SQL 用 `'#{参数名}'`（带引号）。
5. **数据隔离**：单位端 SQL 固定 `p.org_name = '#{departMainId}'`（org_name 存部门 ID）；当前用户 ID 用 `#{currentUser}`。
6. **隐藏字段必须 `hidden:true` + `display:true`**：`display:false` = 控件不渲染 = 不参与提交、出参填不进。
7. **同一表单内多个 batch 严禁共用同一个 model（表名）**——平台按 model 绑定数据，同 model 的 batch 共享数据、异步返回互相覆盖（"每次打开结果变一次"）。要换独立 model（列字段 model 不动）。
8. **"取最新一条"的子查询必须加空值过滤**：`AND c.current_progress IS NOT NULL AND TRIM(c.current_progress) <> ''`——完成类操作会插带状态但无正文的记录，顶掉有值进度。
9. **列表自定义 SQL**：禁 `select *`、结尾不加分号；卡片"全部"不能填任何条件；"自定义 SQL 排序"栏不要填排序代码（排序写进 SQL 内部）。
10. **日期控件被出参填充后提交值是数组** `[2026,10,29,0,0]` → 保存前 JS 转字符串，否则报"字段太长"。
11. **SQL 参数**：pymysql 直连执行含 `%` 通配符的 SQL 时，`%` 要写 `%%` 转义（占位符冲突）。

## 5. 数据安全约定

- 真实数据库地址/账号/密码/单位ID/用户ID 一律不写进本技能；使用 `references/placeholders.md` 的占位符（`{{DB_HOST}}` 等）。
- 造数/清理只动明确授权的表与记录；删数据用软删（`del_flag=1`）优先；改库前先 SELECT 确认目标。
