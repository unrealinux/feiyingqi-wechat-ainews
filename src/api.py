"""
REST API - RESTful API 接口

为外部系统提供 API 接口
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def require_auth(f):
    """API 认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from src.config_secure import get_api_config, load_env, get_env
        load_env()
        
        config = get_api_config()
        
        if config.get("enabled") and config.get("auth_token"):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            
            if token != config["auth_token"]:
                return jsonify({"error": "Unauthorized"}), 401
        
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    """API 概览"""
    return jsonify({
        "name": "AI News Publisher API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/api/health", "method": "GET", "description": "健康检查"},
            {"path": "/api/run", "method": "POST", "description": "触发运行"},
            {"path": "/api/articles", "method": "GET", "description": "获取文章列表"},
            {"path": "/api/articles/<id>", "method": "GET", "description": "获取文章详情"},
            {"path": "/api/stats", "method": "GET", "description": "获取统计信息"},
            {"path": "/api/config/status", "method": "GET", "description": "配置状态"},
        ]
    })


@app.route("/api/health")
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/run", methods=["POST"])
@require_auth
def trigger_run():
    """触发运行"""
    from src.scheduler import run_once
    from src.monitoring import send_run_notification
    import time
    
    start_time = time.time()
    
    try:
        success = run_once()
        elapsed = time.time() - start_time
        
        if success:
            send_run_notification("success", {
                "news_count": 0,
                "word_count": 0,
                "channels": "file,wechat",
                "elapsed": elapsed
            })
        
        return jsonify({
            "success": success,
            "elapsed_seconds": elapsed,
            "message": "Run completed" if success else "Run failed"
        })
        
    except Exception as e:
        logger.error(f"Run API error: {e}")
        send_run_notification("error", {"error": str(e)})
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/articles")
@require_auth
def list_articles():
    """获取文章列表"""
    from src.database import get_db
    
    try:
        db = get_db()
        
        limit = request.args.get("limit", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        articles = db.get_articles(limit=limit, offset=offset)
        stats = db.get_stats()
        
        return jsonify({
            "articles": articles,
            "total": stats.get("total_articles", 0),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Articles API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/articles/<int:article_id>")
@require_auth
def get_article(article_id):
    """获取文章详情"""
    from src.database import get_db
    
    try:
        db = get_db()
        article = db.get_article(article_id)
        
        if not article:
            return jsonify({"error": "Article not found"}), 404
        
        news_items = db.get_news_items(article_id)
        
        return jsonify({
            "article": article,
            "news_items": news_items
        })
        
    except Exception as e:
        logger.error(f"Article API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
@require_auth
def get_stats():
    """获取统计信息"""
    from src.database import get_db
    
    try:
        db = get_db()
        stats = db.get_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/status")
@require_auth
def config_status():
    """配置状态"""
    from src.config_secure import (
        print_config_status, validate_config,
        get_wechat_config, get_openai_config, get_monitoring_config
    )
    from src.config_secure import load_env
    load_env()
    
    validation = validate_config()
    
    return jsonify({
        "valid": validation["valid"],
        "issues": validation["issues"],
        "wechat_configured": bool(get_wechat_config().get("app_id")),
        "openai_configured": bool(get_openai_config().get("api_key")),
        "monitoring_enabled": get_monitoring_config().get("enabled")
    })


@app.route("/api/search")
@require_auth
def search_articles():
    """搜索文章"""
    from src.database import get_db
    
    try:
        keyword = request.args.get("q", "")
        
        if not keyword:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        db = get_db()
        results = db.search_articles(keyword)
        
        return jsonify({
            "query": keyword,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({"error": str(e)}), 500


def start_api_server(port: int = None):
    """启动 API 服务器"""
    from src.config_secure import get_api_config, load_env
    load_env()
    
    config = get_api_config()
    port = port or config.get("port", 5001)
    
    cors_origins = config.get("cors_origins", ["*"])
    CORS(app, origins=cors_origins)
    
    logger.info(f"Starting API server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    start_api_server()
