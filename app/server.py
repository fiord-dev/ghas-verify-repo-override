"""CodeQL (Code Scanning) に検出させるための、意図的に脆弱なサンプルアプリ。

検証専用。実行・デプロイしないこと。
"""
import os
import sqlite3
import subprocess

import yaml
from flask import Flask, request

app = Flask(__name__)


@app.route("/user")
def get_user():
    # SQL injection (py/sql-injection)
    name = request.args.get("name", "")
    conn = sqlite3.connect("app.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name = '" + name + "'")
    return str(cur.fetchall())


@app.route("/ping")
def ping():
    # Command injection (py/command-line-injection)
    host = request.args.get("host", "127.0.0.1")
    return subprocess.check_output("ping -c 1 " + host, shell=True)


@app.route("/file")
def read_file():
    # Path traversal (py/path-injection)
    path = request.args.get("path", "README.md")
    with open(os.path.join("/srv/data", path)) as f:
        return f.read()


@app.route("/config", methods=["POST"])
def load_config():
    # Unsafe deserialization (py/unsafe-deserialization)
    return str(yaml.load(request.data, Loader=yaml.Loader))


@app.route("/hello")
def hello():
    # Reflected XSS (py/reflective-xss)
    return "<h1>Hello " + request.args.get("name", "") + "</h1>"


if __name__ == "__main__":
    # Flask debug mode (py/flask-debug)
    app.run(debug=True)
