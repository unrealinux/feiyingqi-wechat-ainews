"""
Web Dashboard - AI News Publisher 管理界面

使用 Flask 提供简单的 Web 界面
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, send_file, jsonify, request

from src.config import load_config
from src.scheduler import run_once
from src.fetcher import fetch_news, get_mock_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# HTML 模板
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Publisher - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 36px; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        .actions { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }
        .btn { display: inline-block; padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; margin: 5px; text-decoration: none; }
        .btn:hover { background: #5a6fd6; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .articles { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }
        .article-item { padding: 15px; border-bottom: 1px solid #eee; }
        .article-item:last-child { border-bottom: none; }
        .article-title { font-size: 16px; font-weight: bold; color: #333; }
        .article-date { color: #999; font-size: 12px; margin-top: 5px; }
        .log-output { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 400px; overflow-y: auto; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI News Publisher</h1>
        <p>全网 AI 资讯聚合自动发布系统</p>
    </div>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ article_count }}</div>
                <div class="stat-label">已生成文章</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ news_sources }}</div>
                <div class="stat-label">新闻源数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ last_run }}</div>
                <div class="stat-label">最后运行</div>
            </div>
        </div>
        
        <div class="actions">
            <h2 style="margin-bottom: 15px;">⚡ 快速操作</h2>
            <button class="btn" onclick="runNow()">🚀 立即运行</button>
            <a href="/articles" class="btn btn-success">📄 查看文章</a>
            <a href="/download/latest" class="btn">⬇️ 下载最新</a>
            <button class="btn" onclick="loadLogs()">📋 查看日志</button>
        </div>
        
        <div id="run-status" style="display: none; background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <span id="status-text">运行中...</span>
        </div>
        
        <div id="log-container" style="display: none;">
            <h3 style="margin: 15px 0;">运行日志</h3>
            <div class="log-output" id="log-content"></div>
        </div>
        
        <div class="articles">
            <h2 style="margin-bottom: 15px;">📄 最近文章</h2>
            {% for article in articles %}
            <div class="article-item">
                <div class="article-title">{{ article.name }}</div>
                <div class="article-date">{{ article.date }} | {{ article.size }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        function runNow() {
            document.getElementById('run-status').style.display = 'block';
            fetch('/api/run', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status-text').textContent = '✅ 完成！' + (data.message || '');
                    setTimeout(() => { location.reload(); }, 2000);
                })
                .catch(err => {
                    document.getElementById('status-text').textContent = '❌ 失败：' + err;
                });
        }
        
        function loadLogs() {
            const container = document.getElementById('log-container');
            container.style.display = container.style.display === 'none' ? 'block' : 'none';
            if (container.style.display === 'block') {
                fetch('/api/logs').then(r => r.text()).then(logs => {
                    document.getElementById('log-content').textContent = logs || '暂无日志';
                });
            }
        }
    </script>
</body>
</html>
"""

OUTPUT_DIR = Path("output")
LOG_FILE = Path("ainews.log")


def get_article_files():
    """获取文章列表"""
    articles = []
    if OUTPUT_DIR.exists():
        files = sorted(OUTPUT_DIR.glob("article_*.md"), reverse=True)[:10]
        for f in files:
            stat = f.stat()
            articles.append({
                "name": f.name,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "size": f"{stat.st_size / 1024:.1f} KB"
            })
    return articles


@app.route("/")
def dashboard():
    """仪表盘"""
    articles = get_article_files()
    config = load_config()
    
    news_sources = len(config.get("news", {}).get("search_keywords", []))
    
    return render_template_string(DASHBOARD_HTML,
        article_count=len(articles),
        news_sources=news_sources,
        last_run=datetime.now().strftime("%H:%M"),
        articles=articles
    )


@app.route("/api/run", methods=["POST"])
def api_run():
    """运行一次"""
    try:
        result = run_once()
        return jsonify({"success": result, "message": "文章已生成" if result else "运行失败"})
    except Exception as e:
        logger.error(f"Run failed: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/logs")
def api_logs():
    """获取日志"""
    if LOG_FILE.exists():
        return LOG_FILE.read_text(encoding="utf-8")[-5000:]  # 最后 5000 字符
    return "暂无日志"


@app.route("/articles")
def articles():
    """文章列表"""
    files = get_article_files()
    return jsonify(files)


@app.route("/download/<path:filename>")
def download(filename):
    """下载文件"""
    filepath = OUTPUT_DIR / filename
    if filepath.exists():
        return send_file(filepath, as_attachment=True)
    return jsonify({"error": "File not found"}), 404


@app.route("/download/latest")
def download_latest():
    """下载最新文章"""
    files = sorted(OUTPUT_DIR.glob("article_*.md"), reverse=True)
    if files:
        return send_file(files[0], as_attachment=True)
    return jsonify({"error": "No articles found"}), 404


def start_dashboard(port=5000):
    """启动 Dashboard"""
    logger.info(f"Starting Dashboard at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    start_dashboard()
