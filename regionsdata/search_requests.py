import json
from datetime import datetime, date, timedelta
import re

import requests

from config import REQ_PARAMS


# def main():
#     with open(r'regions.json', 'r+', encoding='utf-8') as f:
#         data = json.load(f)
#         for region in data:
#             for setl in data[region]:
#                 del setl['title']
#                 del setl['codes']
#                 for station in setl['stations']:
#                     del station['direction']
#                     del station['station_type']
#                     station['code'] = station['codes']['yandex_code']
#                     del station['codes']
#         f.seek(0)
#         json.dump(data, f, indent=4, ensure_ascii=False)
#         f.truncate()


def find_region(region_name):
    region_name = region_name.lower()
    with open(r'regionsdata/regions.json', encoding='utf-8') as f:
        data = json.load(f)
    return [name for name in data if re.search(rf'.*\b{region_name}.*', name.lower())][0]


def station_to_code(st_name, region_name, transport_type):
    st_name = st_name.lower()
    with open(r'regionsdata/regions.json', encoding='utf-8') as f:
        data = json.load(f)
        found_stations = {}
        for setl in data[region_name]:
            for stn in setl['stations']:
                if re.search(rf'.*\b{st_name}.*', stn['title'].lower()) and stn['transport_type'] == transport_type:
                    found_stations.update({stn['title']: stn['code']})
    return found_stations


def codes_to_time(code_from, code_to, tz, num=None, dt=None):
    if not dt:
        search_datetime = datetime.utcnow() + timedelta(hours=int(tz))
        search_date = date.today()
    elif len(dt) == 5:
        search_datetime = datetime.strptime(dt, '%H.%M') - timedelta(minutes=30)
        search_date = date.today()
    elif len(dt) == 8:
        search_datetime = datetime.utcnow() + timedelta(hours=int(tz))
        search_date = datetime.strptime(dt, '%d.%m.%y')
    else:
        search_datetime = datetime.strptime(dt, '%H.%M %d.%m.%y')
        search_date = search_datetime.date()

    params = REQ_PARAMS.copy()
    params['from'],  params['to'] = code_from, code_to
    params['date'] = search_date.isoformat()
    req = requests.get('https://api.rasp.yandex.net/v3.0/search/', params=params)
    output_info = json.loads(req.text)

    num = int(num) if num else 3
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
