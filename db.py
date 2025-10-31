import asyncio
import psycopg
import os
import psycopg_pool
import contextlib
#Local import
from config import DATABASE_URL

pool = None

async def init_db():
    global pool
    pool = psycopg_pool.AsyncConnectionPool(DATABASE_URL, min_size=1, max_size=16)

async def close_db():
    await pool.close()
@contextlib.asynccontextmanager
async def getDictCursor():
    """
    Async context manager that yields a cursor returning dict rows.
    """
    async with pool.connection() as aconn:
        async with aconn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            yield cur
