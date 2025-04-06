import os
from flask import Flask, render_template, request, g
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)

# ================= 数据库配置 ================= #
def get_db():
    """获取PostgreSQL数据库连接"""
    if 'db' not in g:
        g.db = psycopg2.connect(os.environ['DATABASE_URL'])
    return g.db

# ================= 路由定义 ================= #
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        name = request.form['name']
        message = request.form['message']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with get_db().cursor() as cur:
            cur.execute(
                "INSERT INTO messages (name, message, timestamp) VALUES (%s, %s, %s)",
                (name, message, timestamp)
            )
            get_db().commit()
        
        return render_template('thankyou.html', name=name)
    except Exception as e:
        get_db().rollback()
        return f"提交失败: {str(e)}", 500

@app.route('/view')
def view():
    try:
        with get_db().cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT name, message, timestamp FROM messages ORDER BY timestamp DESC")
            messages = cur.fetchall()
        return render_template('view.html', messages=messages)
    except Exception as e:
        return f"查询失败: {str(e)}", 500

# ================= 数据库初始化 ================= #
def init_db():
    """首次部署时自动建表"""
    with get_db().cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT
            )
        ''')
        get_db().commit()

# ================= 生命周期管理 ================= #
@app.teardown_appcontext
def close_db(error):
    """自动关闭数据库连接"""
    if 'db' in g:
        g.db.close()

# ================= 启动逻辑 ================= #
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)