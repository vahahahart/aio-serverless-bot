from aiogram.dispatcher.router import Router
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from driver_init import main_driver as driver


router = Router()


param_msg = '''
Регион: <b>{}</b>
Транспорт: <b>{}</b>
Часовой пояс  <b>{}</b>'''

params_dict = {
    'Настройки поиска': 'OPT',
    # 'Погода': 'WEATH',
    'Помощь': 'HELP',
    'О боте': 'ABOUT'
}


@router.message(commands='menu')
async def cmd_params(message: Message):
    builder = InlineKeyboardBuilder()
    for param in params_dict:
        builder.add(
            InlineKeyboardButton(
                text=param,
                callback_data=params_dict[param]
            )
        )
    builder.add(
        InlineKeyboardButton(
            text='Зактрыть клавиатуру',
            callback_data='OUT')
    )
    builder.adjust(3)
    user_id = message.from_user.id
    data = await driver.get_data(user_id, 'region', 'transport_type', 'time_zone')
    await message.answer('Сейчас установлено: ' + param_msg.format(*data))
    await message.answer('<b>МЕНЮ</b>', reply_markup=builder.as_markup())
