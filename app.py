#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博物社面试管理系统 - 后端代码
作者：博物社技术组
描述：用于管理社团招新面试流程的系统
"""

import os
import json
import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'bws-interview-secret-key-2025'  # 用于session加密

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'bws_interview.db')

# ============================================================
# 数据库初始化与操作函数
# ============================================================

def init_db():
    """初始化数据库，创建所有必要的表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'interviewer', 'student')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 面试场次表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
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
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            capacity INTEGER DEFAULT 5,
            FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
        )
    ''')

    # 时间段表（绑定房间，每个房间每个时间段最多1人）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER NOT NULL,
            room_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
        )
    ''')

    # 面试官分配表（一个面试官可以负责多个场次或多个时间段或房间）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_assignments (
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
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            interview_id INTEGER NOT NULL,
            time_slot_id INTEGER NOT NULL,
            room_id INTEGER,
            first_position TEXT,
            second_position TEXT,
            phone TEXT,
            accept_adjust INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'cancelled')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
            FOREIGN KEY (time_slot_id) REFERENCES time_slots(id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
        )
    ''')

    # 面试结果表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            interviewer_id INTEGER NOT NULL,
            attendance TEXT CHECK(attendance IN ('present', 'absent')),
            result TEXT CHECK(result IN ('pass', 'fail', 'pending')),
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
            FOREIGN KEY (interviewer_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

    # 创建默认测试账号（如果不存在）
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # 管理员
        cursor.execute("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
                      ('admin', 'admin123', '系统管理员', 'admin'))
        # 面试官
        cursor.execute("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
                      ('interviewer1', 'inter123', '张面试官', 'interviewer'))
        cursor.execute("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
                      ('interviewer2', 'inter123', '李面试官', 'interviewer'))
        # 测试学生
        cursor.execute("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
                      ('2023001', 'student123', '王小明', 'student'))
        cursor.execute("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
                      ('2023002', 'student123', '李小红', 'student'))
        conn.commit()
        print("已创建默认测试账号！")

    conn.close()


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以通过列名访问
    return conn


# ============================================================
# 装饰器：登录验证和权限检查
# ============================================================

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """角色权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                return jsonify({'error': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================
# 路由：首页和认证
# ============================================================

@app.route('/')
def index():
    """首页 - 根据角色跳转到对应页面"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'interviewer':
        return redirect(url_for('interviewer_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))


@app.route('/login')
def login():
    """登录页面"""
    return render_template('login.html')


@app.route('/register')
def register():
    """注册页面"""
    return render_template('register.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    """登录接口"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': '请输入用户名和密码'})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})

    if user['password'] != password:
        return jsonify({'success': False, 'message': '密码错误'})

    # 登录成功，保存session
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['name'] = user['name']
    session['role'] = user['role']

    return jsonify({'success': True, 'role': user['role']})


@app.route('/api/register', methods=['POST'])
def api_register():
    """注册接口（学生）"""
    data = request.get_json()
    username = data.get('username', '').strip()  # 学号
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()

    if not username or not password or not name:
        return jsonify({'success': False, 'message': '请填写完整信息'})

    # 验证学号格式（纯数字）
    if not username.isdigit():
        return jsonify({'success': False, 'message': '学号必须是纯数字'})

    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查学号是否已注册
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '该学号已注册'})

    # 创建学生账号
    cursor.execute(
        "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
        (username, password, name, 'student')
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '注册成功，请登录'})


@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))


# ============================================================
# 路由：管理员后台
# ============================================================

@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    """管理员仪表盘"""
    return render_template('admin/dashboard.html')


@app.route('/admin/interviews')
@login_required
@role_required('admin')
def admin_interviews():
    """面试场次管理"""
    return render_template('admin/interviews.html')


@app.route('/admin/interviewers')
@login_required
@role_required('admin')
def admin_interviewers():
    """面试官管理"""
    return render_template('admin/interviewers.html')


@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    """用户管理"""
    return render_template('admin/users.html')


@app.route('/admin/results')
@login_required
@role_required('admin')
def admin_results():
    """面试结果查看"""
    return render_template('admin/results.html')


# ============================================================
# API：面试场次管理（管理员）
# ============================================================

@app.route('/api/interviews', methods=['GET'])
@login_required
def get_interviews():
    """获取所有面试场次"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interviews ORDER BY created_at DESC")
    interviews = cursor.fetchall()
    conn.close()

    result = []
    for interview in interviews:
        item = dict(interview)
        # 解析职位JSON
        if item.get('positions'):
            item['positions'] = json.loads(item['positions'])
        else:
            item['positions'] = []
        result.append(item)

    return jsonify(result)


@app.route('/api/interviews', methods=['POST'])
@login_required
@role_required('admin')
def create_interview():
    """创建面试场次"""
    data = request.get_json()
    title = data.get('title', '').strip()
    date = data.get('date', '')
    location = data.get('location', '').strip()
    note = data.get('note', '').strip()
    positions = data.get('positions', [])

    if not title:
        return jsonify({'success': False, 'message': '请输入面试标题'})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interviews (title, date, location, note, positions) VALUES (?, ?, ?, ?, ?)",
        (title, date, location, note, json.dumps(positions, ensure_ascii=False))
    )
    conn.commit()
    interview_id = cursor.lastrowid
    conn.close()

    return jsonify({'success': True, 'id': interview_id})


@app.route('/api/interviews/<int:interview_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_interview(interview_id):
    """更新面试场次"""
    data = request.get_json()
    title = data.get('title', '').strip()
    date = data.get('date', '')
    location = data.get('location', '').strip()
    note = data.get('note', '').strip()
    positions = data.get('positions', [])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE interviews SET title=?, date=?, location=?, note=?, positions=? WHERE id=?",
        (title, date, location, note, json.dumps(positions, ensure_ascii=False), interview_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/interviews/<int:interview_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_interview(interview_id):
    """删除面试场次"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interviews WHERE id = ?", (interview_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ============================================================
# API：时间段管理
# ============================================================

@app.route('/api/interviews/<int:interview_id>/time-slots', methods=['GET'])
@login_required
def get_time_slots(interview_id):
    """获取面试场次的时间段（含房间信息）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取时间段（包含房间信息）
    cursor.execute('''
        SELECT ts.*, r.name as room_name
        FROM time_slots ts
        LEFT JOIN rooms r ON ts.room_id = r.id
        WHERE ts.interview_id = ?
        ORDER BY ts.start_time
    ''', (interview_id,))
    time_slots = cursor.fetchall()

    result = []
    for slot in time_slots:
        item = dict(slot)
        # 计算已报名人数（每个时间段最多1人）
        cursor.execute(
            "SELECT COUNT(*) FROM applications WHERE time_slot_id = ? AND status = 'pending'",
            (slot['id'],)
        )
        item['applied_count'] = cursor.fetchone()[0]
        # 该时间段是否已满（每个房间每个时间段最多1人）
        item['is_full'] = item['applied_count'] >= 1
        result.append(item)

    conn.close()
    return jsonify(result)


@app.route('/api/interviews/<int:interview_id>/time-slots', methods=['POST'])
@login_required
@role_required('admin')
def create_time_slot(interview_id):
    """添加时间段（绑定房间）"""
    data = request.get_json()
    start_time = data.get('start_time', '').strip()
    end_time = data.get('end_time', '').strip()
    room_id = data.get('room_id')

    if not start_time or not end_time:
        return jsonify({'success': False, 'message': '请填写开始和结束时间'})

    if not room_id:
        return jsonify({'success': False, 'message': '请选择房间'})

    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查该房间该时间段是否已存在
    cursor.execute(
        "SELECT id FROM time_slots WHERE interview_id = ? AND room_id = ? AND start_time = ?",
        (interview_id, room_id, start_time)
    )
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '该房间该时间段已存在'})

    cursor.execute(
        "INSERT INTO time_slots (interview_id, room_id, start_time, end_time) VALUES (?, ?, ?, ?)",
        (interview_id, room_id, start_time, end_time)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/time-slots/<int:slot_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_time_slot(slot_id):
    """删除时间段"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM time_slots WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ============================================================
# API：面试房间管理
# ============================================================

@app.route('/api/interviews/<int:interview_id>/rooms', methods=['GET'])
@login_required
def get_rooms(interview_id):
    """获取面试场次的房间列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*,
               (SELECT COUNT(*) FROM applications a
                WHERE a.room_id = r.id AND a.status = 'pending') as applied_count
        FROM rooms r
        WHERE r.interview_id = ?
        ORDER BY r.name
    ''', (interview_id,))
    rooms = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rooms])


@app.route('/api/interviews/<int:interview_id>/rooms', methods=['POST'])
@login_required
@role_required('admin')
def create_room(interview_id):
    """添加面试房间"""
    data = request.get_json()
    name = data.get('name', '').strip()
    capacity = data.get('capacity', 5)

    if not name:
        return jsonify({'success': False, 'message': '请输入房间名称'})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO rooms (interview_id, name, capacity) VALUES (?, ?, ?)",
        (interview_id, name, capacity)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_room(room_id):
    """删除面试房间"""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 将该房间的报名记录的房间ID设为NULL
    cursor.execute("UPDATE applications SET room_id = NULL WHERE room_id = ?", (room_id,))
    cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ============================================================
# API：面试官分配
# ============================================================

@app.route('/api/interviews/<int:interview_id>/assignments', methods=['GET'])
@login_required
def get_assignments(interview_id):
    """获取面试官分配"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ia.*, u.name as interviewer_name, ts.start_time, ts.end_time, r.name as room_name
        FROM interview_assignments ia
        JOIN users u ON ia.interviewer_id = u.id
        LEFT JOIN time_slots ts ON ia.time_slot_id = ts.id
        LEFT JOIN rooms r ON ia.room_id = r.id
        WHERE ia.interview_id = ?
    ''', (interview_id,))
    assignments = cursor.fetchall()
    conn.close()

    return jsonify([dict(a) for a in assignments])


@app.route('/api/interviews/<int:interview_id>/assignments', methods=['POST'])
@login_required
@role_required('admin')
def create_assignment(interview_id):
    """分配面试官"""
    data = request.get_json()
    interviewer_id = data.get('interviewer_id')
    time_slot_id = data.get('time_slot_id')
    room_id = data.get('room_id')

    if not interviewer_id:
        return jsonify({'success': False, 'message': '请选择面试官'})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interview_assignments (interview_id, interviewer_id, time_slot_id, room_id) VALUES (?, ?, ?, ?)",
        (interview_id, interviewer_id, time_slot_id, room_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_assignment(assignment_id):
    """删除面试官分配"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interview_assignments WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ============================================================
# API：面试者报名
# ============================================================

@app.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    """获取报名列表（根据角色返回不同数据）"""
    role = session.get('role')
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    if role == 'admin':
        # 管理员查看所有报名
        cursor.execute('''
            SELECT a.*, u.name as student_name, u.username as student_number,
                   i.title as interview_title, ts.start_time, ts.end_time,
                   r.name as room_name
            FROM applications a
            JOIN users u ON a.student_id = u.id
            JOIN interviews i ON a.interview_id = i.id
            JOIN time_slots ts ON a.time_slot_id = ts.id
            LEFT JOIN rooms r ON a.room_id = r.id
            ORDER BY a.created_at DESC
        ''')
    elif role == 'interviewer':
        # 面试官查看自己负责的报名（按房间筛选）
        cursor.execute('''
            SELECT a.*, u.name as student_name, u.username as student_number,
                   i.title as interview_title, ts.start_time, ts.end_time,
                   r.name as room_name
            FROM applications a
            JOIN users u ON a.student_id = u.id
            JOIN interviews i ON a.interview_id = i.id
            JOIN time_slots ts ON a.time_slot_id = ts.id
            LEFT JOIN rooms r ON a.room_id = r.id
            WHERE a.interview_id IN (
                SELECT interview_id FROM interview_assignments WHERE interviewer_id = ?
            )
            AND (a.room_id IN (
                SELECT room_id FROM interview_assignments
                WHERE interviewer_id = ? AND room_id IS NOT NULL
            ) OR a.room_id IS NULL)
            ORDER BY ts.start_time, a.created_at
        ''', (user_id, user_id,))
    else:
        # 学生查看自己的报名
        cursor.execute('''
            SELECT a.*, i.title as interview_title, ts.start_time, ts.end_time,
                   r.name as room_name
            FROM applications a
            JOIN interviews i ON a.interview_id = i.id
            JOIN time_slots ts ON a.time_slot_id = ts.id
            LEFT JOIN rooms r ON a.room_id = r.id
            WHERE a.student_id = ?
            ORDER BY a.created_at DESC
        ''', (user_id,))

    applications = cursor.fetchall()
    conn.close()

    result = []
    for app in applications:
        item = dict(app)
        result.append(item)

    return jsonify(result)


@app.route('/api/applications', methods=['POST'])
@login_required
@role_required('student')
def create_application():
    """提交报名"""
    data = request.get_json()
    interview_id = data.get('interview_id')
    time_slot_id = data.get('time_slot_id')
    first_position = data.get('first_position', '').strip()
    second_position = data.get('second_position', '').strip()
    phone = data.get('phone', '').strip()
    accept_adjust = 1 if data.get('accept_adjust') else 0

    # 验证
    if not interview_id or not time_slot_id or not first_position:
        return jsonify({'success': False, 'message': '请填写完整信息'})

    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查是否已报名（同一学生只能报名一个场次）
    cursor.execute(
        "SELECT * FROM applications WHERE student_id = ? AND status = 'pending'",
        (user_id,)
    )
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '您已报名其他面试场次，每人只能报名一个场次'})

    # 检查时间段是否已满
    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE time_slot_id = ? AND status = 'pending'",
        (time_slot_id,)
    )
    applied_count = cursor.fetchone()[0]

    cursor.execute("SELECT max_count FROM time_slots WHERE id = ?", (time_slot_id,))
    slot = cursor.fetchone()
    if not slot:
        conn.close()
        return jsonify({'success': False, 'message': '时间段不存在'})

    if applied_count >= slot['max_count']:
        conn.close()
        return jsonify({'success': False, 'message': '该时间段已满，请选择其他时间段'})

    # 创建报名
    cursor.execute('''
        INSERT INTO applications (student_id, interview_id, time_slot_id, first_position,
                                 second_position, phone, accept_adjust)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, interview_id, time_slot_id, first_position, second_position, phone, accept_adjust))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '报名成功！'})


@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
@login_required
@role_required('student')
def cancel_application(app_id):
    """取消报名"""
    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    # 验证是否是本人
    cursor.execute("SELECT * FROM applications WHERE id = ? AND student_id = ?", (app_id, user_id))
    app = cursor.fetchone()
    if not app:
        conn.close()
        return jsonify({'success': False, 'message': '报名记录不存在'})

    # 检查状态
    if app['status'] == 'cancelled':
        conn.close()
        return jsonify({'success': False, 'message': '该报名已取消'})

    # 取消报名
    cursor.execute("UPDATE applications SET status = 'cancelled' WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '取消报名成功'})


# ============================================================
# API：面试结果
# ============================================================

@app.route('/api/applications/<int:app_id>/result', methods=['GET'])
@login_required
def get_interview_result(app_id):
    """获取面试结果"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ir.*, u.name as interviewer_name
        FROM interview_results ir
        JOIN users u ON ir.interviewer_id = u.id
        WHERE ir.application_id = ?
    ''', (app_id,))
    results = cursor.fetchall()
    conn.close()

    return jsonify([dict(r) for r in results])


@app.route('/api/applications/<int:app_id>/result', methods=['POST'])
@login_required
@role_required('interviewer')
def create_interview_result(app_id):
    """录入面试结果"""
    data = request.get_json()
    attendance = data.get('attendance')
    result = data.get('result')
    comment = data.get('comment', '').strip()

    if not attendance or not result:
        return jsonify({'success': False, 'message': '请填写到面状态和面试结果'})

    user_id = session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查是否有权限（是否是负责该场次的面试官）
    cursor.execute('''
        SELECT * FROM applications WHERE id = ?
    ''', (app_id,))
    app = cursor.fetchone()
    if not app:
        conn.close()
        return jsonify({'success': False, 'message': '报名记录不存在'})

    cursor.execute('''
        SELECT * FROM interview_assignments
        WHERE interview_id = ? AND interviewer_id = ?
    ''', (app['interview_id'], user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '您没有权限评分此面试者'})

    # 插入或更新面试结果
    cursor.execute('''
        INSERT INTO interview_results (application_id, interviewer_id, attendance, result, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', (app_id, user_id, attendance, result, comment))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '评分成功'})


# ============================================================
# API：面试官相关
# ============================================================

@app.route('/api/interviewers', methods=['GET'])
@login_required
@role_required('admin')
def get_interviewers():
    """获取所有面试官"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name FROM users WHERE role = 'interviewer'")
    interviewers = cursor.fetchall()
    conn.close()
    return jsonify([dict(i) for i in interviewers])


@app.route('/api/interviewers', methods=['POST'])
@login_required
@role_required('admin')
def create_interviewer():
    """创建面试官账号"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()

    if not username or not password or not name:
        return jsonify({'success': False, 'message': '请填写完整信息'})

    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查用户名是否存在
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '用户名已存在'})

    cursor.execute(
        "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
        (username, password, name, 'interviewer')
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '面试官账号创建成功'})


# ============================================================
# API：用户管理（管理员）
# ============================================================

@app.route('/api/users', methods=['GET'])
@login_required
@role_required('admin')
def get_all_users():
    """获取所有用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])


@app.route('/api/users', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    """创建用户（管理员）"""
    data = request.get_json()
    role = data.get('role')
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    name = data.get('name', '').strip()

    if not role or not username or not password or not name:
        return jsonify({'success': False, 'message': '请填写完整信息'})

    if role not in ['admin', 'interviewer', 'student']:
        return jsonify({'success': False, 'message': '角色无效'})

    # 学生需要验证学号格式
    if role == 'student' and not username.isdigit():
        return jsonify({'success': False, 'message': '学号必须是纯数字'})

    conn = get_db_connection()
    cursor = conn.cursor()

    # 检查用户名是否存在
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '用户名/学号已存在'})

    cursor.execute(
        "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
        (username, password, name, role)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '用户创建成功'})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    """删除用户"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取要删除的用户
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': '用户不存在'})

    # 检查是否最后一个管理员
    if user['role'] == 'admin':
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        if admin_count <= 1:
            conn.close()
            return jsonify({'success': False, 'message': '不能删除最后一个管理员'})

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ============================================================
# API：数据统计
# ============================================================

@app.route('/api/stats', methods=['GET'])
@login_required
@role_required('admin')
def get_stats():
    """获取统计数据（管理员用）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 面试场次数量
    cursor.execute("SELECT COUNT(*) FROM interviews")
    interview_count = cursor.fetchone()[0]

    # 报名总人数
    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending'")
    application_count = cursor.fetchone()[0]

    # 已面试人数
    cursor.execute('''
        SELECT COUNT(DISTINCT application_id) FROM interview_results WHERE result IS NOT NULL
    ''')
    interviewed_count = cursor.fetchone()[0]

    # 各场次报名统计
    cursor.execute('''
        SELECT i.title,
               COUNT(a.id) as applied_count,
               (SELECT COUNT(*) FROM interview_results ir
                JOIN applications a2 ON ir.application_id = a2.id
                WHERE a2.interview_id = i.id AND ir.result = 'pass') as pass_count
        FROM interviews i
        LEFT JOIN applications a ON i.id = a.interview_id AND a.status = 'pending'
        GROUP BY i.id
    ''')
    interview_stats = cursor.fetchall()

    conn.close()

    return jsonify({
        'interview_count': interview_count,
        'application_count': application_count,
        'interviewed_count': interviewed_count,
        'interview_stats': [dict(s) for s in interview_stats]
    })


# ============================================================
# API：数据导出
# ============================================================

@app.route('/api/export')
@login_required
@role_required('admin')
def export_data():
    """导出面试数据为Excel（CSV格式）"""
    import csv
    import io

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            u.name as 学生姓名,
            u.username as 学号,
            a.phone as 联系电话,
            i.title as 面试场次,
            ts.start_time as 开始时间,
            ts.end_time as 结束时间,
            a.first_position as 第一志愿,
            a.second_position as 第二志愿,
            CASE a.accept_adjust WHEN 1 THEN '是' ELSE '否' END as 是否接受调剂,
            a.status as 报名状态,
            ir.attendance as 到场状态,
            ir.result as 面试结果,
            ir.comment as 面试评语,
            ir.created_at as 评分时间
        FROM applications a
        JOIN users u ON a.student_id = u.id
        JOIN interviews i ON a.interview_id = i.id
        JOIN time_slots ts ON a.time_slot_id = ts.id
        LEFT JOIN interview_results ir ON a.id = ir.application_id
        ORDER BY i.title, ts.start_time
    ''')

    rows = cursor.fetchall()
    conn.close()

    # 生成CSV
    output = io.StringIO()
    if rows:
        # 写入表头
        output.write(','.join(rows[0].keys()) + '\n')
        # 写入数据
        for row in rows:
            values = [str(v) if v is not None else '' for v in row.values()]
            # 处理包含逗号的值
            values = [v.replace(',', '，') for v in values]
            output.write(','.join(values) + '\n')

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='面试数据导出.csv'
    )


# ============================================================
# 路由：面试官页面
# ============================================================

@app.route('/interviewer')
@login_required
@role_required('interviewer')
def interviewer_dashboard():
    """面试官仪表盘"""
    return render_template('interviewer/dashboard.html')


# ============================================================
# 路由：面试者页面
# ============================================================

@app.route('/student')
@login_required
@role_required('student')
def student_dashboard():
    """面试者仪表盘"""
    return render_template('student/dashboard.html')


# ============================================================
# 调试接口：检查用户账号
# ============================================================

@app.route('/api/debug/users')
def debug_users():
    """调试用：查看所有用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])


# ============================================================
# 主程序入口
# ============================================================

if __name__ == '__main__':
    # 初始化数据库
    init_db()
    print("=" * 50)
    print("博物社面试管理系统已启动！")
    print("访问地址：http://127.0.0.1:5000")
    print("=" * 50)
    print("测试账号：")
    print("  管理员：admin / admin123")
    print("  面试官：interviewer1 / inter123")
    print("  学生：2023001 / student123")
    print("=" * 50)

    # 启动Flask服务
    app.run(debug=True, host='0.0.0.0', port=5000)
