from aiogram.dispatcher.router import Router
from aiogram.types import Message

import ydb_driver
from handlers.options import transport_kb_builder, time_zone_kb_builder


router = Router()

start_msg = '''Чтобы выполнить поиск введите названия начальной, 
а затем конечной станции одним сообщением, разделяя названия запятой (,)
Также вы можете указать время и/или дату поиска написав их после конечной станции, время от даты разделяйте пробелом
Например: "Начальная, конечная, 17.20 22.09.22"\n'''


@router.message(commands='start')
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if not await ydb_driver.check_user(user_id):
        await ydb_driver.add_user(user_id)
        await message.answer('Пользователь зарегестрирован')
    await message.answer(start_msg)
    tr_builder, tz_builder = transport_kb_builder(), time_zone_kb_builder()
    await message.answer(f'Укажите часовой пояс (UTC)', reply_markup=tz_builder.as_markup())
    await message.answer(f'Укажите желаемый вид транспорта', reply_markup=tr_builder.as_markup())
    await message.answer('Введите регион с клавиатуры')
    await ydb_driver.update_data(user_id, 'state', 'inp_region')


help_msg = '''Регион: <b>{}</b>
Транспорт: <b>{}</b>
Часовой пояс +{}'''


@router.message(commands='help')
async def cmd_help(message: Message):
    cur_id = message.from_user.id
    data = await ydb_driver.get_data(cur_id, 'region', 'transport_type', 'time_zone')
    await message.answer(start_msg + help_msg.format(*data))
