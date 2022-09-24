import os
import asyncio
import ydb


driver = ydb.Driver(endpoint=os.getenv('YDB_ENDPOINT'), database=os.getenv('YDB_DATABASE'))
session_pool = ydb.SessionPool(driver)


async def execute_query(pool, query, param=None):
    # checkout a session to execute query.
    with pool.async_checkout() as session_holder:
        try:
            # wait for the session checkout to complete.
            session = await asyncio.wait_for(
                asyncio.wrap_future(session_holder), timeout=5
            )
        except asyncio.TimeoutError:
            raise ydb.SessionPoolEmpty('SessionPoolEmpty')

        prepared_query = session.prepare(query)

        return await asyncio.wrap_future(
            session.transaction().async_execute(
                query=prepared_query,
                parameters=param,
                commit_tx=True,
                settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2),
            )
        )


update_query = '''DECLARE $user_id AS Uint64;
DECLARE $value AS Utf8?;
UPDATE `db-for-bot` SET {} = $value WHERE user_id = $user_id;'''

get_query = '''DECLARE $user_id AS Uint64;
SELECT {} FROM `db-for-bot` WHERE user_id = $user_id;'''


async def check_user(user_id):
    query = 'DECLARE $user_id AS Uint64;\nSELECT user_id FROM `db-for-bot` WHERE user_id = $user_id;'
    param = {'$user_id': user_id}
    result = await ydb.aio.retry_operation(execute_query, None, session_pool, query, param)
    return bool(result[0].rows)


async def add_user(user_id):
    query = 'DECLARE $user_id AS Uint64;\nINSERT INTO `db-for-bot` (user_id) VALUES ($user_id);'
    param = {'$user_id': user_id}
    await ydb.aio.retry_operation(execute_query, None, session_pool, query, param)


async def update_data(user_id, data, value):
    query = update_query.format(data)
    param = {
        '$user_id': user_id,
        '$value': value
    }
    await ydb.aio.retry_operation(execute_query, None, session_pool, query, param)


async def get_data(user_id, *data_list):
    query = get_query.format(', '.join(data_list))
    param = {'$user_id': user_id}
    results = await ydb.aio.retry_operation(execute_query, None, session_pool, query, param)
    return list(results[0].rows[0].values())
