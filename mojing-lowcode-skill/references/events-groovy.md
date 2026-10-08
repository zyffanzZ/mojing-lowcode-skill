# 事件 JS / Groovy / 传参机制

> 平台自定义脚本与前后脚本按钮均"待开发"——改数据/状态一律走"按钮出参带值 + 按钮级事件 Groovy"。**表单级新增后/更新后事件不触发**（自定义按钮提交不走表单级事件）。

## 1. 事件生效矩阵（已验证）

| 配置位置 | 是否生效 | 用途 |
|---|---|---|
| 表单级 `onFormMounted`（JS） | ✅ | 页面加载后执行（轮询、加载子表、格式化） |
| 表单级 `onFormBeforeSubmit`（JS） | ✅ | 提交前校验/字段转换（日期数组转字符串） |
| 表单级 `onFormAfterInsert/AfterUpdate`（groovy） | ❌ 不触发 | **勿用** |
| 按钮级「保存前」 | ✅ | 同 onFormBeforeSubmit 语义 |
| 按钮级「新增后」/「更新后」（groovy） | ✅ | **必须手动设计器粘贴**，源码导入不执行；新建走新增后、编辑走更新后，**两个都要粘同一份** |

## 2. 提交前 JS（onFormBeforeSubmit）常用模板

**日期数组转字符串**（出参填进日期控件后，提交值是数组 `[2026,10,29,0,0]`，不转会报"字段太长"）：

```js
const { formData } = args;
['require_finish_time', 'plan_finish_time'].forEach(function(key) {
  if (Array.isArray(formData[key])) {
    var d = formData[key];
    formData[key] = d[0] + '-' + String(d[1]).padStart(2, '0') + '-' + String(d[2]).padStart(2, '0')
      + ' ' + String(d[3]).padStart(2, '0') + ':' + String(d[4]).padStart(2, '0') + ':00';
  }
});
return true;
```

**置状态/时间（下发按钮示例）**：

```js
const { formData } = args;
formData.submit_status = 'submitted';
formData.project_status = 'wait_fill';
formData.material_status = 'none';
formData.org_name = (formData.org_name || '').toString() + ',';
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
formData.publish_time = now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate())
  + ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds());
return true;
```

**二次确认弹窗**（提交完成前）：

```js
const { formData } = args;
if (!confirm('确认提交？提交后任务即标记为已完成，不可撤回。')) {
  return false;
}
return true;
```

**调试**：保存前 JS 临时加 `console.log(JSON.stringify(formData))`，F12 看提交值（载荷平台加密，只能这样看）。

## 3. Groovy 规范（按钮级事件）

```groovy
import com.rusong.common.util.SpringContextUtils;
import com.rusong.modules.common.service.IEnhanceService;

def execute(formCode, businessData) {
    def service = SpringContextUtils.getBean(IEnhanceService.class);
    // businessData.get('字段名') 取提交值
    def projectId = businessData.get('project_id');
    if (projectId == null || projectId.toString().trim().length() == 0) {
        return;
    }
    service.updateBySql("UPDATE nsm_ipv6_project SET project_status = 'rectifying', submit_status = 'submitted' WHERE id = '" + projectId + "' AND del_flag = 0");
}
```

- 方法名固定 `def execute(formCode, businessData)`；取服务 `SpringContextUtils.getBean(IEnhanceService.class)`；抛异常 `throw new CustomException('...')`。
- IEnhanceService 常用：`searchBySqlCode(sqlCode, dataMap)` / `searchBySql(sql)` → `List<Map>`、`selectOne(sql)` → `Map`、`insertBySql(sql)` / `updateBySql(sql)` / `deleteBySql(sql)`、`save(erCode, dataMap)` / `saveBack(erCode, dataMap)`、`executeBySql(sql)`（执行 MySQL 函数）、`getFile(id)`（附件地址）、`sendMobileSms/sendBusinessSms/sendMsg`。
- **拼接 SQL 单引号转义**：字符串值先 `.replace("'", "''")` 再拼进 SQL。
- **防误改**：关键 ID 为空直接 return。
- 注意：更新状态时若管理端有"填报 x/y"统计，必须同步更新对应状态字段（如 B2 填计划要同时 `project_status='rectifying'` + `submit_status='submitted'`，否则填报统计一直是 0/N）。

## 4. 跨页传参（按钮出参 → 入参声明 → SQL 参数）

链路：源列表按钮「出参配置」→ 目标列表「入参声明」声明同名参数 → 目标 SQL 用 `'#{参数名}'`（**带引号**）。

**出参配置（列表按钮跳转，手册 4.4.4）**：

```json
{"id":"","arguments":[{"paramName":"project_name","agentValue":"${project_name}"},{"paramName":"project_id","agentValue":"${id}"}]}
```

- `paramName` 必须与目标页参数名/表单字段 model 一致；`agentValue=${当前行某列名}`（行内按钮才取得到行）。
- 编辑按钮加载记录用：`{"id":"${id}"}`。
- **inParams 格式（手册 5.2.3）是流程节点按钮/自定义按钮弹窗打开 list 用的**，列表按钮出参**不要用 inParams**（实测不生效）。

**入参声明（手册 4.4.5）**：入参标识/描述/查询操作符/入参类型/非空校验。
- 入参类型：文本参数选「**字符串**」（UUID 是文本！选数值会传不进导致列表空）；数值 ID 才选「数值」。

**目标 SQL**：`WHERE p.project_name='#{project_name}' AND p.org_name NOT LIKE '%,%'`。

坑：
- 入参会被平台当查询条件按同名列过滤——SQL 里 SELECT 出的 `project_id` 列必须与入参**同值**（如任务头 id），否则过滤后列表空。
- 调试法：先把 SQL 条件写死任务名测试——能出数据 = SQL 没问题，问题在参数链路；写死也报错 = SQL 本身问题。
- 跳转关联配置（list key）非必需，配了反而可能干扰，保持留空。

## 5. 按钮打开表单（新增/编辑/查看）

| 按钮类型 | 操作类型 | 说明 |
|---|---|---|
| 弹窗填新数据（填计划/报进度/提交完成） | **新增**（addData） | 出参初始化隐藏字段；"编辑"不认出参初始化 |
| 按 id 加载已有记录（查看详情/退回补充材料） | 编辑（editData）/查看（viewData） | 出参 `{"id":"${id}"}` |
| 只读打开表单 | 查看（viewData） | 表单内全 disabled |

- 表单按钮绑 ER：**必须绑含主表的 ER**（弹窗按 id 加载主表记录时尤其重要）。
- 查看任务内容类"列表头按钮"取不到行 → 出参 `${project_id}` 只能取**入参**（源行内按钮把 id 传进目标页入参，目标页列表头按钮再取入参）。
