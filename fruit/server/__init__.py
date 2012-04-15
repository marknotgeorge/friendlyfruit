import pymongo

from .. import config

_db = None

def db():
    global _db

    if _db is None:
        _db = pymongo.Connection(config.get("database", "host"), config.getint("database", "port"))
        for prefix in config.get("database", "prefix").split("."):
            _db = getattr(_db, prefix)

        _db.users.create_index("user_id", unique=True)

    return _db
