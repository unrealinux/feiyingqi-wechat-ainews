"""
Enhanced Database Module - 增强版SQLite数据库
添加索引、连接池、异步支持
"""
import os
import json
import sqlite3
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from queue import Queue
import logging

from src.logger import get_logger


logger = get_logger(__name__)


DB_FILE = Path("cache/ainews.db")


class ConnectionPool:
    """数据库连接池"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._created = 0
        
        # 预创建连接
        for _ in range(pool_size):
            self._pool.put(self._create_connection())
            self._created += 1
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建新连接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        conn.row_factory = sqlite3.Row
        # 启用WAL模式提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """获取连接"""
        try:
            return self._pool.get_nowait()
        except:
            with self._lock:
                if self._created < self.pool_size * 2:
                    self._created += 1
                    return self._create_connection()
            return self._pool.get(timeout=30)
    
    def return_connection(self, conn: sqlite3.Connection):
        """归还连接"""
        try:
            self._pool.put_nowait(conn)
        except:
            conn.close()
    
    def close_all(self):
        """关闭所有连接"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except:
                pass


@dataclass
class Article:
    """文章数据模型"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    summary: str = ""
    source: str = ""
    word_count: int = 0
    read_time: int = 0
    created_at: Optional[datetime] = None
    published: bool = False
    publish_channel: str = ""
    views: int = 0
    likes: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "source": self.source,
            "word_count": self.word_count,
            "read_time": self.read_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published": self.published,
            "publish_channel": self.publish_channel,
            "views": self.views,
            "likes": self.likes,
            "metadata": self.metadata,
        }


class EnhancedDatabase:
    """增强版数据库管理器"""
    
    def __init__(self, db_path: str = None, use_pool: bool = True):
        self.db_path = str(db_path or DB_FILE)
        self._pool = None
        
        if use_pool:
            self._pool = ConnectionPool(self.db_path)
        
        # 确保目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接"""
        if self._pool:
            conn = self._pool.get_connection()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                self._pool.return_connection(conn)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
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
        """初始化数据库表和索引"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # 文章表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    source TEXT,
                    word_count INTEGER DEFAULT 0,
                    read_time INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published INTEGER DEFAULT 0,
                    publish_channel TEXT,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            # 新闻项表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    title TEXT NOT NULL,
                    url TEXT,
                    source TEXT,
                    description TEXT,
                    published_at TEXT,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id)
                )
            """)
            
            # 运行记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT,
                    news_count INTEGER DEFAULT 0,
                    article_id INTEGER,
                    duration_seconds REAL DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    articles_count INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    total_shares INTEGER DEFAULT 0,
                    UNIQUE(date)
                )
            """)
            
            # 创建索引 (优化查询性能)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_items_article ON news_items(article_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_items_fetched ON news_items(fetched_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_statistics_date ON statistics(date)")
            
            logger.info("Database initialized with indexes")
    
    # ==================== Article Operations ====================
    
    def save_article(self, article: Article) -> int:
        """保存文章"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articles (
                    title, content, summary, source, word_count, read_time,
                    published, publish_channel, views, likes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.title,
                article.content,
                article.summary,
                article.source,
                article.word_count,
                article.read_time,
                int(article.published),
                article.publish_channel,
                article.views,
                article.likes,
                json.dumps(article.metadata, ensure_ascii=False)
            ))
            return cursor.lastrowid
    
    def get_article(self, article_id: int) -> Optional[Article]:
        """获取文章"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_article(row)
            return None
    
    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """获取最新文章"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM articles ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [self._row_to_article(row) for row in cursor.fetchall()]
    
    def get_published_articles(self, limit: int = 10) -> List[Article]:
        """获取已发布文章"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM articles WHERE published = 1 ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [self._row_to_article(row) for row in cursor.fetchall()]
    
    def update_article_published(self, article_id: int, channel: str) -> bool:
        """更新文章发布状态"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE articles SET published = 1, publish_channel = ? WHERE id = ?",
                (channel, article_id)
            )
            return cursor.rowcount > 0
    
    def _row_to_article(self, row: sqlite3.Row) -> Article:
        """行数据转换为Article对象"""
        return Article(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            summary=row["summary"],
            source=row["source"],
            word_count=row["word_count"],
            read_time=row["read_time"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            published=bool(row["published"]),
            publish_channel=row["publish_channel"],
            views=row["views"],
            likes=row["likes"],
            metadata=json.loads(row["metadata"] or "{}")
        )
    
    # ==================== Statistics ====================
    
    def record_run(
        self, 
        status: str, 
        news_count: int = 0, 
        article_id: int = None,
        duration: float = 0,
        error: str = ""
    ):
        """记录运行"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO runs (status, news_count, article_id, duration_seconds, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (status, news_count, article_id, duration, error))
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取统计信息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # 总文章数
            cursor.execute("SELECT COUNT(*) as count FROM articles")
            total_articles = cursor.fetchone()["count"]
            
            # 已发布文章数
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE published = 1")
            published_articles = cursor.fetchone()["count"]
            
            # 总浏览量
            cursor.execute("SELECT SUM(views) as total FROM articles")
            total_views = cursor.fetchone()["total"] or 0
            
            # 近期运行统计
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM runs 
                WHERE created_at > datetime('now', '-{} days')
                GROUP BY status
            """.format(days), ())
            run_stats = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            # 今日文章
            cursor.execute("""
                SELECT * FROM articles 
                WHERE date(created_at) = date('now')
                ORDER BY created_at DESC
            """)
            today_articles = [self._row_to_article(row) for row in cursor.fetchall()]
            
            return {
                "total_articles": total_articles,
                "published_articles": published_articles,
                "total_views": total_views,
                "run_stats": run_stats,
                "today_articles": today_articles,
            }
    
    def cleanup_old_data(self, days: int = 90):
        """清理旧数据"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # 清理旧的未发布文章
            cursor.execute("""
                DELETE FROM articles 
                WHERE published = 0 
                AND created_at < datetime('now', '-{} days')
            """.format(days))
            
            # 清理旧的运行记录
            cursor.execute("""
                DELETE FROM runs 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            # 清理孤立新闻项
            cursor.execute("""
                DELETE FROM news_items 
                WHERE article_id IS NULL 
                AND fetched_at < datetime('now', '-{} days')
            """.format(days))
            
            logger.info(f"Cleaned up old data")
    
    def close(self):
        """关闭数据库连接"""
        if self._pool:
            self._pool.close_all()


# 全局数据库实例
_db_instance: Optional[EnhancedDatabase] = None
_db_lock = threading.Lock()


def get_database(db_path: str = None) -> EnhancedDatabase:
    """获取数据库实例(单例)"""
    global _db_instance
    
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = EnhancedDatabase(db_path)
    
    return _db_instance
