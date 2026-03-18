#!/bin/bash
# 一键更新脚本 - 在VPS上运行

echo "=== 博物社面试管理系统更新脚本 ==="

# 项目目录
PROJECT_DIR="/var/www/bws-interview/bws-interview"
cd "$PROJECT_DIR" || exit 1

# 停止旧服务
echo "1. 停止旧服务..."
pkill -f "python.*app.py" 2>/dev/null
sleep 1

# 备份数据库（如果有）
if [ -f "bws_interview.db" ]; then
    echo "2. 备份数据库..."
    cp bws_interview.db bws_interview.db.bak
fi

# 删除旧数据库（重新初始化）
echo "3. 重新初始化数据库..."
rm -f bws_interview.db

# 使用Python初始化数据库
python3 << 'PYEOF'
import sqlite3
import os

DB_PATH = 'bws_interview.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 用户表
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

# 面试场次表
cursor.execute('''
    CREATE TABLE interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        date TEXT,
        location TEXT,
        note TEXT,
        positions TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

# 面试房间表
cursor.execute('''
    CREATE TABLE rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        capacity INTEGER DEFAULT 5,
        FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
    )
''')

# 时间段表
cursor.execute('''
    CREATE TABLE time_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        max_count INTEGER DEFAULT 3,
        FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
    )
''')

# 面试官分配表
cursor.execute('''
    CREATE TABLE interview_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id INTEGER NOT NULL,
        interviewer_id INTEGER NOT NULL,
        time_slot_id INTEGER,
        room_id INTEGER,
        FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
        FOREIGN KEY (interviewer_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (time_slot_id) REFERENCES time_slots(id) ON DELETE CASCADE,
        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
    )
''')

# 报名表
cursor.execute('''
    CREATE TABLE applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        interview_id INTEGER NOT NULL,
        time_slot_id INTEGER NOT NULL,
        room_id INTEGER,
        first_position TEXT,
        second_position TEXT,
        phone TEXT,
        accept_adjust INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
        FOREIGN KEY (time_slot_id) REFERENCES time_slots(id) ON DELETE CASCADE,
        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
    )
''')

# 面试结果表
cursor.execute('''
    CREATE TABLE interview_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        interviewer_id INTEGER NOT NULL,
        attendance TEXT,
        result TEXT,
        comment TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
        FOREIGN KEY (interviewer_id) REFERENCES users(id) ON DELETE CASCADE
    )
''')

# 创建测试账号
cursor.execute("INSERT INTO users (username, password, name, role) VALUES ('admin', 'admin123', '系统管理员', 'admin')")

conn.commit()
conn.close()
print("数据库初始化完成！")
PYEOF

# 启动服务
echo "4. 启动服务..."
nohup python3 app.py > app.log 2>&1 &
sleep 2

# 检查是否启动成功
if ps aux | grep -v grep | grep "python3 app.py" > /dev/null; then
    echo "5. 服务启动成功！"
    echo ""
    echo "=== 登录信息 ==="
    echo "账号：admin"
    echo "密码：admin123"
    echo ""
    echo "请访问你的服务器IP进行登录"
else
    echo "启动失败，请检查日志："
    cat app.log
fi
