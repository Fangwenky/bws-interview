# 博物社面试管理系统 - 部署说明

## 一、系统要求

### 本地运行（Windows/Mac/Linux）
- Python 3.7+
- 无需额外安装数据库（SQLite）

### VPS部署
- Python 3.7+
- Nginx
- Gunicorn
- Linux服务器（推荐Ubuntu 20.04+）

---

## 二、本地运行方式

### 步骤1：安装Python依赖

```bash
# 进入项目目录
cd bws-interview

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 安装Flask
pip install flask
```

### 步骤2：启动系统

```bash
# 运行应用
python app.py
```

### 步骤3：访问系统

打开浏览器访问：`http://127.0.0.1:5000`

### 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 面试官 | interviewer1 | inter123 |
| 学生 | 2023001 | student123 |

---

## 三、VPS部署方式（Ubuntu）

### 步骤1：服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install -y python3 python3-pip python3-venv

# 安装Nginx
sudo apt install -y nginx
```

### 步骤2：上传代码

```bash
# 创建项目目录
sudo mkdir -p /var/www/bws-interview
cd /var/www/bws-interview

# 上传代码（通过FTP/SFTP/Git）
# 或直接复制代码文件
```

### 步骤3：创建虚拟环境并安装依赖

```bash
cd /var/www/bws-interview

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install flask gunicorn
```

### 步骤4：配置Gunicorn

创建启动脚本 `/var/www/bws-interview/start.sh`：

```bash
#!/bin/bash
cd /var/www/bws-interview
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 app:app --workers 2
```

添加执行权限：
```bash
chmod +x /var/www/bws-interview/start.sh
```

### 步骤5：配置Nginx

创建配置文件 `/etc/nginx/sites-available/bws-interview`：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态文件
    location /static/ {
        alias /var/www/bws-interview/static/;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/bws-interview /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

### 步骤6：配置Systemd服务（可选）

创建 `/etc/systemd/system/bws-interview.service`：

```ini
[Unit]
Description=BWS Interview System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/bws-interview
Environment="PATH=/var/www/bws-interview/venv/bin"
ExecStart=/var/www/bws-interview/venv/bin/gunicorn --bind 127.0.0.1:5000 app:app --workers 2

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start bws-interview
sudo systemctl enable bws-interview
```

### 步骤7：访问系统

打开浏览器访问：`http://your-server-ip`

---

## 四、功能说明

### 管理员功能
1. 登录后台（admin/admin123）
2. 创建面试场次（标题、日期、地点、职位）
3. 添加时间段（开始时间、结束时间、人数上限）
4. 分配面试官到场次
5. 查看所有报名和面试结果
6. 导出数据为Excel

### 面试官功能
1. 登录系统（interviewer1/inter123）
2. 查看分配的面试场次
3. 查看面试者列表
4. 标记到场状态
5. 录入面试结果（通过/未通过/待定）
6. 添加面试评语

### 学生功能
1. 注册账号（姓名+学号）
2. 登录系统
3. 查看可报名的场次
4. 选择时间段报名
5. 选择志愿职位
6. 查看/取消报名

---

## 五、常见问题

### 1. 数据库文件位置
数据库文件 `bws_interview.db` 会在首次运行时自动创建在项目目录下。

### 2. 如何重置数据
删除 `bws_interview.db` 文件，重新运行 `python app.py` 会重新初始化数据库和测试账号。

### 3. 端口被占用
如果5000端口被占用，可以修改 `app.py` 最后一行：
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # 改为其他端口
```

### 4. 如何备份数据
只需备份 `bws_interview.db` 文件即可。

### 5. 如何添加更多管理员
需要通过数据库直接插入管理员账号，或联系现有管理员添加。

---

## 六、目录结构

```
bws-interview/
├── app.py              # 主应用文件
├── bws_interview.db    # SQLite数据库（自动生成）
├── SPEC.md             # 规格文档
├── DEPLOY.md           # 部署说明
├── templates/          # HTML模板
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── interviews.html
│   │   ├── interviewers.html
│   │   └── results.html
│   ├── interviewer/
│   │   └── dashboard.html
│   └── student/
│       └── dashboard.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── common.js
```

---

## 七、技术支持

如有问题，请联系：
- 开发者：博物社技术组
- 邮箱：tech@bws.example.com
