import re
from typing import Optional, Union

from aiogram import types
from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import ContentTypesFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from regionsdata import search_requests as req
import ydb_driver


router = Router()


class StationsCallbackFactory(CallbackData, prefix='stn'):
    code: Optional[str]
    prev_stn: Optional[Union[str, None]]
    prev_code: Optional[Union[str, None]]
    dt: Optional[Union[str, None]]


async def station_kb_builder(event, station_to_code, prev_station=None, dt=None, prev_code=None):
    builder = InlineKeyboardBuilder()
    user_id = event.from_user.id
    data = await ydb_driver.get_data(user_id, 'region', 'transport_type')

    if None in data:
        return

    stations_and_codes = req.station_to_code(station_to_code, *data)

    if not stations_and_codes:
        return

    for station in stations_and_codes:
        builder.add(
            types.InlineKeyboardButton(
                text=station,
                callback_data=StationsCallbackFactory(
                    code=stations_and_codes[station],
                    prev_stn=prev_station,
                    prev_code=prev_code,
                    dt=dt
                ).pack()
            )
        )
    builder.adjust(1)
    return builder


@router.message(ContentTypesFilter(content_types=['text']))
async def inp_stations(message: types.Message):
    match = re.findall(r'\s*([\w\s.]+)\s*', message.text)
    station_builder = await station_kb_builder(message, *match)

    if station_builder:
        await message.answer('Укажите начальную станцию', reply_markup=station_builder.as_markup(resize_keyborad=True))
    else:
        await message.answer('Начальная станция не найдена')


start_text = '''Начальная ст. <b>{}</b>
Конечная ст. <b>{}</b>
Дата <b>{}</b>'''

info_text = '''Рейс <b>{}</b>
Отправляется в <b>{}</b>
Длительность <b>{}</b> мин
----
'''


@router.callback_query(StationsCallbackFactory.filter(F.prev_code))
async def reg2_station(callback: types.CallbackQuery, callback_data: StationsCallbackFactory):
    user_id = callback.from_user.id
    data = await ydb_driver.get_data(user_id, 'time_zone', 'num')
    await ydb_driver.update_data(user_id, 'last_codes', f'{callback_data.prev_code}_{callback_data.code}')

    try:
        time_list = req.codes_to_time(
            code_from=callback_data.prev_code,
            code_to=callback_data.code,
            tz=data[0],
            num=data[1],
            dt=callback_data.dt
        )
    except ValueError:
        await callback.message.edit_text('Неверный ввод времени/даты поиска!')
        await callback.answer()
        return
    text = '\n----\n'

    if time_list[1:]:
        for thread in time_list[1:]:
            text += info_text.format(
                thread['title'],
                thread['departure'],
                thread['duration']
            )
    else:
        text += 'Рейсов нет'

    await callback.message.edit_text(start_text.format(
        time_list[0]['name_from'],
        time_list[0]['name_to'],
        time_list[0]['date']
    ) + text)
    await callback.answer()


@router.callback_query(StationsCallbackFactory.filter())
async def reg_station(callback: types.CallbackQuery, callback_data: StationsCallbackFactory):
    try:
        builder = await station_kb_builder(callback, station_to_code=callback_data.prev_stn, dt=callback_data.dt,
                                           prev_code=callback_data.code)
    except AttributeError:
        await callback.message.edit_text('Пожалуйста вводите две станции, разделяя названия запятой!')
        return

    if builder:
        await callback.message.edit_text(f'Ввыберите конечную станцию',
                                         reply_markup=builder.as_markup(resize_keyborad=True))
    else:
        await callback.message.edit_text(f'Конечная станция не найдена')
