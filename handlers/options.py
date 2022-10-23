from typing import Callable, Dict, Any, Awaitable

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from driver_init import main_driver as driver
from requests_data import search_requests


router = Router()


@router.message.outer_middleware()
async def check_state_middleware(
    handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
    event: Message,
    data: Dict[str, Any]
):
    user_id = event.from_user.id
    state = await driver.get_data(user_id, 'state')
    states_dict = {'inp_region': set_region}
    if state[0]:
        return await states_dict[state[0]](event)
    else:
        return await handler(event, data)


kb_builder_dict = {
        'time_zone': {'keys': range(0, 13), 'callback': 'set_tz_{}'},
        'num': {'keys': [1, 3, 5, 7], 'callback': 'set_n_{}'},
        'transport_type': {'keys': ['Автобус', 'Поезд', 'Электричка'], 'callback': 'set_tr_{}'}
    }


def kb_builder(keyboard_type: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    kb = kb_builder_dict[keyboard_type]
    for value in kb['keys']:
        builder.add(
            InlineKeyboardButton(
                text='{}'.format(value),
                callback_data=kb['callback'].format(value)
            )
        )
    builder.add(
        InlineKeyboardButton(
            text='<<',
            callback_data='OPT')
    )
    builder.adjust(4)
    return builder


option_dict = {
    'Регион': 'opt_r',
    'Тип транспорта': 'opt_tr',
    'Часовой пояс': 'opt_tz',
    'Отображаемое количество рейсов': 'opt_n',
    'Закрыть клавиатуру': 'OUT'
}


@router.callback_query(F.data.startswith('OPT'))
async def cmd_option(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for option in option_dict:
        builder.add(
            InlineKeyboardButton(
                text=option,
                callback_data=option_dict[option]
            )
        )
    builder.adjust(2)
    await callback.message.edit_text('Настройки поиска:', reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('opt'))
async def set_option(callback: CallbackQuery):
    action = callback.data.split('_')[1]
    action_dict = {
        'r': opt_region,
        'setreg': opt_set_region,
        'tz': opt_timezone,
        'n': opt_num,
        'tr': opt_transport,
    }
    await action_dict[action](callback)


async def opt_region(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
                text='Поиск по всем регионам',
                callback_data=f'set_region_none'))
    builder.add(InlineKeyboardButton(
                text='Ввести регион',
                callback_data=f'opt_setreg'))
    builder.add(InlineKeyboardButton(
            text='<<',
            callback_data='OPT'))
    await callback.message.edit_text(f'Настройки региона:', reply_markup=builder.as_markup())


async def opt_set_region(callback: CallbackQuery):
    user_id = callback.from_user.id
    await driver.update_data(user_id, 'state', 'inp_region')
    await callback.message.edit_text(f'Введите регион:')


async def set_region(message: Message):
    try:
        region = search_requests.find_region_name(message.text)
    except IndexError:
        await message.answer('Регион не найден')
        return
    user_id = message.from_user.id
    await driver.update_data(user_id, 'region', region)
    await message.answer(f'Выбранный регион: <b>{region}</b>')
    await driver.update_data(user_id, 'state', None)


async def opt_timezone(callback: CallbackQuery):
    builder = kb_builder('time_zone')
    await callback.message.edit_text(f'Укажите часовой пояс (UTC)', reply_markup=builder.as_markup())


async def opt_num(callback: CallbackQuery):
    builder = kb_builder('num')
    await callback.message.edit_text(f'Укажите отображаемое количество рейсов', reply_markup=builder.as_markup())


async def opt_transport(callback: CallbackQuery):
    builder = kb_builder('transport_type')
    await callback.message.edit_text(f'Укажите желаемый вид транспорта', reply_markup=builder.as_markup())


options_cb_handler_dict = {
        'tr': 'transport_type',
        'tz': 'time_zone',
        'n': 'num',
        'region': 'region'
    }


@router.callback_query(F.data.startswith('set'))
async def options_callback_handler(callback: CallbackQuery):
    user_id, data, value = callback.from_user.id, callback.data.split('_')[1], callback.data.split('_')[2]
    if data == 'region':
        value = None
    await driver.update_data(user_id, options_cb_handler_dict[data], value)
    await callback.message.edit_text('Настройки успешно внесены')
    await callback.answer()
