import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from handlers import commands, options, search


def set_logging():
    """
    Set logging for Yandex.Cloud logging
    'WARN' level default
    """
    if os.getenv('START') == 'LOCAL':
        # local logging
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s]\t%(asctime)s\t%(name)s\t%(message)s'
        )
    else:
        logging_level = os.getenv('LOGGING_LEVEL')
        root_logger = logging.getLogger()
        root_logger.handlers[0].setFormatter(
            logging.Formatter('[%(levelname)s]\t%(name)s\t%(request_id)s\t%(message)s\n')
        )
        root_logger.setLevel(logging_level if logging_level else 'WARN')


async def set_commands(bot: Bot):
    cmds = [
        BotCommand(command='/help', description='Отобразить выбранные параметры поиска и инструкции по командам'),
        BotCommand(command='/options', description='Параметры поиска'),
        BotCommand(command='/last', description='Поиск по последнему маршруту'),
        BotCommand(command='/reverse_last', description='Поиск обратного маршрута')
    ]
    await bot.set_my_commands(cmds)


def bot_init():
    set_logging()

    bot = Bot(token=os.environ['BOT_TOKEN'], parse_mode='HTML')
    dp = Dispatcher()

    dp.include_router(commands.router)
    dp.include_router(options.router)
    dp.include_router(search.router)

    return bot, dp


main_bot, main_dp = bot_init()


async def process_event(event, bot: Bot, dp: Dispatcher):
    """
    Converting a Yandex.Cloud functions event to an update and
    handling the update.
    """

    update = json.loads(event['body'])
    await dp.feed_raw_update(bot, update)


async def handler(event, context):
    """Yandex.Cloud functions handler."""

    if event['httpMethod'] == 'POST':

        await set_commands(main_bot)
        await process_event(event, main_bot, main_dp)

        return {'statusCode': 200, 'body': 'ok!'}
    return {'statusCode': 405}


async def start():
    """Start long polling for tests"""
    await main_bot.delete_webhook(drop_pending_updates=True)
    await set_commands(main_bot)
    await main_dp.start_polling(main_bot)


if __name__ == '__main__':
    asyncio.run(start())
