# 关联弹窗（relationSelect）配置

> 场景：表单里点"关联弹窗"按钮 → 弹出另一个**在线列表页**选数据 → 选中的值回填本表单。典型用途：选责任单位（从单位列表页多选）。

## 1. 控件结构（核心字段）

```json
{
  "type": "relationSelect",
  "label": "",
  "customCom": true,
  "icon": "icon-ai-code",
  "component": {
    "name": "modalSelect",
    "inject": {"$form": {"from": "$form", "default": null}},
    "components": {
      "OnlListPageRenderModel": {
        "name": "OnlListPageRenderModel",
        "components": {"listBuild": {"name": "ListBuild",
          "props": {"onlListHeadId": {"default": ""}, "height": {"default": "calc(100vh - 104px)"}, "width": {"default": "100%"}},
          "computed": {}, "methods": {}, "staticRenderFns": [], "_compiled": true, "_scopeId": "data-v-b99ff6e0", "_Ctor": {}}},
        "props": {"multiple": {"default": false}, "selectRows": {}, "relationComp": {"default": true}, "isBatchAdd": {"default": false}},
        "methods": {}, "staticRenderFns": [], "_compiled": true, "_scopeId": "data-v-a079f2f2", "_Ctor": {}
      }
    },
    "props": {"isEdit": {"type": null}, "dataJson": {"type": null}, "relationSaveField": {"type": null},
              "disabled": {"type": null}, "value": {"type": null}, "record": {"type": null}},
    "watch": {"dataJson": {"deep": true, "user": true}, "value": {"immediate": true, "user": true}},
    "computed": {}, "methods": {}, "staticRenderFns": [], "_compiled": true, "_scopeId": "data-v-dab3e98a", "_Ctor": {}
  },
  "options": {
    "defaultValue": null,
    "multiple": true,
    "disabled": false,
    "hidden": false,
    "width": "100%",
    "clearable": true,
    "placeholder": "请选择发布单位",
    "isCc": false,
    "labelCol": {"span": 4}, "isCustomLabelCol": false,
    "pageCode": "ListXXX",
    "pageName": "选择发布单位",
    "listId": "{{LIST_HEAD_ID}}",
    "listKey": "list_xxx",
    "comeParam": "{}",
    "tableName": "",
    "isMainTable": true,
    "backFillFields": [{"pageField": "", "formField": ""}],
    "allowEdit": false,
    "linkConfig": {"formCode": "", "listCode": "", "dataId": "", "openType": "router"},
    "saveField": "id",
    "showField": "name",
    "showSelectList": true
  },
  "model": "publish_org_id",
  "key": "relationSelect_xxx",
  "rules": [{"required": false, "message": "必填项"}],
  "events": {},
  "table": "nsm_annual_check"
}
```

## 2. 关键字段含义（容易配错）

| 字段 | 含义 | 易错点 |
|---|---|---|
| `pageCode` | 目标**列表页 code**（数据源页，如 ListXXX） | 必须存在且已发布 |
| `listId` / `listKey` | 目标列表 head id / 控件 key | 复制现有控件时一起改 |
| `saveField` | **存储字段**：选中后存入表单字段的值（建议 `id`，存唯一 ID） | 与 `model` 配合：model=表单存储字段名 |
| `showField` | **显示字段**：弹窗选中后回显到输入框的列名（建议 `name` 等名称列） | **常见坑：误配成 `id` → 回显是数字 ID 而不是单位名** |
| `multiple` | 是否多选（选多个单位） | 下发任务多选=true |
| `pageName` | 弹窗标题 | 可空，但配了体验好 |
| `comeParam` | 弹窗页入参（`{}` 默认） | 需要过滤时配 JSON |

## 3. 排查顺序（弹窗打不开/选不了/回显错）

1. 目标列表页存在且 online_status 正常？
2. `pageCode` 拼写/大小写？（列表 code 如 `ListXXX`）
3. 回显数字 → `showField` 应为 `name`；存储/关联错 → `saveField` 应为 `id`。
4. 弹窗空列表 → 目标列表 SQL 有问题或入参过滤过严。
5. `model` 存的是逗号串（多选）→ 目标表字段长度要够（如 varchar(200) 以上），超长会报"字段太长"。

## 4. 多选存储口径（任务下发场景）

- 多选时控件把选中值**逗号连接**存入 `model` 对应字段（如 `org_name` = `id1,id2,`），**自带尾逗号**。
- 处理：JS/groovy 里 `split(',')` 后 `trim()` 跳过空段；统计个数用 `TRIM(BOTH ',' FROM org_name)` 掐首尾再数段（不能只数逗号，尾逗号会多算一家）。
