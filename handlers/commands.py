from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.types import Message, CallbackQuery

from driver_init import main_driver as driver
from handlers.search import out_last
from handlers.options import kb_builder

router = Router()

start_msg = '''
<b>БОТ ПОИСКА РАСПИСАНИЙ ТРАНСПОРТА</b>

В данный момент поддерживаются междугородние автобусы, поезда, электрички и даже самолеты.
Бот запоминает ваш последний запрос, но при этом 
не хранит и не собирает информация обо всех ваших передвижениях!

<b>Доступные команды:</b>
/help - Помощь
/params - Меню параметров
/last - Поиск по последнему маршруту
/reverse_last - Поиск обратного маршрута

Чтобы выполнить поиск введите названия начальной, 
а затем конечной станций одним сообщением, 
разделяя названия двумя тире (--).

Если бот не находит нужную станцию, укажите регион поиска в настройках или в самом запросе.

Также вы можете указать время и/или дату поиска отделив их от конечной станции двумя тире, 
время от даты разделяйте пробелом
<b>Формат ввода времени:</b> <i>ЧЧ.ММ</i>
<b>Формат даты:</b> <i>ДД.ММ.ГГ</i>

Примерный запрос: 
"Начальная, Регион1 -- Конечная, Регион2 -- 17.20 22.09.22"\n'''


@router.message(commands='start')
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if not await driver.check_user(user_id):
        await driver.add_user(user_id)
        await driver.update_data(user_id, 'num', '3')
    await message.answer('<b>СТАРТ БОТА\n</b>' + start_msg)
    tz_builder = kb_builder('time_zone')
    await message.answer(
        f'Установите ваш часовой пояс (UTC) перед началом работы. ' +
        f'В дальнейшем его можно будет поменять в параметрах поиска',
        reply_markup=tz_builder.as_markup()
    )


help_msg = '''
<b>Формат ввода времени:</b> <i>ЧЧ.ММ</i>
<b>Формат даты:</b> <i>ДД.ММ.ГГ</i>
<b>Пример запроса:</b>
"Начальная, Регион1 -- Конечная, Регион2 -- 17.20 22.09.22"

<b>Доступные команды:</b>
/help - Помощь
/menu - Меню бота, где вы можете поменять настройки
/last - Поиск по последнему маршруту
/reverse_last - Поиск обратного маршрута

В данный момент поддерживаются междугородние автобусы, поезда, электрички и самолеты.

Чтобы выполнить поиск введите названия начальной, 
а затем конечной станции одним сообщением, 
разделяя названия двумя тире (--).

Если вы не можете найти в списке свою станцию, проверьте сообщение на опечатки, 
установите регион поиска в настройках или укажите его в сообщении запроса.
'''


@router.message(commands='help')
async def cmd_help(message: Message):
    await message.answer('<b>ПОМОЩЬ\n</b>' + help_msg)


@router.callback_query(F.data.startswith('HELP'))
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text('<b>ПОМОЩЬ\n</b>' + help_msg)


info_msg = '''
Бот создан при помощи aiogram 3.0.0b4
Поиск расписания происходит благодаря сервису <a href="https://rasp.yandex.ru/">Яндекс.Расписания</a>

<b>Связаться с разработчиком</b>
email - vahahahart@yandex.ru
'''


@router.callback_query(F.data.startswith('ABOUT'))
async def cb_help(callback: CallbackQuery):
    await callback.message.edit_text('<b>О БОТЕ\n</b>' + info_msg)


@router.message(commands='last')
async def cmd_last(message: Message):
    await out_last(message)


@router.message(commands='reverse_last')
async def cmd_reverse_last(message: Message):
    await out_last(message, reverse=True)


@router.callback_query(F.data.startswith('OUT'))
async def opt_out(callback: CallbackQuery):
    await callback.message.edit_text('Действие отменено')
    await callback.answer()
