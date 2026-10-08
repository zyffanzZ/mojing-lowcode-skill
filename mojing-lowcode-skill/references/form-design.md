# 表单设计（form JSON 实操）

> 修改已保存表单：读 `onl_form_head.html_json` → 改 → 写回（`UPDATE onl_form_head SET html_json=?`）。交付给用户时给完整 JSON，可复制回设计器源码框覆盖导入。

## 1. 布局（table）

- 每行 `trs[]` 一个，内含 4 个 `tds[]`（colspan 1/3 或 1/1/1/1 等），`widthList` 对应 4 列宽（如 17%/33%/17%/33%）。
- 标签列背景常用 `#EDF6FF`（浅蓝），值列 `#FFFFFF`。
- 全宽行：td colspan=4 放标题/批量子表。
- `options.currentTd/currentTr` 是设计器光标位置，可保留原值。

## 2. 控件骨架（input 示例）

```json
{
  "type": "input",
  "label": "",
  "labelHTML": "",
  "icon": "icon-write",
  "options": {
    "width": "100%", "defaultValue": null, "placeholder": "",
    "clearable": true, "maxLength": 100,
    "hidden": false, "display": true, "disabled": false,
    "labelCol": {"span": 4}, "isCustomLabelCol": false,
    "linkConfig": {"formCode": "", "listCode": "", "dataId": "", "openType": "router"}
  },
  "table": "nsm_xxx", "model": "field_name",
  "cusClass": [], "key": "input_xxx", "rules": [], "events": {}
}
```

- `table` = 表单绑定表；`model` = 字段名；`rules` 必填：`[{"required": true, "message": "必填项"}]`。
- 标签控件 `text` 的 `label` 就是显示文字；`showRequiredMark: true` 显示红星（与 rules 是两回事，规则校验看 rules）。

## 3. 常见控件要点

- **textarea**：`options.minRows/maxRows/maxLength`；textarea 没有 `table` 时放 model 即可（实际两者都存）。
- **date**：`format:"YYYY-MM-DD"`；`defaultValue:"${currentDate}"` 可默认今天。
- **uploadFile**：`bizPath:"files/ipv6_plan"`、`saveField:"single"`、`multiple:true`、`fileName:"file"`、`action:"/sys/common/upload"`；存储值是路径字符串（如 `/files/ipv6_plan/xxx.docx`）。
- **number**：`min/max/precision/step`，`disabled:true` 可做只读统计框。

## 4. 隐藏字段（传参/状态关键）

```json
{
  "type": "input",
  "options": { "width": "100%", "hidden": true, "display": true, "disabled": false, "maxLength": 36,
    "labelCol": {"span": 4}, "isCustomLabelCol": false,
    "linkConfig": {"formCode": "", "listCode": "", "dataId": "", "openType": "router"} },
  "table": "nsm_xxx", "model": "project_id",
  "cusClass": [], "key": "input_project_id",
  "rules": [{"required": true, "message": "必填项"}], "events": {}
}
```

**铁律：`hidden:true`（隐藏显示）+ `display:true`（渲染并参与提交）必须同时**。`display:false` = 控件不渲染 = 不参与提交、按钮出参也填不进 → 后续 groovy 拿不到值。若 hidden 未生效，用 CSS 兜底隐藏。

## 5. 按钮

```json
{
  "type": "btnBlock", "label": "按钮容器", "key": "btnBlock_main",
  "list": [
    { "type": "button", "label": "确认提交", "key": "button_submit",
      "options": { "type": "primary", "handle": "submit", "hidden": false, "disabled": false,
                   "editShow": true, "viewShow": true, "size": "default" } },
    { "type": "button", "label": "返回", "key": "button_close",
      "options": { "type": "default", "handle": "close", "editShow": true, "viewShow": true } }
  ],
  "options": { "hidden": false, "float": true }
}
```

- `handle`: `submit`（提交表单）/ `close`（关闭弹窗）。`back` 平台不认，勿用。
- 只读表单 = 所有控件 `disabled:true` + 按钮仅"关闭"。

## 6. 只读表单改造（详情弹窗套路）

从原表单 JSON 复制，改：全部控件 `disabled:true`；删提交类按钮；`config.onFormAfterInsert/onFormAfterUpdate` 的 groovy 清空；标题 text 改成详情名。按钮"查看/详情"用操作类型 **viewData/编辑** 打开（按 id 加载已有记录，不新增）。

## 7. 表单级 vs 按钮级事件（关键）

- `config.onFormMounted/onFormBeforeSubmit`（JS）：**表单级 JS 生效**（加载子表、提交前校验/转换）。
- `config.onFormAfterInsert/onFormAfterUpdate`（groovy）：**不触发**！自定义按钮提交不走表单级事件。
- **按钮级事件**：在设计器点按钮 → 事件 →「新增后」「更新后」粘 groovy；「保存前」粘 JS。**必须手动配，源码导入不执行**。
- 新建走 insert（新增后）、编辑走 update（更新后），**两个事件都要粘同一份代码**。

## 8. 表单交付格式

- 交付完整 JSON（缩进 2，中文不转义：`json.dumps(j, ensure_ascii=False, indent=2)`）。
- 说明改动点：改了什么控件/字段，其余未动。
