# 平台对象模型（MoJing 在线开发）

> 儒松/魔镜 V7.x，JeecgBoot 系低代码。所有页面配置存在 MySQL 的在线开发表中。

## 1. 核心配置表

| 表 | 用途 | 关键列 |
|---|---|---|
| `onl_form_head` | 表单（在线表单） | `form_code`（如 FormXXX）、`form_name`、`table_name`、`html_json`（**完整表单 JSON**）、`del_flag` |
| `onl_list_head` | 列表页（在线列表） | `id`、`name`、`code`（如 ListXXX）、`online_status` |
| `onl_list_basic` | 列表数据源 | `list_id`、`list_key`、`custom_sql`（**列表 SQL**） |
| `onl_list_button` | 列表按钮 | `list_id`、`button_name`、`open_type`（addData/editData/viewData）、`form_code`/`page_code`（关联目标）、`show_condition`（显隐条件）、`out_variable_config`（出参 JSON） |
| `sys_depart` | 部门/单位 | `id`、`depart_name`、`parent_id`、`org_code`（单位名称/层级） |
| `sys_user_depart` | 用户-部门关系 | `user_id`、`dep_id`（用于 #{currentUser} 推下级单位） |

探查套路：`SELECT id, form_code, form_name, html_json FROM onl_form_head WHERE form_code='FormXXXX' AND del_flag=0`；`SELECT id, list_id, custom_sql FROM onl_list_basic WHERE list_id='<list_head.id>'`。

## 2. 表单 JSON（html_json）总结构

```json
{
  "list": [ ...控件树... ],
  "config": { "onFormMounted": {"js": "..."}, "onFormBeforeSubmit": {"js": "..."},
              "onFormCreated": {}, "onFormAfterSubmit": {},
              "onFormBeforeInsert": {}, "onFormAfterInsert": {"groovy": ""},
              "onFormBeforeUpdate": {}, "onFormAfterUpdate": {"groovy": ""},
              "layout": "horizontal", "labelWidth": 100, ... }
}
```

- `list[]`：顶层控件数组。**table（表格布局）** 是容器：`trs[].tds[]` 每个 td 有 `colspan/rowspan/backgroundColor/list[]`，控件放在 td.list 里；每行 4 个 td（1+1+1+1 或 1+3 等）。table 之外可放隐藏字段控件、btnBlock 按钮容器。
- 每个控件通用字段：`type`、`label`、`icon`、`options`、`model`（绑定字段名）、`key`（唯一标识）、`rules`（校验）、`table`（绑定的数据表）、`events`。
- `options` 通用：`hidden/display/disabled/width/placeholder/labelCol/linkConfig`。
- 按钮容器 `btnBlock`：`list[]` 里放 `button` 控件，`options.handle` = `submit`（确认提交）/ `close`（关闭）/ `back`（平台不认，勿用）。

## 3. 控件字典（type）

| type | 用途 | 关键 options |
|---|---|---|
| `text` | 静态文本/标题/标签 | textAlign/fontSize/isBold/showRequiredMark |
| `input` | 单行文本 | maxLength/disabled/clearable |
| `textarea` | 多行文本 | minRows/maxRows/maxLength |
| `date` | 日期时间 | format(YYYY-MM-DD)/range/showTime |
| `selectRadio` | 静态单选 | options[{value,label}]（动态用 dynamic:static/dict/distal） |
| `select` | 下拉（字典） | dynamic:"dict"/dynamicKey:字典编码 |
| `number` | 数字 | min/max/precision |
| `uploadFile` | 附件 | bizPath/saveField:"single"/multiple/fileName:"file"/action:"/sys/common/upload" |
| `relationSelect` | 关联弹窗选数据 | 见 `relation-select.md` |
| `batch` | 子表（列表内嵌表格） | list[]（列控件）+ model=子表名 + options(lineNums/disabled) |
| `btnBlock` | 按钮容器 | 内含 button |
| `input`(隐藏) | 传 ID/状态 | hidden:true + **display:true** |

## 4. 命名规范（本项目约定）

- 列表/表单名：`端名-页面名[-类型]`（管理端=查看方、单位端=填报方）。例：`卫健委端-任务详情`、`单位端-我的整改任务`。
- 表名：`系统名_模块_子模块` ≤3 下划线（`nsm_ipv6_project`）；字段 `名_名` ≤2 下划线。
- 平台内置字段 8 个（建表自动带出）：`id varchar(36) 主键`、`create_by`、`create_time datetime(3)`、`update_by`、`update_time`、`del_flag int default 0`、`tenant_id`、`sys_org_code`。

## 5. ER 模型

- 主表字段选**主键（id）**；子表字段选**关联字段**（如 project_id）；**绝不能选子表自己的主键**（否则关联全错）。
- 表单/按钮绑 ER：按钮弹窗表单必须绑**含主表的 ER**（曾误选子表 ER 导致按 id 加载错记录）。

## 6. SQL 管理编码

- 在"SQL 管理"里建命名 SQL（如 SQL001 整改进度 / SQL002 整改完成 / SQL003 补充材料）。
- 表单 JS 用 `this.executeSqlByCode('SQL001', {})` 调用，返回 `res.data/res.rows/res.list` 数组（兼容多种壳）。
- 改完 SQL 编码内容要点「确定」保存；内容被串改时表现为"有行数但字段全空"——根治用新建编码。
