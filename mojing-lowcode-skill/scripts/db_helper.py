#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MoJing 平台数据库操作模板（脱敏）。
用途：探查表结构 / 造模拟数据 / 清理测试数据 / 迁移关联 / 软删。
使用前替换下方 CONFIG 中的占位符为你自己的环境值（见 references/placeholders.md）。

连接信息（占位符，勿写真实值）：
  {{DB_HOST}}:{{DB_PORT}} / {{DB_USER}} / {{DB_PASSWORD}} / db={{DB_NAME}}
"""
import pymysql

CONFIG = {
    "host": "{{DB_HOST}}",
    "port": int("{{DB_PORT}}"),
    "user": "{{DB_USER}}",
    "password": "{{DB_PASSWORD}}",
    "database": "{{DB_NAME}}",
    "charset": "utf8mb4",
}

# 业务表（IPv6 整改案例；你的项目可能不同，先 SHOW TABLES 确认）
TABLE_PROJECT = "nsm_ipv6_project"    # 任务主记录 + 单位拆分记录
TABLE_PLAN = "nsm_ipv6_plan"          # 整改计划（project_id 关联）
TABLE_PROGRESS = "nsm_ipv6_progress"  # 整改进度（project_id 关联，可多条）
TABLE_REMIND = "nsm_ipv6_remind"      # 补充材料（biz_id=project.id）


def get_conn():
    return pymysql.connect(**CONFIG)


def query(conn, sql, args=None):
    """只读查询。注意：SQL 中 '%' 通配符在 pymysql 占位符模式下要写 '%%' 转义。"""
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def execute(conn, sql, args=None):
    """写操作（INSERT/UPDATE/DELETE）。调用方负责 conn.commit()。"""
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.rowcount


def soft_delete(conn, table, where_sql, args=None):
    """软删优先：del_flag=1，保留记录可恢复。"""
    return execute(conn, f"UPDATE {table} SET del_flag = 1 WHERE {where_sql}", args)


def probe(conn):
    """探查：列出 nsm_ipv6 相关表与 project 表结构。"""
    print("== tables ==")
    for r in query(conn, "SHOW TABLES LIKE 'nsm_ipv6%'"):
        print(r)
    print("== project columns ==")
    for r in query(conn, "SHOW COLUMNS FROM " + TABLE_PROJECT):
        print(r["Field"], r["Type"], r["Null"], r["Default"])


def clear_task(conn, project_name):
    """
    清理某个任务的全部测试数据（含关联子表）。
    顺序：remind/progress/plan（按 project_id 或 biz_id 关联）→ project 拆分记录 → 主记录。
    默认软删；如需物理删除，把 UPDATE ... SET del_flag=1 换为 DELETE。
    """
    # 1) 先找出该任务全部 project 记录 id（主记录 + 拆分记录）
    rows = query(
        conn,
        "SELECT id, org_name FROM %s WHERE project_name = %%s AND del_flag = 0" % TABLE_PROJECT,
        (project_name,),
    )
    ids = [r["id"] for r in rows]
    if not ids:
        print("no records for task:", project_name)
        return
    in_clause = ",".join(["%s"] * len(ids))
    print("target ids:", ids)

    # 2) 清理关联子表（软删）
    soft_delete(conn, TABLE_REMIND, f"biz_id IN ({in_clause})", ids)
    soft_delete(conn, TABLE_PROGRESS, f"project_id IN ({in_clause})", ids)
    soft_delete(conn, TABLE_PLAN, f"project_id IN ({in_clause})", ids)

    # 3) 清理 project 记录
    soft_delete(conn, TABLE_PROJECT, f"id IN ({in_clause})", ids)
    conn.commit()
    print("cleared task:", project_name)


def seed_split_records(conn, project_name, unit_ids, **kwargs):
    """
    造数：为一个已存在的任务主记录补建 N 条单位拆分记录。
    前提：任务头已存在（org_name 为逗号单位串）。缺拆分记录 = 管理端统计全 0。
    业务铁律：逾期单位不要写 complete_time 等完成字段；有补充材料的单位必须已有完成填报。
    """
    for uid in unit_ids:
        sql = (
            f"INSERT INTO {TABLE_PROJECT} "
            "(id, project_name, project_status, submit_status, material_status, org_name, "
            " plan_finish_time, work_require, rectify_target, target_type, task_file, publish_time, create_time, del_flag) "
            "VALUES (UUID(), %s, 'wait_fill', 'draft', 'none', %s, "
            " %s, %s, %s, %s, %s, NOW(), NOW(), 0)"
        )
        execute(conn, sql, (
            project_name,
            uid,
            kwargs.get("plan_finish_time"),    # 形如 '2026-12-31 00:00:00'
            kwargs.get("work_require", ""),
            kwargs.get("rectify_target", ""),
            kwargs.get("target_type", ""),
            kwargs.get("task_file", ""),
        ))
    conn.commit()
    print(f"seeded {len(unit_ids)} split records for task:", project_name)


def main():
    conn = get_conn()
    try:
        probe(conn)
        # 示例：清理 + 造数（替换为实际任务名与单位 ID，单位 ID 从 sys_depart 查）
        # clear_task(conn, "{{TASK_NAME}}")
        # seed_split_records(conn, "{{TASK_NAME}}", ["{{UNIT_ID_1}}", "{{UNIT_ID_2}}"],
        #                    plan_finish_time="2026-12-31 00:00:00",
        #                    work_require="完成 IPv6 地址改造并上报")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
