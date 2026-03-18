# 博物社面试管理系统 - 规格文档

## 一、项目概述
- **项目名称**：博物社面试管理系统
- **项目类型**：Web应用（前后端分离）
- **核心功能**：管理社团招新面试流程，包括场次配置、报名管理、面试评分、数据导出
- **目标用户**：社团管理员、面试官、面试学生

## 二、技术栈
- 后端：Python + Flask
- 数据库：SQLite
- 前端：原生HTML + CSS + JavaScript

## 三、角色与权限

### 1. 超级管理员（admin）
- 登录系统
- 增删改查面试场次
- 配置面试场次参数：
  - 面试标题
  - 面试日期+时间段（支持多个）
  - 可面试职位/部门
  - 每个时间段人数上限
  - 面试地点、备注
- 查看所有报名数据
- 查看面试官分配
- 查看面试结果
- 导出Excel数据
- 管理面试官账号

### 2. 面试官（interviewer）
- 登录系统
- 查看负责的面试场次、时间段
- 查看对应时间段报名的面试者列表（姓名、学号、志愿职位、是否接受调剂）
- 标记面试者「已到场/未到场」
- 录入面试结果（通过/未通过/待定）
- 添加面试评语

### 3. 面试者（student）
- 注册：姓名+学号（学号唯一）
- 登录：姓名+学号
- 查看可报名的面试场次
- 报名：选择时间段、选择志愿职位（支持排序）、填写联系电话、勾选是否接受调剂
- 校验：时间段满则提示无法报名
- 查看报名信息
- 取消报名（面试开始前）

## 四、数据库设计

### 表结构

#### users（用户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | TEXT | 用户名（学号或admin） |
| password | TEXT | 密码（明文存储，新手友好） |
| name | TEXT | 真实姓名 |
| role | TEXT | 角色：admin/interviewer/student |

#### interviews（面试场次表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | TEXT | 面试标题 |
| date | TEXT | 面试日期 |
| location | TEXT | 面试地点 |
| note | TEXT | 备注 |
| positions | TEXT | 可面试职位（JSON数组） |
| created_at | TEXT | 创建时间 |

#### time_slots（时间段表）
| 字段 | 类型 |说明 |
|------|------|------|
| id | INTEGER | 主键 |
| interview_id | INTEGER | 外键，关联interviews |
| start_time | TEXT | 开始时间 |
| end_time | TEXT | 结束时间 |
| max_count | INTEGER | 该时间段最大面试人数 |

#### interview_assignments（面试官分配表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| interview_id | INTEGER | 外键，关联interviews |
| interviewer_id | INTEGER | 外键，关联users |
| time_slot_id | INTEGER | 外键，关联time_slots |

#### applications（报名表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| student_id | INTEGER | 外键，关联users |
| interview_id | INTEGER | 外键，关联interviews |
| time_slot_id | INTEGER | 外键，关联time_slots |
| first_position | TEXT | 第一志愿 |
| second_position | TEXT | 第二志愿 |
| phone | TEXT | 联系电话 |
| accept_adjust | INTEGER | 是否接受调剂（0/1） |
| status | TEXT | 报名状态：pending/cancelled |
| created_at | TEXT | 报名时间 |

#### interview_results（面试结果表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| application_id | INTEGER | 外键，关联applications |
| interviewer_id | INTEGER | 外键，关联users |
| attendance | TEXT | 到场状态：present/absent |
| result | TEXT | 面试结果：pass/fail/pending |
| comment | TEXT | 面试评语 |
| created_at | TEXT | 评分时间 |

## 五、页面设计

### 1. 登录页（login.html）
- 用户名输入框
- 密码输入框
- 登录按钮
- 注册链接（面试者专用）

### 2. 注册页（register.html）
- 姓名输入框
- 学号输入框
- 密码输入框
- 确认密码输入框
- 注册按钮
- 返回登录链接

### 3. 管理员后台（admin/）
- 仪表盘：显示各场次报名统计
- 面试场次管理：增删改查
- 面试官管理：添加/移除面试官
- 数据导出：导出Excel
- 面试结果查看

### 4. 面试官页面（interviewer/）
- 我的面试场次列表
- 每个场次的时间段选择
- 面试者列表（可筛选时间段）
- 面试评分功能（模态框）

### 5. 面试者页面（student/）
- 可报名的面试场次列表
- 报名表单（选择时间段、志愿职位、联系电话、是否接受调剂）
- 我的报名信息
- 取消报名按钮

## 六、API接口设计

### 认证
- POST /api/login - 登录
- POST /api/register - 注册（学生）
- POST /api/logout - 登出

### 面试场次
- GET /api/interviews - 获取所有面试场次
- POST /api/interviews - 创建面试场次（管理员）
- PUT /api/interviews/<id> - 更新面试场次（管理员）
- DELETE /api/interviews/<id> - 删除面试场次（管理员）

### 时间段
- GET /api/interviews/<id>/time-slots - 获取场次的时间段
- POST /api/interviews/<id>/time-slots - 添加时间段（管理员）
- DELETE /api/time-slots/<id> - 删除时间段（管理员）

### 报名
- GET /api/applications - 获取报名列表
- POST /api/applications - 提交报名
- DELETE /api/applications/<id> - 取消报名

### 面试结果
- GET /api/applications/<id>/result - 获取面试结果
- POST /api/applications/<id>/result - 录入面试结果（面试官）
- GET /api/interviewer/applications - 面试官查看自己负责的报名

### 导出
- GET /api/export - 导出Excel（管理员）

## 七、约束规则

1. **同一面试者只能报名一个面试场次的一个时间段**
   - 报名时检查是否已有报名记录

2. **同一时间段报名人数不能超过上限**
   - 报名时检查已报名人数 < max_count

3. **面试官只能查看自己负责的面试数据**
   - 查询时过滤 interviewer_id

## 八、测试账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 超级管理员 |
| 面试官 | interviewer1 | inter123 | 面试官1 |
| 面试官 | interviewer2 | inter123 | 面试官2 |
| 学生 | 2023001 | student123 | 测试学生1 |
| 学生 | 2023002 | student123 | 测试学生2 |

## 九、部署方式

### 本地运行
```bash
pip install flask
python app.py
# 访问 http://127.0.0.1:5000
```

### VPS部署
- 使用Gunicorn + Nginx
- 详细说明见DEPLOY.md
