from datetime import datetime, timedelta
import os
from statistics import mean

from flask import Flask, jsonify, request, send_file
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest, HTTPException


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
DATABASE_PATH = os.path.join(BASE_DIR, "memory_game.db")

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DATABASE_PATH.replace("\\", "/")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "please-change-this-secret-key-for-production"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
app.config["JSON_AS_ASCII"] = False
app.json.ensure_ascii = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)


@app.route("/", methods=["GET"])
def index():
    if not os.path.exists(INDEX_FILE):
        return error(
            "未找到 index.html，请确认 index.html 和 app.py 在同一个文件夹下。当前查找路径：" + INDEX_FILE,
            404,
        )

    return send_file(INDEX_FILE)


@app.route("/index.html", methods=["GET"])
def index_html():
    if not os.path.exists(INDEX_FILE):
        return error(
            "未找到 index.html，请确认 index.html 和 app.py 在同一个文件夹下。当前查找路径：" + INDEX_FILE,
            404,
        )

    return send_file(INDEX_FILE)


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return "", 204


def now():
    return datetime.now()


def format_time(value):
    if not value:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def success(message="success", data=None, code=200):
    return jsonify({
        "code": code,
        "message": message,
        "data": data,
    }), code


def error(message="error", code=400, data=None):
    return jsonify({
        "code": code,
        "message": message,
        "data": data,
    }), code


def get_json_body():
    data = request.get_json(silent=True)

    if data is None:
        raise ValueError("JSON 参数格式错误")

    if not isinstance(data, dict):
        raise ValueError("JSON 参数必须是对象")

    return data


def require_fields(data, fields):
    missing = [
        field
        for field in fields
        if field not in data or data[field] in (None, "")
    ]

    if missing:
        return error("必填字段缺失: " + ", ".join(missing), 422)

    return None


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    create_time = db.Column(db.DateTime, default=now)


class GameRecord(db.Model):
    __tablename__ = "game_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.String(64), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    number_text = db.Column(db.String(20), nullable=False)
    correct_answer = db.Column(db.String(20), nullable=False)
    user_answer = db.Column(db.String(20), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    answer_time = db.Column(db.Float, nullable=False)
    create_time = db.Column(db.DateTime, default=now)


class GameProgress(db.Model):
    __tablename__ = "game_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    current_level = db.Column(db.Integer, default=1)
    max_level = db.Column(db.Integer, default=1)
    total_count = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    update_time = db.Column(db.DateTime, default=now, onupdate=now)


class GameReport(db.Model):
    __tablename__ = "game_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    session_id = db.Column(db.String(64), nullable=False)
    total_count = db.Column(db.Integer, nullable=False)
    correct_count = db.Column(db.Integer, nullable=False)
    wrong_count = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    max_level = db.Column(db.Integer, nullable=False)
    avg_time = db.Column(db.Float, nullable=False)
    create_time = db.Column(db.DateTime, default=now)


def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
    }


def progress_to_dict(progress):
    return {
        "currentLevel": progress.current_level,
        "maxLevel": progress.max_level,
        "totalCount": progress.total_count,
        "correctCount": progress.correct_count,
        "lastUpdateTime": format_time(progress.update_time),
    }


def record_to_dict(record):
    return {
        "id": record.id,
        "sessionId": record.session_id,
        "level": record.level,
        "numberText": record.number_text,
        "correctAnswer": record.correct_answer,
        "userAnswer": record.user_answer,
        "isCorrect": record.is_correct,
        "answerTime": record.answer_time,
        "createTime": format_time(record.create_time),
    }


def report_to_dict(report):
    return {
        "id": report.id,
        "sessionId": report.session_id,
        "totalCount": report.total_count,
        "correctCount": report.correct_count,
        "wrongCount": report.wrong_count,
        "accuracy": report.accuracy,
        "maxLevel": report.max_level,
        "avgTime": report.avg_time,
        "createTime": format_time(report.create_time),
    }


def current_user_id():
    return int(get_jwt_identity())


def get_or_create_progress(user_id):
    progress = GameProgress.query.filter_by(user_id=user_id).first()

    if progress is None:
        progress = GameProgress(user_id=user_id)
        db.session.add(progress)
        db.session.commit()

    return progress


@app.route("/api/users", methods=["POST"])
def register():
    try:
        data = get_json_body()
    except ValueError as exc:
        return error(str(exc), 400)

    missing_response = require_fields(data, ["username", "password"])
    if missing_response:
        return missing_response

    username = str(data["username"]).strip()
    password = str(data["password"])

    if not username or not password:
        return error("用户名和密码不能为空", 422)

    if User.query.filter_by(username=username).first():
        return error("用户名已存在", 409)

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password=hashed_password)

    db.session.add(user)
    db.session.commit()

    return success("创建成功", {"user": user_to_dict(user)}, 201)


@app.route("/api/auth/login", methods=["POST"])
def login():
    try:
        data = get_json_body()
    except ValueError as exc:
        return error(str(exc), 400)

    missing_response = require_fields(data, ["username", "password"])
    if missing_response:
        return missing_response

    username = str(data["username"]).strip()
    password = str(data["password"])

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return error("账号或密码错误", 401)

    token = create_access_token(identity=str(user.id))

    return success(data={
        "token": token,
        "user": user_to_dict(user),
    })


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(current_user_id())

    if not user:
        return error("用户不存在", 401)

    return success(data=user_to_dict(user))


@app.route("/api/game/progress", methods=["GET"])
@jwt_required()
def get_progress():
    progress = get_or_create_progress(current_user_id())
    return success(data=progress_to_dict(progress))


@app.route("/api/game/progress", methods=["PUT"])
@jwt_required()
def update_progress():
    try:
        data = get_json_body()
    except ValueError as exc:
        return error(str(exc), 400)

    fields = ["currentLevel", "maxLevel", "totalCount", "correctCount"]
    missing_response = require_fields(data, fields)
    if missing_response:
        return missing_response

    try:
        current_level = int(data["currentLevel"])
        max_level = int(data["maxLevel"])
        total_count = int(data["totalCount"])
        correct_count = int(data["correctCount"])
    except (TypeError, ValueError):
        return error("进度参数必须是数字", 400)

    if min(current_level, max_level, total_count, correct_count) < 0:
        return error("进度参数不能小于 0", 400)

    progress = get_or_create_progress(current_user_id())
    progress.current_level = max(1, current_level)
    progress.max_level = max(1, max_level)
    progress.total_count = total_count
    progress.correct_count = correct_count
    progress.update_time = now()

    db.session.commit()

    return success(data=progress_to_dict(progress))


@app.route("/api/game/records", methods=["POST"])
@jwt_required()
def create_record():
    try:
        data = get_json_body()
    except ValueError as exc:
        return error(str(exc), 400)

    fields = [
        "sessionId",
        "level",
        "numberText",
        "correctAnswer",
        "userAnswer",
        "isCorrect",
        "answerTime",
    ]

    missing_response = require_fields(data, fields)
    if missing_response:
        return missing_response

    try:
        level = int(data["level"])
        answer_time = float(data["answerTime"])
    except (TypeError, ValueError):
        return error("level 和 answerTime 必须是数字", 400)

    if not isinstance(data["isCorrect"], bool):
        return error("isCorrect 必须是布尔值", 400)

    if level < 1 or answer_time < 0:
        return error("level 必须大于 0，answerTime 不能小于 0", 400)

    record = GameRecord(
        user_id=current_user_id(),
        session_id=str(data["sessionId"]),
        level=level,
        number_text=str(data["numberText"]),
        correct_answer=str(data["correctAnswer"]),
        user_answer=str(data["userAnswer"]),
        is_correct=data["isCorrect"],
        answer_time=answer_time,
    )

    db.session.add(record)
    db.session.commit()

    return success("创建成功", record_to_dict(record), 201)


@app.route("/api/game/records", methods=["GET"])
@jwt_required()
def list_records():
    query = GameRecord.query.filter_by(user_id=current_user_id())

    session_id = request.args.get("sessionId")
    if session_id:
        query = query.filter_by(session_id=session_id)

    records = query.order_by(
        GameRecord.create_time.asc(),
        GameRecord.id.asc()
    ).all()

    return success(data=[record_to_dict(record) for record in records])


@app.route("/api/game/reports", methods=["POST"])
@jwt_required()
def create_report():
    try:
        data = get_json_body()
    except ValueError as exc:
        return error(str(exc), 400)

    missing_response = require_fields(data, ["sessionId"])
    if missing_response:
        return missing_response

    user_id = current_user_id()
    session_id = str(data["sessionId"])

    records = (
        GameRecord.query
        .filter_by(user_id=user_id, session_id=session_id)
        .order_by(GameRecord.create_time.asc(), GameRecord.id.asc())
        .all()
    )

    if not records:
        return error("该 sessionId 没有作答记录，无法生成报告", 400)

    total_count = len(records)
    correct_count = sum(1 for record in records if record.is_correct)
    wrong_count = total_count - correct_count
    accuracy = round(correct_count / total_count * 100, 2) if total_count else 0
    max_level = max(record.level for record in records if record.is_correct) if correct_count else 0
    avg_time = round(mean(record.answer_time for record in records), 2)

    report = GameReport(
        user_id=user_id,
        session_id=session_id,
        total_count=total_count,
        correct_count=correct_count,
        wrong_count=wrong_count,
        accuracy=accuracy,
        max_level=max_level,
        avg_time=avg_time,
    )

    db.session.add(report)
    db.session.commit()

    return success("创建成功", report_to_dict(report), 201)


@app.route("/api/game/reports/latest", methods=["GET"])
@jwt_required()
def latest_report():
    report = (
        GameReport.query
        .filter_by(user_id=current_user_id())
        .order_by(GameReport.create_time.desc(), GameReport.id.desc())
        .first()
    )

    return success(data=report_to_dict(report) if report else None)


@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return error("JWT 无效: " + reason, 401)


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return error("JWT 已过期，请重新登录", 401)


@jwt.unauthorized_loader
def missing_token_callback(reason):
    return error("未携带 Token，请先登录", 401)


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return error("JWT 已失效，请重新登录", 401)


@app.errorhandler(BadRequest)
def handle_bad_request(exc):
    return error("JSON 参数格式错误", 400)


@app.errorhandler(404)
def handle_404(exc):
    return error("页面或接口不存在", 404)


@app.errorhandler(500)
def handle_500(exc):
    db.session.rollback()
    return error("服务器错误", 500)


@app.errorhandler(Exception)
def handle_exception(exc):
    if isinstance(exc, HTTPException):
        return error(exc.description, exc.code)

    db.session.rollback()
    return error("服务器错误", 500)


with app.app_context():
    db.create_all()


print("当前运行的是新版 app.py")
print("当前项目目录：", BASE_DIR)
print("首页文件路径：", INDEX_FILE)
print("index.html 是否存在：", os.path.exists(INDEX_FILE))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)