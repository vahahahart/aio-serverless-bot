import os

from database.ydb_driver import YDBDriver


if os.getenv('START') == 'LOCAL':
    from database.SQLite_db import BotDB
    main_driver = BotDB('database/bot.db')
else:
    main_driver = YDBDriver(endpoint=os.getenv('YDB_ENDPOINT'), database=os.getenv('YDB_DATABASE'))
