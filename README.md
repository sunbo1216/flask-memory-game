# Flask 阿尔茨海默记忆训练小游戏——我可以倒着记

## 一、项目简介

本项目是 25-26-2 学期《Web程序设计》期中考项目，主题为基于 Flask 的老人记忆康复训练小游戏——“我可以倒着记”。

项目采用前后端分离设计，后端基于 Flask 技术栈实现用户认证、数据持久化、游戏记录保存、训练报告生成等功能；前端使用原生 HTML、CSS、JavaScript 实现适老化交互页面、倒序记忆训练、暂停继续、本地离线缓存和训练报告展示。

游戏核心玩法是：系统展示一串数字，用户需要在数字消失后将数字倒着输入。例如系统显示 `358`，用户应输入 `853`。游戏通过逐步增加数字长度训练用户短时记忆能力。

---

## 二、项目功能

### 1. 用户功能

- 用户注册
- 用户登录
- JWT Token 身份认证
- 登录状态本地缓存
- 退出登录

### 2. 游戏功能

- 数字倒序记忆训练
- 连续闯关机制
- 难度逐级提升
- 暂停 / 继续游戏
- 中途退出自动生成报告
- 每次训练自动生成 `session_id`
- 每次作答记录完整保存

### 3. 数据同步功能

- 本地 `localStorage` 离线缓存
- 云端 SQLite 数据库存储
- 游戏进度本地与云端同步
- 答题记录本地与云端同步
- 训练报告本地与云端同步

### 4. 报告统计功能

- 总作答次数
- 正确次数
- 错误次数
- 答题准确率
- 最高通关关卡
- 平均作答用时
- 全部答题明细
- 简短训练建议

---

## 三、技术栈

### 后端技术

- Python
- Flask
- SQLite
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Bcrypt
- Flask-CORS

### 前端技术

- HTML
- CSS
- JavaScript
- Fetch API
- localStorage

---

## 四、项目结构

```text
test2-1/
├─ app.py                  # Flask 后端主程序
├─ index.html              # 前端单文件页面
├─ requirements.txt        # Python 依赖文件
├─ memory_game.db          # SQLite 数据库文件，运行后自动生成
├─ screenshots/            # 项目截图文件夹
│  ├─ 01_login_api.png
│  ├─ 02_save_record_api.png
│  ├─ 03_get_records_api.png
│  ├─ 04_update_progress_api.png
│  ├─ 05_game_start.png
│  ├─ 06_game_running_localstorage.png
│  └─ 07_game_report.png
└─ README.md               # 项目说明文件
