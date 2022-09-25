from typing import Callable, Dict, Any, Awaitable

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import available_transport, option_dict, values_kb_builder_templates, options_cb_handler_templates
import ydb_driver
from regionsdata import search_requests


router = Router()


def values_kb_builder(template):
    builder = InlineKeyboardBuilder()
    template_dict = values_kb_builder_templates[template]
    for value in template_dict['iterable']:
        builder.add(
            InlineKeyboardButton(
                text='{}'.format(value),
                callback_data=template_dict['cb_data'].format(value)
            )
        )
    builder.adjust(4)
    return builder


def transport_kb_builder():
    builder = InlineKeyboardBuilder()
    for transport in available_transport:
        builder.add(
            InlineKeyboardButton(
                text=transport[0],
                callback_data=f'set_tr_{transport[1]}'
            )
        )
    builder.adjust(2)
    return builder


@router.message.outer_middleware()
async def check_state_middleware(
    handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
    event: Message,
    data: Dict[str, Any]
) -> Any:
    user_id = event.from_user.id
    state = await ydb_driver.get_data(user_id, 'state')
    states_dict = {'inp_region': set_region}
    if state[0]:
        return await states_dict[state[0]](event)
    else:
        return await handler(event, data)


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


@router.callback_query(F.data.startswith('opt'))
async def set_option(callback: CallbackQuery):
    action = callback.data.split('_')[1]
    action_dict = {'r': opt_region, 'tr': opt_transport, 'tz': opt_timezone, 'n': opt_num, 'out': opt_out}
    await action_dict[action](callback)


async def opt_out(callback: CallbackQuery):
    await callback.message.edit_text('Действие отменено')
    await callback.answer()


async def opt_region(callback: CallbackQuery):
    await callback.message.edit_text(f'Введите регион:')
    user_id = callback.from_user.id
    await ydb_driver.update_data(user_id, 'state', 'inp_region')
    await callback.answer()


async def set_region(message: Message):
    try:
        region = search_requests.find_region(message.text)
    except IndexError:
        await message.answer('Регион не найден')
        return
    user_id = message.from_user.id
    await ydb_driver.update_data(user_id, 'region', region)
    await message.answer(f'Выбранный регион: <b>{region}</b>')
    await ydb_driver.update_data(user_id, 'state', None)


async def opt_transport(callback: CallbackQuery):
    builder = transport_kb_builder()
    await callback.message.edit_text(f'Укажите желаемый вид транспорта', reply_markup=builder.as_markup())


async def opt_timezone(callback: CallbackQuery):
    builder = values_kb_builder('time_zone')
    await callback.message.edit_text(f'Укажите часовой пояс (UTC)', reply_markup=builder.as_markup())


async def opt_num(callback: CallbackQuery):
    builder = values_kb_builder('num')
    await callback.message.edit_text(f'Укажите отображаемое количество рейсов', reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('set'))
async def options_callback_handler(callback: CallbackQuery):
    user_id, data, value = callback.from_user.id, callback.data.split('_')[1], callback.data.split('_')[2]
    await ydb_driver.update_data(user_id, options_cb_handler_templates[data], value)
    await callback.message.edit_text('Настройки успешно внесены')

    await callback.answer()
