import os
import json
from typing import Generator
from itertools import chain
from datetime import datetime, date, timedelta
import re

import requests

REQ_PARAMS = {
        'format': 'json',
        'apikey': os.environ['YANDEX_API_KEY'],
        'limit': 200,
        'show_systems': 'yandex'
    }


station_types = {
    'bus_stop': 'авт.ост. ',
    'station': 'ст. ',
    'platform': 'плт. ',
    'stop': 'ост. ',
    'checkpoint': 'бп. ',
    'post': 'пост ',
    'crossing': 'рзд. ',
    'overtaking_point': 'о.п. ',
    'train_station': 'вкз. ',
    'airport': 'а/п',
    'bus_station': 'авт.вкз. ',
    'unknown': '',
    'port': 'порт',
    'port_point': 'порт ',
    'wharf': 'п. ',
    'river_port': 'реч.вкз. ',
    'marine_station': 'мор.вкз. ',
    '': 'о.п. '
}

with open(os.path.dirname(os.path.abspath(__file__)) + r'\stations.json', encoding='utf-8') as f:
    DATA = json.load(f)


def re_search_name(name: str, name_in_list: str) -> bool:
    return bool(re.search(rf'.*\b{name.lower()}.*', name_in_list.lower()))


def find_name_in_region(name: str, region: str) -> chain[Generator]:
    setl_gen = ([setl['title'] + ', ' + region, setl['code']] for setl in
                DATA[region] if re_search_name(name, setl['title']))
    stn_gen_list = []
    for setl in DATA[region]:
        stn_gen = ([station_types[stn['station_type']] + stn['title'] + ', ' + region, stn['code']] for stn in
                   setl['stations'] if re_search_name(name, stn['title']))
        stn_gen_list.append(stn_gen)
    return chain(setl_gen, *stn_gen_list)


def find_region_name(region: str) -> str:
    region = region.lower()
    reg_list = (name for name in DATA if re.search(rf'.*\b{region}.*', name.lower()))
    return next(reg_list)


def station_name_to_code_gen(station: str, region: str = None):
    station = station.lower()
    if region:
        return find_name_in_region(station, region)
    else:
        gen_list = []
        for region in DATA:
            gen_list.append(find_name_in_region(station, region))
        return chain(*gen_list)


if __name__ == '__main__':
    inp = '12.20 12.22.23'
    out = re.findall(r'\b((?:\d{2}\.){2}\d{2})\b|\b(\d{2}\.\d{2})\b', inp)
    print(out)


def codes_to_time(
        from_id: str,
        to_id: str,
        tz: str,
        num: str,
        transport_type: str = None,
        dt: str = None
) -> list[dict[str, str]]:

    search_datetime = datetime.utcnow() + timedelta(hours=int(tz))
    search_date = date.today()

    if dt:
        dt = re.findall(r'\b((?:\d{2}\.){2}\d{2})\b|\b(\d{2}\.\d{2})\b', dt)
        for match in dt:
            search_date = datetime.strptime(match[0], '%d.%m.%y') if match[0] else search_date
            search_datetime = datetime.strptime(match[1], '%H.%M') if match[1] else search_datetime

    params = REQ_PARAMS.copy()
    params['from'],  params['to'] = from_id, to_id
    params['date'] = search_date.isoformat()
    if transport_type:
        params['transport_types'] = transport_type

    req = requests.get('https://api.rasp.yandex.net/v3.0/search/', params=params)
    output_info = json.loads(req.text)

    num = int(num)
    time_list = []
    n = 0

    time_list.append(
        {
            'name_from': output_info['search']['from']['title'],
            'name_to': output_info['search']['to']['title'],
            'date': '.'.join(output_info['search']['date'].split('-')[::-1])
        }
    )
    for segment in output_info['segments']:
        if datetime.fromisoformat(segment['departure']).time() > search_datetime.time():
            time_list.append({
                'title': segment['thread']['title'],
                'departure': segment['departure'][11:16],
                'arrival': segment['arrival'][11:16],
                'duration': int(segment['duration'] // 60)
            })
            n += 1
        if num <= n:
            break
    return time_list
