import json
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from handlers import commands, options, search


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

ycf_bot = Bot(token=os.environ['BOT_TOKEN'], parse_mode='HTML')

ycf_dp = Dispatcher()
ycf_dp.include_router(commands.router)
ycf_dp.include_router(options.router)
ycf_dp.include_router(search.router)


async def set_commands(bot: Bot):
    cmds = [
        BotCommand(command='/help', description='Отобразить выбранные параметры поиска и инструкции по командам'),
        BotCommand(command='/options', description='Параметры поиска'),
    ]
    await bot.set_my_commands(cmds)


async def process_event(event, bot: Bot, dp: Dispatcher):
    """
    Converting a Yandex.Cloud functions event to an update and
    handling tha update.
    """

    update = json.loads(event['body'])
    await dp.feed_raw_update(bot, update)


async def handler(event, context):
    """Yandex.Cloud functions handler."""

    if event['httpMethod'] == 'POST':

        await set_commands(ycf_bot)
        await process_event(event, ycf_bot, ycf_dp)

        return {'statusCode': 200, 'body': 'ok!'}
    return {'statusCode': 405}
