import csv
import os
import time as _time
import requests
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify

app = Flask(__name__)

RIPTA_URL = 'http://realtime.ripta.com:81/api/tripupdates?format=json'

OPEN_METEO_URL = (
    'https://api.open-meteo.com/v1/forecast'
    '?latitude=41.8491001&longitude=-71.3969192'
    '&current=temperature_2m'
    '&hourly=precipitation_probability'
    '&daily=precipitation_probability_max,weather_code'
    '&temperature_unit=fahrenheit&forecast_days=1&timezone=America%2FNew_York'
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


# Lookup table: trip_id -> minutes from trip start_time to arrival at stop 20535 (Route 11)
# Regenerated from GTFS effective 2026-06-22
STOP_OFFSET_RT11 = {
    '4771291': 14, '4771294': 15, '4771297': 14, '4771300': 14, '4771303': 16,
    '4771306': 14, '4771319': 14, '4771322': 15, '4771505': 12, '4771508': 14,
    '4771511': 14, '4771514': 14, '4771517': 14, '4771520': 15, '4771664': 13,
    '4771667': 14, '4771670': 14, '4771673': 14, '4771676': 16, '4771679': 15,
    '4771682': 13, '4771685': 13, '4771688': 12, '4771754': 13, '4771757': 14,
    '4771760': 14, '4771763': 14, '4771766': 15, '4771769': 15, '4771773': 13,
    '4771776': 13, '4771780': 12, '4771783': 14, '4771786': 15, '4771789': 14,
    '4771792': 14, '4771795': 16, '4771798': 13, '4771801': 13, '4771804': 12,
    '4771825': 16, '4771867': 12, '4771870': 14, '4771873': 15, '4771876': 14,
    '4771879': 14, '4771882': 16, '4771885': 13, '4771888': 13, '4771891': 13,
    '4772549': 12, '4772552': 14, '4772555': 15, '4772558': 14, '4772561': 14,
    '4772564': 16, '4772612': 13, '4772615': 14, '4772618': 14, '4772621': 14,
    '4772624': 16, '4772627': 14, '4772630': 13, '4772633': 13, '4772636': 12,
    '4772683': 13, '4772686': 14, '4772689': 14, '4772692': 14, '4772695': 16,
    '4772698': 15, '4772701': 13, '4772704': 13, '4772707': 12, '4772937': 16,
    '4772940': 15, '4773195': 14, '4773198': 13, '4776725': 11, '4776779': 12,
    '4776780': 12, '4776781': 13, '4776782': 13, '4776783': 13, '4776784': 13,
    '4776785': 13, '4776786': 13, '4776787': 13, '4776788': 13, '4776789': 13,
    '4776790': 15, '4776791': 15, '4776792': 15, '4776793': 15, '4776794': 15,
    '4776795': 15, '4776796': 15, '4776797': 15, '4776798': 15, '4776799': 15,
    '4776800': 15, '4776801': 15, '4776802': 15, '4776803': 15, '4776804': 15,
    '4776805': 15, '4776806': 15, '4776807': 15, '4776808': 15, '4776809': 15,
    '4776810': 15, '4776811': 14, '4776812': 14, '4776813': 14, '4776814': 14,
    '4776815': 14, '4776816': 14, '4776817': 14, '4776818': 14, '4776819': 13,
    '4776820': 13, '4776821': 13, '4776822': 13, '4776823': 13, '4776824': 13,
    '4776825': 13, '4776826': 13, '4776827': 12, '4778499': 13, '4778500': 13,
    '4778501': 13, '4778502': 12, '4778503': 12, '4778504': 12, '4778505': 13,
    '4778506': 13, '4778507': 13, '4778508': 13, '4778509': 13, '4778510': 13,
    '4778511': 13, '4778512': 13, '4778513': 13, '4778514': 13, '4778515': 13,
    '4778516': 13, '4778517': 14, '4778518': 14, '4778519': 14, '4778520': 14,
    '4778521': 15, '4778522': 15, '4778523': 14, '4778524': 14, '4778525': 14,
    '4778526': 14, '4778527': 14, '4778528': 14, '4778529': 13, '4778530': 13,
    '4778531': 13, '4778532': 13, '4778533': 13, '4778534': 13, '4778535': 13,
    '4778536': 13, '4778537': 13, '4778538': 13, '4778539': 13, '4778540': 13,
    '4778541': 13, '4778542': 13, '4778543': 12, '4778544': 12, '4778545': 12,
}

# Lookup table: trip_id -> minutes from trip start_time to arrival at stop 20280 (Route 1)
# Regenerated from GTFS effective 2026-06-22
STOP_OFFSET_RT1 = {
    '4771252': 24, '4771254': 23, '4771256': 23, '4771258': 24, '4771260': 21,
    '4771962': 24, '4771964': 23, '4771966': 23, '4771968': 24, '4771970': 22,
    '4772174': 24, '4772176': 23, '4772178': 23, '4772180': 24, '4772250': 21,
    '4772642': 10, '4772648': 10, '4772654': 10, '4772660': 10, '4772666': 10,
    '4772672': 9, '4772678': 9, '4772926': 22, '4772928': 23, '4772930': 23,
    '4772932': 24, '4772934': 24, '4773492': 10, '4773498': 10, '4773504': 10,
    '4773510': 10, '4773516': 9, '4773522': 9, '4773524': 9, '4773531': 10,
    '4773537': 10, '4773543': 10, '4773549': 10, '4773555': 9, '4773561': 9,
    '4773563': 9, '4773567': 10, '4773573': 10, '4773579': 10, '4773585': 10,
    '4773591': 9, '4773597': 9, '4777306': 9, '4777310': 9, '4777316': 9,
    '4777320': 9, '4777323': 21, '4777332': 9, '4777333': 9, '4777334': 9,
    '4777338': 21, '4777342': 21, '4777344': 21, '4777346': 21, '4777348': 22,
    '4777350': 22, '4777357': 9, '4777358': 9, '4777359': 9, '4777363': 22,
    '4777368': 22, '4777369': 9, '4777371': 21, '4777376': 21, '4778838': 8,
    '4778844': 8, '4778845': 9, '4778854': 9, '4778862': 20, '4778863': 20,
    '4778869': 9, '4778874': 20, '4778875': 20, '4778876': 20, '4778880': 20,
    '4778882': 9, '4778890': 20, '4778891': 9, '4778896': 20, '4778899': 9,
    '4778904': 20, '4778908': 9, '4778914': 20, '4778917': 8, '4778922': 20,
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
@app.route('/ping')
def ping():
    global _weather_cache
    try:
        data = requests.get(OPEN_METEO_URL, timeout=5).json()
        if not data.get('error'):
            temp_f = data['current']['temperature_2m']
            daily_code = data['daily']['weather_code'][0]
            precip_pct_later = data['daily']['precipitation_probability_max'][0]
            snow_codes = set(range(71, 78)) | {85, 86}
            has_snow = daily_code in snow_codes

            # Next 3 hours precipitation probability
            now = eastern_now()
            current_hour = now.hour
            hourly_precip = data['hourly']['precipitation_probability']
            next_3 = hourly_precip[current_hour:current_hour + 3]
            precip_pct_now = max(next_3) if next_3 else None

            _weather_cache = {
                'temp_f': temp_f,
                'precip_pct_now': precip_pct_now,
                'precip_pct_later': precip_pct_later,
                'has_snow': has_snow,
            }
            print('Weather updated: temp=%s now=%s later=%s snow=%s' % (
                temp_f, precip_pct_now, precip_pct_later, has_snow))
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
    """Subtract walk time from each result's arrival, skip if departure <= 0."""
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

    # R: up to 5, 1: up to 2
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
