# 业务模式：任务下发 → 单位填报 → 闭环监控

> 本页沉淀"管理端建任务下发多家单位、单位端各自填报、管理端监控/要求补充材料"的完整业务模式（卫健委 IPv6 整改任务为落地案例）。同类业务（年度考核等）直接照搬。

## 1. 核心数据模型：主记录 + 拆分记录

**一个任务下发 N 家单位 = 1 条主记录 + N 条拆分记录（同一张表 nsm_ipv6_project）**：

| 记录 | org_name 值 | 其他关键字段 |
|---|---|---|
| 主记录（任务头） | 逗号连接的单位 ID 串（`id1,id2,` 自带尾逗号） | submit_status=submitted（已下发）、publish_time=下发时间 |
| 拆分记录（每单位一条） | 单个单位 ID（无逗号） | submit_status=draft（未填报）、project_status=wait_fill（待填报）、material_status=none |

- 管理端列表只显示主记录；统计（填报 x/y、完成 x/y、逾期数、任务状态）看拆分记录。
- 区分：主记录 `org_name LIKE '%,%'`；拆分记录 `org_name NOT LIKE '%,%'`。
- **造数/修数据时最容易漏**：只建主记录不建拆分记录 → 管理端统计全 0、任务状态误判"已结束"、详情页点开没单位。

## 2. 状态机（三态驱动）

| 维度 | 字段 | 取值 | 流转 |
|---|---|---|---|
| 任务状态 | project_status | wait_fill 待填报 → rectifying 整改中 → finished 已完成 | 填计划/报进度 → rectifying；提交完成 → finished（管理端不审核，直接生效） |
| 填报状态 | submit_status | draft 未填报 → submitted 已填报 | 填计划/报进度/提交完成 后置 submitted |
| 材料状态 | material_status | none 无 → not_submitted 待补充 → finished 已补充 | 管理端要求补充 → not_submitted；单位补交 → finished |

- **逾期判定**（SQL 推导）：`NOW() > plan_finish_time AND project_status <> 'finished'` → 逾期。
- 材料状态**只有三态**：none / not_submitted / finished。废弃的 delay（已上报延期）不再使用——字典项可保留但不用，存量数据按"无"处理。
- **业务一致性铁律（演示造数必查）**：
  - 有补充材料（remind 有记录）的单位 = 完成提交被退回后补交 → **必须先有整改完成填报**（complete_time 等完成字段 + progress 完成记录 + material_status 曾流转）；
  - **逾期任务不该有完成填报**（填了完成状态就是已完成，不是逾期）——逾期演示单位 = 无完成字段、无完成 progress；
  - 提交完成 = 必然有 progress 完成记录（progress_status='finished'，可带空正文，见 batch-subform 空值过滤）。

## 3. 闭环流程（9 步）

```text
管理端新建任务（M2）→ 保存草稿（不下发）或保存并下发
  ├─ 下发 = 按钮级 groovy 按 org_name 拆单位循环 INSERT 拆分记录（带防重）
单位端收到任务（U1 列表）→ 填写整改计划（U2，plan 子表）
  └─ 提交后 project_status→rectifying、submit_status→submitted
单位端上报整改进度（U3，progress 表，可多次）→ 同步提交状态
单位端提交整改完成情况（U4）
  └─ project 写 complete_time/rectify_result/complete_desc/complete_material
     + progress 插一条 finished 记录；material_status 保持 none；project_status→finished
管理端监控（M1 列表统计 + M3 任务详情各单位落实情况）
管理端要求补充材料（M4）→ remind 插记录（remind_type=material_supply、view_status=unviewed）
  + project.material_status→not_submitted
单位端补充整改材料（U5）→ remind 更新 supply_material/supply_desc/supply_time、view_status→viewed
  + project.material_status→finished
```

## 4. 关键表字段（nsm_ipv6_project，改造后）

| 字段 | 说明 |
|---|---|
| project_name | 任务名称（同名任务 = 主+拆分同值） |
| org_name | 主记录=逗号单位串 / 拆分=单单位 ID |
| publish_time | 下发时间 |
| plan_finish_time | 要求完成时间 |
| work_require | 整改工作要求 |
| rectify_target / target_type | 整改对象 / 类型 |
| task_file | 任务附件路径 |
| submit_status / project_status / material_status | 三态驱动字段 |
| complete_time / rectify_result / complete_desc / complete_material | 整改完成情况 |
| create_time | 下发时间线（排序用） |

子表：`nsm_ipv6_plan`（计划，project_id 关联）、`nsm_ipv6_progress`（进度，project_id 关联，可多条）、`nsm_ipv6_remind`（补充材料，biz_id=project 记录 id、remind_type='material_supply'）。

## 5. 管理端详情页（列表详情页模式）

- 载体：在线开发列表（列表设计），不是门户图表。
- 入参 `project_name`（任务名）+ `project_id`（任务头 id，字符串类型）→ SQL `WHERE p.project_name='#{project_name}' AND p.org_name NOT LIKE '%,%'` 只显示该任务各单位。
- 单位名称 join `sys_depart`；时间列 `DATE_FORMAT`；`is_overdue` CASE 推导。
- **project_id 列必须是任务头 id（子查询）**：`(SELECT h.id FROM nsm_ipv6_project h WHERE h.project_name=p.project_name AND h.org_name LIKE '%,%' AND h.del_flag=0 LIMIT 1) AS project_id`——入参按同名列过滤，值一致列表才有数据。
- 各列表按钮（查看任务内容/退回补充材料/查看详情）显隐与出参见 `events-groovy.md`。

## 6. 造数（模拟真实数据给客户演示）

- 只对**有实际账号的单位**造数（用户要求），未建账号的单位不插。
- 造数前先清空测试数据：删关联子表（plan/progress/remind）→ 删 project 拆分记录 → 删主记录；**用软删优先**（del_flag=1）或记录原 id。
- 每任务必须：主记录 1 条 + 拆分记录 N 条；状态组合要**业务自洽**（见 §2 铁律）。
- 造数脚本模板见 `scripts/db_helper.py`。
