import csv
import os
import time as _time
import requests
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify

app = Flask(__name__)

RIPTA_URL = 'http://realtime.ripta.com:81/api/tripupdates?format=json'

WEATHERAPI_URL = (
    'http://api.weatherapi.com/v1/forecast.json'
    '?key=341dd973faff4befb4625011260509'
    '&q=41.8491001,-71.3969192&days=1&aqi=no&alerts=no'
)

_weather_cache = {
    'temp_f': None,
    'precip_pct_now': None,
    'precip_pct_later': None,
    'has_snow': False,
}


def fetch_weather():
    return (
        _weather_cache['temp_f'],
        _weather_cache['precip_pct_now'],
        _weather_cache['precip_pct_later'],
        _weather_cache['has_snow'],
    )


# Regenerated from GTFS effective 2026-08-29
STOP_OFFSET_RT11 = {
    '4885847': 11, '4885901': 12, '4885902': 12, '4885903': 13, '4885904': 13, 
    '4885905': 13, '4885906': 13, '4885907': 13, '4885908': 13, '4885909': 13, 
    '4885910': 13, '4885911': 13, '4885912': 15, '4885913': 15, '4885914': 15, 
    '4885915': 15, '4885916': 15, '4885917': 15, '4885918': 15, '4885919': 15, 
    '4885920': 15, '4885921': 15, '4885922': 15, '4885923': 15, '4885924': 15, 
    '4885925': 15, '4885926': 15, '4885927': 15, '4885928': 15, '4885929': 15, 
    '4885930': 15, '4885931': 15, '4885932': 15, '4885933': 14, '4885934': 14, 
    '4885935': 14, '4885936': 14, '4885937': 14, '4885938': 14, '4885939': 14, 
    '4885940': 14, '4885941': 13, '4885942': 13, '4885943': 13, '4885944': 13, 
    '4885945': 13, '4885946': 13, '4885947': 13, '4885948': 13, '4885949': 12, 
    '4902036': 13, '4902037': 13, '4902038': 13, '4902039': 12, '4902040': 12, 
    '4902041': 12, '4902042': 13, '4902043': 13, '4902044': 13, '4902045': 13, 
    '4902046': 13, '4902047': 13, '4902048': 13, '4902049': 13, '4902050': 13, 
    '4902051': 13, '4902052': 13, '4902053': 13, '4902054': 14, '4902055': 14, 
    '4902056': 14, '4902057': 14, '4902058': 15, '4902059': 15, '4902060': 14, 
    '4902061': 14, '4902062': 14, '4902063': 14, '4902064': 14, '4902065': 14, 
    '4902066': 13, '4902067': 13, '4902068': 13, '4902069': 13, '4902070': 13, 
    '4902071': 13, '4902072': 13, '4902073': 13, '4902074': 13, '4902075': 13, 
    '4902076': 13, '4902077': 13, '4902078': 13, '4902079': 13, '4902080': 12, 
    '4902081': 12, '4902082': 12, '4906895': 14, '4906898': 15, '4907601': 14, 
    '4907604': 14, '4907607': 16, '4907610': 14, '4907625': 14, '4907628': 15, 
    '4907865': 12, '4907868': 14, '4907871': 14, '4907874': 14, '4907877': 14, 
    '4907880': 15, '4908042': 13, '4908045': 14, '4908048': 14, '4908051': 14, 
    '4908054': 16, '4908057': 15, '4908060': 13, '4908063': 13, '4908066': 12, 
    '4908133': 13, '4908136': 14, '4908139': 14, '4908142': 14, '4908145': 15, 
    '4908148': 15, '4908152': 13, '4908155': 13, '4908159': 12, '4908162': 14, 
    '4908165': 15, '4908168': 14, '4908171': 14, '4908174': 16, '4908177': 13, 
    '4908180': 13, '4908183': 12, '4908212': 16, '4908272': 12, '4908275': 14, 
    '4908278': 15, '4908281': 14, '4908284': 14, '4908287': 16, '4908290': 13, 
    '4908293': 13, '4908296': 13, '4908981': 12, '4908984': 14, '4908987': 15, 
    '4908990': 14, '4908993': 14, '4908996': 16, '4909046': 13, '4909049': 14, 
    '4909052': 14, '4909055': 14, '4909058': 16, '4909061': 14, '4909064': 13, 
    '4909067': 13, '4909070': 12, '4909117': 13, '4909120': 14, '4909123': 14, 
    '4909126': 14, '4909129': 16, '4909132': 15, '4909135': 13, '4909138': 13, 
    '4909141': 12, '4909393': 16, '4909396': 15, '4909710': 14, '4909713': 13, 
}

# Regenerated from GTFS effective 2026-08-29
STOP_OFFSET_RT1 = {
    '4886428': 9, '4886432': 9, '4886438': 9, '4886442': 9, '4886445': 21, 
    '4886454': 9, '4886455': 9, '4886456': 9, '4886460': 21, '4886464': 21, 
    '4886466': 21, '4886468': 21, '4886470': 22, '4886472': 22, '4886479': 9, 
    '4886480': 9, '4886481': 9, '4886485': 22, '4886490': 22, '4886491': 9, 
    '4886493': 21, '4886498': 21, '4902375': 8, '4902381': 8, '4902382': 9, 
    '4902391': 9, '4902399': 20, '4902400': 20, '4902406': 9, '4902411': 20, 
    '4902412': 20, '4902413': 20, '4902417': 20, '4902419': 9, '4902427': 20, 
    '4902428': 9, '4902433': 20, '4902436': 9, '4902441': 20, '4902445': 9, 
    '4902451': 20, '4902454': 8, '4902459': 20, '4906851': 24, '4906853': 23, 
    '4906855': 23, '4906857': 24, '4906859': 21, '4907835': 0, '4907954': 0, 
    '4908380': 24, '4908382': 23, '4908384': 23, '4908386': 24, '4908388': 22, 
    '4908596': 24, '4908598': 23, '4908600': 23, '4908602': 24, '4908676': 21, 
    '4909076': 10, '4909082': 10, '4909088': 10, '4909094': 10, '4909100': 10, 
    '4909106': 9, '4909112': 9, '4909382': 22, '4909384': 23, '4909386': 23, 
    '4909388': 24, '4909390': 24, '4910016': 10, '4910022': 10, '4910028': 10, 
    '4910034': 10, '4910040': 9, '4910046': 9, '4910048': 9, '4910055': 10, 
    '4910061': 10, '4910067': 10, '4910073': 10, '4910079': 9, '4910085': 9, 
    '4910087': 9, '4910091': 10, '4910097': 10, '4910103': 10, '4910109': 10, 
    '4910115': 9, '4910121': 9, 
}

SCHEDULE_RT11 = []
SCHEDULE_RT1 = []
CALENDAR = {}
TRIP_HEADSIGNS = {}


def load_schedule():
    global SCHEDULE_RT11, SCHEDULE_RT1, CALENDAR, TRIP_HEADSIGNS
    base = os.getcwd()

    cal = defaultdict(set)
    with open(os.path.join(base, 'calendar_dates.csv')) as f:
        reader = csv.DictReader(f)
        for row in reader:
            cal[row['date'].strip()].add(row['service_id'].strip())
    CALENDAR = dict(cal)

    with open(os.path.join(base, 'route11_stop20535.csv')) as f:
        reader = csv.DictReader(f)
        for row in reader:
            SCHEDULE_RT11.append((
                time_str_to_minutes(row['arrival_time']),
                row['headsign'],
                row['service_id'],
            ))
            TRIP_HEADSIGNS[row['trip_id']] = row['headsign']
    SCHEDULE_RT11.sort(key=lambda x: x[0])

    with open(os.path.join(base, 'route1_stop20280.csv')) as f:
        reader = csv.DictReader(f)
        for row in reader:
            SCHEDULE_RT1.append((
                time_str_to_minutes(row['arrival_time']),
                row['headsign'],
                row['service_id'],
            ))
            TRIP_HEADSIGNS[row['trip_id']] = row['headsign']
    SCHEDULE_RT1.sort(key=lambda x: x[0])


def time_str_to_minutes(t):
    parts = t.split(':')
    return int(parts[0]) * 60 + int(parts[1])


def eastern_now():
    return datetime.now(timezone.utc) - timedelta(hours=4)


def now_minutes():
    t = eastern_now()
    return t.hour * 60 + t.minute


def today_date_str():
    return eastern_now().strftime('%Y%m%d')


def active_service_ids():
    return CALENDAR.get(today_date_str(), set())


def shorten_destination(dest):
    dest = dest.strip()
    dest_upper = dest.upper()

    if 'BROAD STREET TERMINAL' in dest_upper or 'BROAD ST' in dest_upper:
        return 'BrdSt'
    if 'TF GREEN AIRPORT' in dest_upper:
        return 'TFGrn'
    if "SHAW'S" in dest_upper:
        return 'Shaws'

    dest = dest_upper
    replacements = [
        ('PROVIDENCE', 'PVD'),
        ('KENNEDY PLAZA', 'KP'),
        ('PAWTUCKET', 'PWT'),
        ('CRANSTON', 'CRAN'),
        ('NEWPORT', 'NWPT'),
        ('STATION', 'STA'),
        ('TERMINAL', 'TERM'),
        ('NORTH ', 'N '),
        ('SOUTH ', 'S '),
        ('EAST ', 'E '),
        ('WEST ', 'W '),
    ]
    for long, short in replacements:
        dest = dest.replace(long, short)
    return dest


def get_live_results(offset_table, route_label, current_minutes, feed):
    results = []
    for entity in feed.get('entity', []):
        trip_update = entity.get('trip_update')
        if not trip_update:
            continue
        trip = trip_update.get('trip', {})
        trip_id = str(trip.get('trip_id', ''))
        if trip_id not in offset_table:
            continue
        start_time_str = trip.get('start_time', '')
        if not start_time_str:
            continue
        start_minutes = time_str_to_minutes(start_time_str)
        offset = offset_table[trip_id]
        delay_seconds = 0
        updates = trip_update.get('stop_time_update', [])
        if updates:
            last = updates[-1]
            arrival = last.get('arrival') or last.get('departure')
            if arrival:
                delay_seconds = arrival.get('delay', 0)
        delay_minutes = delay_seconds // 60
        estimated_arrival = start_minutes + offset + delay_minutes
        minutes_away = estimated_arrival - current_minutes
        if minutes_away < 0:
            continue
        if route_label == 'R' and minutes_away <= 6:
            continue
        headsign = TRIP_HEADSIGNS.get(trip_id, '')
        dest = shorten_destination(headsign) if headsign else 'PVD'
        results.append({
            'route': route_label,
            'destination': route_label + ' ' + dest,
            'arrival': str(minutes_away) if minutes_away > 0 else 'BRD',
            'live': True,
            'urgent': minutes_away <= (10 if route_label == 'R' else 5),
        })
    results.sort(key=lambda r: int(r['arrival']) if r['arrival'] != 'BRD' else 0)
    return results


def get_scheduled_results(schedule, route_label, current_minutes, count=1):
    today_services = active_service_ids()
    results = []
    for arrival_minutes, headsign, service_id in schedule:
        if service_id not in today_services:
            continue
        minutes_away = arrival_minutes - current_minutes
        if minutes_away < 0 or minutes_away > 90:
            continue
        if route_label == 'R' and minutes_away <= 6:
            continue
        results.append({
            'route': route_label,
            'destination': route_label + ' ' + shorten_destination(headsign),
            'arrival': str(minutes_away) if minutes_away > 0 else 'BRD',
            'live': False,
            'urgent': minutes_away <= (10 if route_label == 'R' else 5),
        })
        if len(results) == count:
            break
    return results


def deduplicate_results(results):
    live = [r for r in results if r['live']]
    scheduled = [r for r in results if not r['live']]
    filtered_scheduled = []
    for s in scheduled:
        s_min = int(s['arrival']) if s['arrival'] != 'BRD' else 0
        too_close = False
        for l in live:
            l_min = int(l['arrival']) if l['arrival'] != 'BRD' else 0
            if s['route'] == l['route'] and abs(s_min - l_min) <= 3:
                too_close = True
                break
        if not too_close:
            filtered_scheduled.append(s)
    return live + filtered_scheduled


@app.route('/')
def health():
    return 'ok', 200


@app.route('/ping')
def ping():
    global _weather_cache
    try:
        data = requests.get(WEATHERAPI_URL, timeout=5).json()
        if 'error' not in data:
            temp_f = data['current']['temp_f']
            condition_code = data['current']['condition']['code']
            # WeatherAPI snow condition codes
            snow_codes = {1114, 1117, 1210, 1213, 1216, 1219, 1222, 1225,
                          1255, 1258, 1279, 1282}
            has_snow = condition_code in snow_codes

            # Hourly precip probability for next 3 hours
            now = eastern_now()
            current_hour = now.hour
            hourly = data['forecast']['forecastday'][0]['hour']
            next_3 = [h['chance_of_rain'] for h in hourly
                      if int(h['time'].split(' ')[1].split(':')[0]) >= current_hour][:3]
            precip_pct_now = max(next_3) if next_3 else 0

            # Daily max precip probability
            precip_pct_later = data['forecast']['forecastday'][0]['day']['daily_chance_of_rain']

            _weather_cache = {
                'temp_f': temp_f,
                'precip_pct_now': precip_pct_now,
                'precip_pct_later': precip_pct_later,
                'has_snow': has_snow,
            }
            print('Weather updated: temp=%s now=%s later=%s snow=%s' % (
                temp_f, precip_pct_now, precip_pct_later, has_snow))
        else:
            print('WeatherAPI error:', data.get('error', {}).get('message'))
    except Exception as e:
        print('ping weather error:', e)
    return 'ok', 200


@app.route('/debug')
def debug():
    try:
        data = requests.get(RIPTA_URL, timeout=10).json()
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    current_minutes = now_minutes()
    trips = []
    for entity in data.get('entity', []):
        trip_update = entity.get('trip_update')
        if not trip_update:
            continue
        trip = trip_update.get('trip', {})
        route = str(trip.get('route_id', ''))
        if route not in ('1', '11'):
            continue
        trip_id = str(trip.get('trip_id', ''))
        in_lookup = trip_id in STOP_OFFSET_RT11 or trip_id in STOP_OFFSET_RT1
        trips.append({
            'route_id': route,
            'trip_id': trip_id,
            'start_time': trip.get('start_time'),
            'in_lookup': in_lookup,
        })

    return jsonify({
        'current_minutes_since_midnight': current_minutes,
        'today_date': today_date_str(),
        'active_service_ids': list(active_service_ids()),
        'trips_in_feed': trips,
    })


@app.route('/board')
def board():
    current_minutes = now_minutes()
    all_results = []

    try:
        feed = requests.get(RIPTA_URL, timeout=10).json()
        all_results += get_live_results(STOP_OFFSET_RT11, 'R', current_minutes, feed)
        all_results += get_live_results(STOP_OFFSET_RT1, '1', current_minutes, feed)
    except Exception:
        pass

    live_r_count = sum(1 for r in all_results if r['route'] == 'R')
    live_1_count = sum(1 for r in all_results if r['route'] == '1')

    if live_r_count < 2:
        all_results += get_scheduled_results(SCHEDULE_RT11, 'R', current_minutes, count=2 - live_r_count)
    if live_1_count < 2:
        all_results += get_scheduled_results(SCHEDULE_RT1, '1', current_minutes, count=2 - live_1_count)

    all_results = deduplicate_results(all_results)
    all_results.sort(key=lambda r: int(r['arrival']) if r['arrival'] != 'BRD' else 0)

    temp_f, precip_pct_now, precip_pct_later, has_snow = fetch_weather()

    return jsonify({
        'buses': all_results[:3],
        'temp_f': temp_f,
        'precip_pct_now': precip_pct_now,
        'precip_pct_later': precip_pct_later,
        'has_snow': has_snow,
    })


MINI_WALK_TIMES = {'R': 6, '1': 2}


def apply_walk_time(results, walk_times):
    adjusted = []
    for r in results:
        if r['arrival'] == 'BRD':
            continue
        arrival_min = int(r['arrival'])
        walk = walk_times.get(r['route'], 0)
        departure = arrival_min - walk
        if departure <= 0:
            continue
        adjusted.append({
            'route': r['route'],
            'departure': str(departure),
            'live': r['live'],
            'urgent': departure <= 5,
        })
    return adjusted


@app.route('/mini')
def mini():
    current_minutes = now_minutes()
    all_results = []

    try:
        feed = requests.get(RIPTA_URL, timeout=10).json()
        all_results += get_live_results(STOP_OFFSET_RT11, 'R', current_minutes, feed)
        all_results += get_live_results(STOP_OFFSET_RT1, '1', current_minutes, feed)
    except Exception:
        pass

    live_r_count = sum(1 for r in all_results if r['route'] == 'R')
    live_1_count = sum(1 for r in all_results if r['route'] == '1')

    if live_r_count < 5:
        all_results += get_scheduled_results(SCHEDULE_RT11, 'R', current_minutes, count=5 - live_r_count)
    if live_1_count < 2:
        all_results += get_scheduled_results(SCHEDULE_RT1, '1', current_minutes, count=2 - live_1_count)

    all_results = deduplicate_results(all_results)
    all_results.sort(key=lambda r: int(r['arrival']) if r['arrival'] != 'BRD' else 0)
    all_results = apply_walk_time(all_results, MINI_WALK_TIMES)

    route_limits = {'R': 5, '1': 2}
    route_counts = {}
    final = []
    for r in all_results:
        limit = route_limits.get(r['route'], 0)
        count = route_counts.get(r['route'], 0)
        if count < limit:
            final.append(r)
            route_counts[r['route']] = count + 1

    return jsonify({'buses': final})


if __name__ == '__main__':
    load_schedule()
    app.run(host='0.0.0.0', port=10000)


with app.app_context():
    try:
        load_schedule()
        print('Schedule loaded: RT11', len(SCHEDULE_RT11), 'RT1', len(SCHEDULE_RT1), 'Calendar dates', len(CALENDAR))
    except Exception as e:
        print('Warning: could not load schedule:', e)
        import traceback
        traceback.print_exc()
