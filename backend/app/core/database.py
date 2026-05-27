# backend/app/core/database.py
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path(__file__).parent.parent.parent / "admin_law_review.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 规则表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT UNIQUE NOT NULL,
            rule_type TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            penalty TEXT,
            enabled INTEGER DEFAULT 1
        )
    """)

    # 案件表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            case_type TEXT NOT NULL,
            content TEXT NOT NULL,
            filing_date TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # 证据记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            evidence_type TEXT NOT NULL,
            content TEXT NOT NULL,
            submitted_date TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 处罚记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS penalty_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            penalty_type TEXT NOT NULL,
            amount REAL,
            basis_article TEXT,
            discretion_basis TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 分析结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            details_json TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 相似案件表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS similar_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            similar_case_id INTEGER NOT NULL,
            similarity_score REAL NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases(id),
            FOREIGN KEY (similar_case_id) REFERENCES cases(id)
        )
    """)

    # 审计日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # 初始化默认规则
    default_rules = [
        ("RULE_AL_001", "fact_unclear", "事实认定不清", "high", "责令重新调查", 1),
        ("RULE_AL_002", "evidence_incomplete", "证据链不完整", "high", "责令补充调查", 1),
        ("RULE_AL_003", "wrong_legal_basis", "处罚依据引用错误", "high", "撤销处罚决定", 1),
        ("RULE_AL_004", "unequal_penalty", "同案不同罚", "medium", "重新裁量", 1),
        ("RULE_AL_005", "procedure_defect", "程序瑕疵（期限/告知/签章/送达）", "medium", "补正程序", 1),
        ("RULE_AL_006", "discretion_abnormal", "自由裁量幅度异常", "medium", "重新裁量", 1),
        ("RULE_AL_007", "document_format", "文书格式不规范", "low", "整改", 1),
    ]

    for rule in default_rules:
        cursor.execute("""
            INSERT OR IGNORE INTO rules (rule_id, rule_type, description, severity, penalty, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rule)

    conn.commit()
    conn.close()

def log_audit(action: str, target_type: str = None, target_id: int = None, details: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (action, target_type, target_id, details)
        VALUES (?, ?, ?, ?)
    """, (action, target_type, target_id, details))
    conn.commit()
    conn.close()
