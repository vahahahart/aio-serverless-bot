import os

available_transport = [['автобус', 'bus'], ['электричка/поезд', 'train']]

option_dict = {
    'Изменить регион': 'opt_r',
    'Изменить тип транспорта': 'opt_tr',
    'Изменить часовой пояс': 'opt_tz',
    'Отмена': 'opt_out'
}

REQ_PARAMS = {
        'format': 'json',
        'apikey': os.environ['YANDEX_API_KEY'],
        'limit': 200,
        'show_systems': 'yandex'
    }
