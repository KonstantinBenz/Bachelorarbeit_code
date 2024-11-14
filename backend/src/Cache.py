import sqlite3
import hashlib
from typing import Optional
from src.loggingConfig import logger

class Cache:
    def __init__(self, dbPath: str = 'cache.db') -> None:
        """
        Initialize the cache system with a SQLite database.

        :param dbPath: Path to the SQLite database file.
        """
        self.dbPath = dbPath
        self.createCacheTable()

    def createCacheTable(self) -> None:
        """
        Create the cache table if it doesn't exist already.
        """
        try:
            with sqlite3.connect(self.dbPath) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache (
                        query_hash TEXT PRIMARY KEY,
                        query TEXT,
                        response TEXT
                    )
                ''')
                conn.commit()
            logger.info("Cache table created or verified successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error creating cache table: {e}")

    def hashQuery(self, query: str) -> str:
        """
        Hash the query string using SHA-256.

        :param query: The query to hash.
        :return: A SHA-256 hash of the query.
        """
        return hashlib.sha256(query.encode()).hexdigest()

    def getCachedResponse(self, query: str) -> Optional[str]:
        """
        Retrieve a cached response based on the query.

        :param query: The query to retrieve the cached response for.
        :return: The cached response if found, None otherwise.
        """
        queryHash = self.hashQuery(query)
        try:
            with sqlite3.connect(self.dbPath) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT response FROM cache WHERE query_hash=?', (queryHash,))
                result = cursor.fetchone()
            if result:
                logger.info(f"Cache hit for query: {queryHash}")
                return result[0]
            else:
                logger.info(f"Cache miss for query: {queryHash}")
                return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching from cache: {e}")
            return None

    def cacheResponse(self, query: str, response: str) -> None:
        """
        Cache the response for a query.

        :param query: The query string.
        :param response: The response to cache.
        """
        queryHash = self.hashQuery(query)
        try:
            with sqlite3.connect(self.dbPath) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO cache (query_hash, query, response)
                    VALUES (?, ?, ?)
                ''', (queryHash, query, response))
                conn.commit()
            logger.info(f"Response cached for query: {queryHash}")
        except sqlite3.Error as e:
            logger.error(f"Error inserting into cache: {e}")
