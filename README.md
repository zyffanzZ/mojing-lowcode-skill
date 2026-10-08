# mojing-lowcode-skill

魔镜（MoJing / 儒松·维保保 / JeecgBoot 系）低代码平台的 AI 操作技能包。

让 AI 在魔镜在线开发平台上直接干活：配置表单、列表 SQL、关联弹窗、按钮出参、跨页传参、Groovy 事件、批量子表、任务下发拆分、数据造数与清理。所有配置方式均来自真实项目验证，踩坑结论直接给出，AI 读完即可照做。

## 这是什么

一个标准的 Agent Skill 文件夹（`mojing-lowcode-skill/`），包含：

- `SKILL.md` —— 技能总入口（触发说明 + 工作流 + 11 条最高频结论）
- `references/` —— 分域操作手册（表单 / 列表 SQL / 关联弹窗 / 事件与传参 / 批量子表 / 业务模式 / 踩坑清单 / 占位符约定）
- `assets/` —— 可直接复制的控件模板片段（隐藏字段 / 关联弹窗 / 批量子表 / 按钮）
- `scripts/` —— 数据库操作模板（探查 / 清数 / 造数 / 软删）

## 安装方法

### 方式一：git clone

```bash
git clone https://github.com/<你的账号>/<仓库名>.git
```

### 方式二：Download ZIP

在 GitHub 仓库页面点 **Code → Download ZIP**，解压。

### 放入 AI 的 skills 目录

克隆/解压后，把 `mojing-lowcode-skill/` **整个文件夹**（保持目录结构）放入你的 AI 的 skills 目录：

| AI / 环境 | skills 目录（按需选择） |
|---|---|
| Claude Code | `~/.claude/skills/` |
| 豆包工作 / 本技能运行环境 | `workspace/.user_skills/` |
| Cline / Roo Code | 各自的插件 skills 目录 |
| OpenClaw | `~/.openclaw/skills/`（按其文档） |
| 其他支持 Agent Skill 的框架 | 对应框架的 skills 目录 |

放置后重启会话，AI 即可自动识别（描述中包含"魔镜 / 表单设计 / 列表设计 / 关联弹窗 / 按钮出参 / Groovy"等关键词时会自动触发）。

## 使用前必读：替换占位符

示例与脚本中的环境信息已全部脱敏为占位符（见 `mojing-lowcode-skill/references/placeholders.md`）。首次使用前：

1. 打开 `scripts/db_helper.py`，将 `{{DB_HOST}} / {{DB_PORT}} / {{DB_USER}} / {{DB_PASSWORD}} / {{DB_NAME}}` 替换为你自己的数据库连接；
2. 造数脚本中的 `{{UNIT_ID_1}}` 等替换为你的真实单位 ID（执行 `SELECT id, depart_name FROM sys_depart` 可查）；
3. `{{FORM_CODE}} / {{LIST_CODE}} / {{SQL_CODE}}` 等以你的平台实际存在的编码为准（可在 `onl_form_head` / `onl_list_head` / SQL 管理中查询）。

> 注意：本技能中"单位/部门 ID"、"任务头 + 拆分记录"等概念均基于实际业务模式（一任务下发多家单位），具体表名以你的项目为准，先探查再动手。

## 能力清单

- **表单设计**：表单 JSON（html_json）结构、控件配置、隐藏字段（hidden+display）、按钮 handle、只读表单改造
- **关联弹窗**：relationSelect 完整配置（pageCode / saveField / showField / multiple）与故障排查
- **列表 SQL**：`#{departMainId}` / `#{currentUser}` 数据隔离、统计子查询、卡片配置、查询条件、按钮显隐
- **事件与脚本**：onFormMounted / onFormBeforeSubmit 事件 JS、按钮级 Groovy（IEnhanceService）、日期数组转字符串、二次确认
- **跨页传参**：按钮出参 arguments → 入参声明 → SQL `'#{参数名}'`，列表头按钮与行内按钮差异
- **批量子表**：batch 加载、多 batch 严禁共用 model 的坑、"取最新一条"空值过滤
- **业务闭环**：任务下发（主记录 + 拆分记录）→ 单位填报 → 提交完成 → 补充材料 → 管理端监控，含造数/清理/修复脚本

## 内容结构

```text
mojing-lowcode-skill/
├── SKILL.md                        # 技能总入口（必读）
├── references/
│   ├── platform-model.md           # 平台对象模型、配置表、控件字典
│   ├── form-design.md              # 表单 JSON 实操
│   ├── relation-select.md          # 关联弹窗配置
│   ├── list-sql.md                 # 列表数据源 SQL / 统计 / 卡片 / 按钮
│   ├── events-groovy.md            # 事件 JS / Groovy / 跨页传参
│   ├── batch-subform.md            # 批量子表加载与踩坑
│   ├── ipv6-business.md            # 任务下发→填报→闭环 业务模式
│   ├── troubleshooting.md          # 平台坑清单与排查套路
│   └── placeholders.md             # 占位符约定（脱敏规范）
├── assets/
│   └── form-templates.json         # 控件模板片段合集
└── scripts/
    └── db_helper.py                # 数据库操作模板（探查/清数/造数/软删）
```

## 安全说明

- 本仓库不包含任何真实数据库地址、账号密码、单位 ID 或内部编码，均为占位符 + 说明；
- 使用方在公开环境使用时，请自行确保不提交真实凭据。

## License

MIT
