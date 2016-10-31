"""Simple caching utilities.
"""
from ..app import app
from redis import Redis

def get_redis_connection():
    host = app.config.get('REDIS_HOST')
    port = app.config.get('REDIS_PORT')
    if host and port:
        return Redis(host, port)

def get(key):
    """Gets the given key from cache.
    """
    redis = get_redis_connection()
    return redis and redis.get(key)

def set(key, value, expiry=None):
    """Sets the given key-value pair in the cache.

    Optionally expiry can be specified in seconds.
    """
    redis = get_redis_connection()
    return redis and redis.set(key, value, ex=expiry)
