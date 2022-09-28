import os

available_transport = [['автобус', 'bus'], ['электричка/поезд', 'train']]

option_dict = {
    'Регион': 'opt_r',
    'Тип транспорта': 'opt_tr',
    'Часовой пояс': 'opt_tz',
    'Отображаемое количество рейсов': 'opt_n',
    'Отмена': 'opt_out'
}

options_cb_handler_templates = {
        'tr': 'transport_type',
        'tz': 'time_zone',
        'n': 'num'
    }

values_kb_builder_templates = {
        'time_zone': {'iterable': range(0, 13), 'cb_data': 'set_tz_{}'},
        'num': {'iterable': [1, 3, 5, 7], 'cb_data': 'set_n_{}'}
    }

REQ_PARAMS = {
        'format': 'json',
        'apikey': os.environ['YANDEX_API_KEY'],
        'limit': 200,
        'show_systems': 'yandex'
    }
