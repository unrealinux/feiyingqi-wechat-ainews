"""
Enhanced Web Dashboard - 增强版管理界面

包含图表统计、更好的 UI 设计
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, send_file, jsonify, request, redirect, url_for

from src.config import load_config
from src.scheduler import run_once
from src.fetcher import fetch_news, get_mock_news
from src.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Publisher - 管理后台</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        
        .header { background: rgba(255,255,255,0.95); padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 20px rgba(0,0,0,0.1); }
        .header h1 { font-size: 24px; color: #333; }
        .header .nav { display: flex; gap: 20px; }
        .header .nav a { color: #667eea; text-decoration: none; font-weight: 500; }
        .header .nav a:hover { color: #764ba2; }
        
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card .icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 15px; }
        .stat-card .number { font-size: 36px; font-weight: bold; color: #333; }
        .stat-card .label { color: #666; font-size: 14px; margin-top: 5px; }
        
        .chart-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px; }
        .chart-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .chart-card h3 { font-size: 16px; color: #333; margin-bottom: 20px; }
        
        .action-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .action-card h3 { font-size: 16px; color: #333; margin-bottom: 20px; }
        
        .btn { display: inline-block; padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; margin: 5px; text-decoration: none; transition: all 0.3s; }
        .btn:hover { background: #5a6fd6; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .btn-warning { background: #ffc107; color: #333; }
        .btn-warning:hover { background: #e0a800; }
        
        .table-card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .table-card h3 { font-size: 16px; color: #333; margin-bottom: 20px; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { color: #666; font-weight: 500; font-size: 14px; }
        td { color: #333; }
        tr:hover { background: #f8f9fa; }
        
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
        .status-published { background: #d4edda; color: #155724; }
        .status-draft { background: #fff3cd; color: #856404; }
        
        .log-output { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
        
        .loading { opacity: 0.5; pointer-events: none; }
        
        @media (max-width: 768px) {
            .chart-grid { grid-template-columns: 1fr; }
            .header { flex-direction: column; gap: 15px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI News Publisher</h1>
        <div class="nav">
            <a href="/">📊 Dashboard</a>
            <a href="/articles">📄 Articles</a>
            <a href="/api">🔌 API</a>
            <a href="/config">⚙️ Config</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon" style="background: #e8f5e9;">📄</div>
                <div class="number">{{ stats.total_articles }}</div>
                <div class="label">总文章数</div>
            </div>
            <div class="stat-card">
                <div class="icon" style="background: #e3f2fd;">📝</div>
                <div class="number">{{ stats.total_words // 1000 }}K</div>
                <div class="label">总字数</div>
            </div>
            <div class="stat-card">
                <div class="icon" style="background: #fff3e0;">✅</div>
                <div class="number">{{ stats.published_articles }}</div>
                <div class="label">已发布</div>
            </div>
            <div class="stat-card">
                <div class="icon" style="background: #fce4ec;">▶️</div>
                <div class="number">{{ stats.total_runs }}</div>
                <div class="label">运行次数</div>
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="chart-card">
                <h3>📈 文章发布趋势</h3>
                <canvas id="trendChart" height="100"></canvas>
            </div>
            <div class="chart-card">
                <h3>📊 数据分布</h3>
                <canvas id="pieChart"></canvas>
            </div>
        </div>
        
        <div class="action-card">
            <h3>⚡ 快速操作</h3>
            <button class="btn btn-success" onclick="runNow()">🚀 立即运行</button>
            <button class="btn" onclick="testMode()">🧪 测试模式</button>
            <button class="btn" onclick="refreshStats()">🔄 刷新统计</button>
            <button class="btn" onclick="showLogs()">📋 查看日志</button>
            <a href="/download/latest" class="btn">⬇️ 下载文章</a>
        </div>
        
        <div id="run-status" style="display: none;" class="action-card">
            <div id="status-text" style="padding: 10px;">运行中...</div>
        </div>
        
        <div class="table-card">
            <h3>📄 最近文章</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>标题</th>
                        <th>字数</th>
                        <th>状态</th>
                        <th>创建时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for article in articles %}
                    <tr>
                        <td>{{ article.id }}</td>
                        <td>{{ article.title[:30] }}...</td>
                        <td>{{ article.word_count }}</td>
                        <td><span class="status-badge {% if article.published %}status-published{% else %}status-draft{% endif %}">
                            {% if article.published %}已发布{% else %}草稿{% endif %}
                        </span></td>
                        <td>{{ article.created_at[:19] if article.created_at else '-' }}</td>
                        <td>
                            <a href="/api/articles/{{ article.id }}" class="btn" style="padding: 6px 12px; font-size: 12px;">查看</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const stats = {{ stats_json | safe }};
        
        // Trend Chart
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Articles',
                    data: [2, 3, 1, 4, 2, 3, 2],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102,126,234,0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
        
        // Pie Chart
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['已发布', '草稿'],
                datasets: [{
                    data: [{{ stats.published_articles }}, {{ stats.total_articles - stats.published_articles }}],
                    backgroundColor: ['#28a745', '#ffc107']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
        
        function runNow() {
            if (!confirm('确认运行？将获取新闻并生成文章')) return;
            
            const btn = event.target;
            btn.classList.add('loading');
            btn.textContent = '运行中...';
            
            fetch('/api/run', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    alert(data.success ? '✅ 运行成功！' : '❌ 运行失败：' + data.message);
                    location.reload();
                })
                .catch(err => {
                    alert('❌ 错误：' + err);
                    btn.classList.remove('loading');
                    btn.textContent = '🚀 立即运行';
                });
        }
        
        function testMode() {
            window.location.href = '/test';
        }
        
        function refreshStats() {
            location.reload();
        }
        
        function showLogs() {
            alert('日志功能开发中...');
        }
    </script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    """仪表盘主页"""
    db = get_db()
    stats = db.get_stats()
    articles = db.get_articles(limit=10)
    
    return render_template_string(DASHBOARD_HTML,
        stats=stats,
        articles=articles,
        stats_json=json.dumps(stats)
    )


@app.route("/test")
def test_page():
    """测试页面"""
    return """
    <h1>🧪 Test Mode</h1>
    <p>Running in test mode...</p>
    """


@app.route("/articles")
def articles_page():
    """文章列表页面"""
    db = get_db()
    articles = db.get_articles(limit=50)
    stats = db.get_stats()
    
    return render_template_string(DASHBOARD_HTML.replace('📈 文章发布趋势', '📄 所有文章'),
        stats=stats,
        articles=articles,
        stats_json=json.dumps(stats)
    )


@app.route("/config")
def config_page():
    """配置页面"""
    from src.config_secure import print_config_status, validate_config, load_env
    load_env()
    
    validation = validate_config()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Config - AI News Publisher</title></head>
    <body style="font-family: sans-serif; padding: 40px; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh;">
        <div style="background: white; border-radius: 16px; padding: 30px; max-width: 600px; margin: 0 auto;">
            <h1>⚙️ Configuration Status</h1>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 8px; overflow-x: auto;">
""" + json.dumps(validation, indent=2) + """
            </pre>
            <a href="/" style="display: inline-block; margin-top: 20px; color: #667eea;">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """
    return html


def start_dashboard(port=5000):
    """启动增强版 Dashboard"""
    logger.info(f"Starting Enhanced Dashboard at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    start_dashboard()
