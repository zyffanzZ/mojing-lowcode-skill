# 批量子表（batch）加载

> 场景：管理端查看详情弹窗里用多个 batch 子表展示"整改计划/整改进展/整改完成/补充材料"。数据由 `onFormMounted` JS 轮询拿到主键后，用 `executeSqlByCode` 查 SQL 编码并 `table.setValue(rows)` 写入。

## 1. batch 控件骨架

```json
{
  "type": "batch",
  "label": "整改进展情况",
  "icon": "icon-table",
  "options": { "width": "100%", "lineNums": 1, "disabled": false,
    "labelCol": {"span": 4}, "isCustomLabelCol": false,
    "linkConfig": {"formCode": "", "listCode": "", "dataId": "", "openType": "router"} },
  "list": [ /* 列控件：type input/date/uploadFile 等，model=子表字段名 */ ],
  "table": "nsm_ipv6_progress",   // ← model 绑定数据模型（关键坑见下）
  "model": "nsm_ipv6_progress",   // ← 与 table 一致
  "key": "batch_progress_records",
  "cusClass": [], "rules": [], "events": {}
}
```

- batch 本身绑定一个**子表 model**；`lineNums:1` 时页面默认渲染"序号 1"空行（空模板行，不是数据）。
- 列控件（list 内）的 model = 子表列字段名，type input/date/textarea/uploadFile。

## 2. 加载 JS（onFormMounted 模板）

```js
// 轮询等 project_id（出参传入的隐藏字段就绪）
let waitCnt = 0;
let timer = setInterval(() => {
  const pid = this.getWidget('project_id').value;
  if (pid || waitCnt >= 10) {
    clearInterval(timer);
    if (pid) { loadTables(pid); }
  }
  waitCnt++;
}, 300);

function loadTables(pid) {
  this.executeSqlByCode('SQL001', {}).then((res) => {
    const rows = (res && (res.data || res.rows || res.list)) || [];
    this.getWidget('batch_progress_records').setValue(rows);
  });
  // 其余子表同理，各用独立 SQL 编码
}
```

- 三选一壳：`res.data / res.rows / res.list`（兼容）。
- 轮询上限 300ms×10；project_id 为空不加载，避免空表清掉已加载数据。

## 3. 关键坑：多个 batch 严禁共用同一 model（表名）

- **平台按 model（表名）绑定 batch 数据模型，不按组件 key 独立**。两个 batch 的 `model` 相同（如都是 `nsm_ipv6_progress`）→ 共享同一份数据 → 两个异步 SQL 返回顺序不定、后返回覆盖先返回 → 子表"每次打开结果变一次"（有值/全空交替）。
- **解法**：给冲突的那个 batch 换**独立 model**（如 `nsm_ipv6_progress_complete_view`），**列字段的 model/table 一律不动**；三个子表各用独立 SQL 编码。
- 判断依据：多子表中只有一个一直正常，往往是它是唯一 model（如 `nsm_ipv6_remind`），无竞争者。

## 4. "取最新一条"空值过滤（联动）

完成/提交类操作常插一条"状态记录"但**正文为空**（如 B4 提交完成插 `progress_status='finished'` 但 `current_progress` 空）。任何 `ORDER BY create_time DESC LIMIT 1` 的最新值子查询都必须过滤空正文：

```sql
AND c.current_progress IS NOT NULL AND TRIM(c.current_progress) <> ''
```

否则最新进展列/详情子表会被空记录顶掉，显示空白。

## 5. 排查"子表有行但内容全空"四步套路

1. 查库确认数据在不在；
2. 核对 SQL 编码内容与 JS 引用编码一一对应（SQL 内容被串改会表现为"有行数但字段全空"）；
3. F12 打印 `getWidget('batch_xxx')` 组件属性 / SQL 返回行数 / 过滤后行数；
4. **单测法**：JS 只加载一个子表——单独正常 = 多子表互扰（查 model 是否重复）；单独也空 = setValue 或字段映射问题。

> batch 空行"序号 1"是 `lineNums:1` 默认渲染，不是查出了空数据，别误判。
