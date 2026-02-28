"""
Database Module - SQLite 数据库支持

存储文章历史、统计数据、配置等
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = Path("cache/ainews.db")


class Database:
    """SQLite 数据库管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_FILE)
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    source TEXT,
                    word_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published INTEGER DEFAULT 0,
                    publish_channel TEXT,
                    metadata TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    title TEXT NOT NULL,
                    url TEXT,
                    source TEXT,
                    description TEXT,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT,
                    news_count INTEGER DEFAULT 0,
                    article_id INTEGER,
                    error_message TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    articles_count INTEGER DEFAULT 0,
                    words_count INTEGER DEFAULT 0,
                    views_count INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_created 
                ON articles(created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_started 
                ON runs(started_at DESC)
            """)
            
            logger.info("Database initialized")
    
    def save_article(self, title: str, content: str, 
                     source: str = "auto", 
                     published: int = 0,
                     publish_channel: str = None,
                     metadata: dict = None) -> int:
        """保存文章"""
        word_count = len(content) if content else 0
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articles (title, content, source, word_count, published, publish_channel, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, content, source, word_count, published, publish_channel, 
                  json.dumps(metadata) if metadata else None))
            
            return cursor.lastrowid
    
    def get_articles(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """获取文章列表"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, source, word_count, published, publish_channel, created_at
                FROM articles 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_article(self, article_id: int) -> Optional[Dict]:
        """获取单篇文章"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_publish_status(self, article_id: int, published: int = 1, 
                             channel: str = None):
        """更新发布状态"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articles 
                SET published = ?, publish_channel = ?
                WHERE id = ?
            """, (published, channel, article_id))
    
    def save_news_items(self, article_id: int, news_items: List):
        """保存新闻素材"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            for item in news_items:
                cursor.execute("""
                    INSERT INTO news_items (article_id, title, url, source, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (article_id, item.title, item.url, item.source, item.description))
    
    def get_news_items(self, article_id: int) -> List[Dict]:
        """获取文章关联的新闻素材"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM news_items WHERE article_id = ?
            """, (article_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def save_run(self, status: str, news_count: int = 0, 
                 article_id: int = None, error: str = None) -> int:
        """保存运行记录"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO runs (status, news_count, article_id, error_message, finished_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (status, news_count, article_id, error))
            return cursor.lastrowid
    
    def get_runs(self, limit: int = 10) -> List[Dict]:
        """获取运行记录"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM runs ORDER BY started_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM articles")
            total_articles = cursor.fetchone()["count"]
            
            cursor.execute("SELECT SUM(word_count) as total FROM articles")
            total_words = cursor.fetchone()["total"] or 0
            
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE published = 1")
            published_articles = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM runs WHERE status = 'success'")
            total_runs = cursor.fetchone()["count"]
            
            return {
                "total_articles": total_articles,
                "total_words": total_words,
                "avg_words": total_words // max(total_articles, 1),
                "published_articles": published_articles,
                "total_runs": total_runs,
            }
    
    def search_articles(self, keyword: str) -> List[Dict]:
        """搜索文章"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, source, created_at
                FROM articles 
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
                LIMIT 20
            """, (f"%{keyword}%", f"%{keyword}%"))
            return [dict(row) for row in cursor.fetchall()]


_db_instance = None


def get_db() -> Database:
    """获取数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def init_db():
    """初始化数据库"""
    get_db()


if __name__ == "__main__":
    db = Database()
    
    print("\n=== Database Test ===")
    
    article_id = db.save_article(
        title="Test Article",
        content="This is a test article content with some words.",
        source="test"
    )
    print(f"Saved article ID: {article_id}")
    
    articles = db.get_articles(limit=5)
    print(f"Total articles: {len(articles)}")
    
    stats = db.get_stats()
    print(f"Stats: {stats}")
    
    runs = db.get_runs(limit=5)
    print(f"Total runs: {len(runs)}")
