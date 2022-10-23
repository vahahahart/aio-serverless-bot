import re
from typing import Optional, Union

from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import ContentTypesFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from driver_init import main_driver as driver
from requests_data import search_requests as req


router = Router()


class StationsCallbackFactory(CallbackData, prefix='stn'):
    id1: str
    stn2: Optional[Union[str, None]]
    id2: Optional[Union[str, None]]
    dt: Optional[Union[str, None]]


start_text = '''Начальная ст. <b>{}</b>
Конечная ст. <b>{}</b>
Дата <b>{}</b>'''

info_text = '''Рейс <b>{}</b>
Отправляется в <b>{}</b>
Длительность <b>{}</b> мин
----
'''

end_text = '''
<i>Данные предоставлены сервисом <a href="https://rasp.yandex.ru/">Яндекс.Расписания</a></i>
'''


def form_text(time_list: list[dict[str, str]]) -> str:
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
    text = start_text.format(
        time_list[0]['name_from'],
        time_list[0]['name_to'],
        time_list[0]['date']
    ) + text + end_text
    return text


async def station_kb_builder(
        uid: int,
        station_to_code: str,
        stn2: str = None,
        dt: str = None,
        id2: str = None,
        reg: str = None
) -> Union[InlineKeyboardBuilder, None]:

    builder = InlineKeyboardBuilder()
    if reg:
        reg = req.find_region_name(reg[0])
    else:
        data = await driver.get_data(uid, 'region')
        reg = data[0]
    found_stations = req.station_name_to_code_gen(station_to_code, reg)

    if not found_stations:
        return

    n = 0
    for station in found_stations:
        n += 1
        builder.add(
            InlineKeyboardButton(
                text=station[0],
                callback_data=StationsCallbackFactory(
                    id1=station[1],
                    stn2=stn2,
                    id2=id2,
                    dt=dt,
                ).pack()
            )
        )
        if n >= 9:
            builder.add(
                InlineKeyboardButton(
                    text='(Отмена) Много совпадающих станций, укажите регион',
                    callback_data='OUT')
            )
            break
    else:
        builder.add(
            InlineKeyboardButton(
                text='Отмена',
                callback_data='OUT')
        )
    builder.adjust(1)
    return builder


@router.callback_query(StationsCallbackFactory.filter(F.id2))
async def out_stations(callback: CallbackQuery, callback_data: StationsCallbackFactory):
    user_id = callback.from_user.id
    data = await driver.get_data(user_id, 'time_zone', 'num')

    try:
        time_list = req.codes_to_time(from_id=callback_data.id2, to_id=callback_data.id1, tz=data[0], num=data[1],
                                      dt=callback_data.dt)
    except ValueError:
        await callback.message.edit_text('Неверный ввод времени/даты поиска!')
        await callback.answer()
        return

    await driver.update_data(user_id, 'last_codes', f'{callback_data.id2}_{callback_data.id1}')
    text = form_text(time_list)
    await callback.message.edit_text(text, disable_web_page_preview=True)
    await callback.answer()


async def out_last(message: Message, reverse=False):
    user_id = message.from_user.id
    data = await driver.get_data(user_id, 'last_codes', 'time_zone', 'num')
    if not data[0]:
        await message.answer('Последний маршрут не сохранен')
        return
    if reverse:
        to_id, from_id = data[0].split('_')
        await driver.update_data(user_id, 'last_codes', '_'.join((from_id, to_id)))
    else:
        from_id, to_id = data[0].split('_')
    time_list = req.codes_to_time(from_id=from_id, to_id=to_id, tz=data[1], num=data[2])
    text = form_text(time_list)
    await message.answer(text, disable_web_page_preview=True)


@router.message(ContentTypesFilter(content_types=['text']))
async def inp_stations(message: Message):
    match = re.findall(r'\s*([\w\s.,]+[-]?[\w\s.,]+)\s*', message.text)
    user_id = message.from_user.id
    try:
        match1, match2, *dt = match
        stn1, *reg = re.findall(r'\b([\w\s-]+)\b', match1)
        station_builder = await station_kb_builder(user_id, station_to_code=stn1, stn2=match2, dt='-'.join(dt), reg=reg)
    except (KeyError, ValueError):
        await message.answer('Чтобы выполнить поиск необходимо ввести две станции через двойное тире (--)')
        return

    if station_builder:
        await message.answer(
            'Укажите начальную станцию',
            reply_markup=station_builder.as_markup(resize_keyborad=True),
            disable_web_page_preview=True
        )
    else:
        await message.answer('Начальная станция не найдена')


@router.callback_query(StationsCallbackFactory.filter())
async def inp_2_station(callback: CallbackQuery, callback_data: StationsCallbackFactory):
    user_id = callback.from_user.id
    try:
        stn2, *reg2 = re.findall(r'\b([\w\s-]+)\b', callback_data.stn2)
        builder = await station_kb_builder(user_id, station_to_code=stn2, dt=callback_data.dt,
                                           id2=callback_data.id1, reg=reg2)
    except AttributeError:
        await callback.message.edit_text('Чтобы выполнить поиск необходимо ввести две станции через запятую')
        return

    if builder:
        await callback.message.edit_text(f'Ввыберите конечную станцию',
                                         reply_markup=builder.as_markup(resize_keyborad=True))
    else:
        await callback.message.edit_text(f'Конечная станция не найдена')
