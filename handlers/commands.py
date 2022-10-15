from aiogram.dispatcher.router import Router
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from driver_init import main_driver as driver
from handlers.search import out_last
from handlers.options import kb_builder


router = Router()

start_msg = '''Чтобы выполнить поиск введите названия начальной, 
а затем конечной станции одним сообщением, разделяя названия запятой (,)
Также вы можете указать время и/или дату поиска написав их после конечной станции, время от даты разделяйте пробелом
Например: "Начальная, конечная, 17.20 22.09.22"\n'''


@router.message(commands='start')
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if not await driver.check_user(user_id):
        await driver.add_user(user_id)
        await driver.update_data(user_id, 'num', '3')
    await message.answer(start_msg)
    tz_builder = kb_builder('timezone')
    await message.answer(f'Укажите часовой пояс (UTC)', reply_markup=tz_builder.as_markup())


help_msg = '''Регион: <b>{}</b>
Транспорт: <b>{}</b>
Часовой пояс +{}'''


@router.message(commands='help')
async def cmd_help(message: Message):
    user_id = message.from_user.id
    data = await driver.get_data(user_id, 'region', 'transport_type', 'time_zone')
    await message.answer(start_msg + help_msg.format(*data))


option_dict = {
    'Регион': 'opt_r',
    'Тип транспорта': 'opt_tr',
    'Часовой пояс': 'opt_tz',
    'Отображаемое количество рейсов': 'opt_n',
    'Отмена': 'opt_out'
}


@router.message(commands='options')
async def cmd_option(message: Message):
    builder = InlineKeyboardBuilder()
    for option in option_dict:
        builder.add(
            InlineKeyboardButton(
                text=option,
                callback_data=option_dict[option]
            )
        )
    builder.adjust(2)
    await message.answer('Настройки поиска:', reply_markup=builder.as_markup())


@router.message(commands='last')
async def cmd_last(message: Message):
    await out_last(message)


@router.message(commands='reverse_last')
async def cmd_reverse_last(message: Message):
    await out_last(message, reverse=True)
