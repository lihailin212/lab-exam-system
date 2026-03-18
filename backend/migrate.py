"""
数据库迁移脚本 - 添加 total_questions 字段到 exams 表
"""
import sqlite3
import os

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "exam_system.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，无需迁移")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查 exams 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exams'")
    if not cursor.fetchone():
        print("exams 表不存在，无需迁移")
        conn.close()
        return

    # 检查 total_questions 列是否已存在
    cursor.execute("PRAGMA table_info(exams)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'total_questions' in column_names:
        print("total_questions 列已存在，无需迁移")
        conn.close()
        return

    # 添加 total_questions 列
    try:
        cursor.execute("ALTER TABLE exams ADD COLUMN total_questions INTEGER")
        conn.commit()
        print("成功添加 total_questions 列到 exams 表")
    except Exception as e:
        print(f"迁移失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
