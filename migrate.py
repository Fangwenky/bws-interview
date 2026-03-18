#!/usr/bin/env python3
# 数据库迁移脚本 - 添加rooms表和时间段-房间关联

import sqlite3
import os

DB_PATH = 'bws_interview.db'

if not os.path.exists(DB_PATH):
    print("数据库文件不存在，请先运行 python3 -c \"from app import init_db; init_db()\"")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("开始数据库迁移...")

# 1. 创建rooms表（如果不存在）
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            capacity INTEGER DEFAULT 5,
            FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
        )
    ''')
    print("✓ rooms表已创建")
except Exception as e:
    print(f"rooms表创建错误: {e}")

# 2. 为time_slots添加room_id列（如果不存在）
try:
    cursor.execute('ALTER TABLE time_slots ADD COLUMN room_id INTEGER REFERENCES rooms(id)')
    print("✓ time_slots.room_id列已添加")
except:
    print("✓ time_slots.room_id列已存在")

# 3. 为applications添加room_id列（如果不存在）
try:
    cursor.execute('ALTER TABLE applications ADD COLUMN room_id INTEGER REFERENCES rooms(id)')
    print("✓ applications.room_id列已添加")
except:
    print("✓ applications.room_id列已存在")

# 4. 为interview_assignments添加room_id列（如果不存在）
try:
    cursor.execute('ALTER TABLE interview_assignments ADD COLUMN room_id INTEGER REFERENCES rooms(id)')
    print("✓ interview_assignments.room_id列已添加")
except:
    print("✓ interview_assignments.room_id列已存在")

conn.commit()
conn.close()

print("\n迁移完成！")
print("\n新的使用流程：")
print("1. 先添加面试场次")
print("2. 为场次添加房间")
print("3. 为每个房间添加时间段")
print("4. 分配面试官到时间段+房间")
print("5. 学生选择时间段+房间报名")
