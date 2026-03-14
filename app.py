import requests
from flask import Flask, jsonify
from datetime import datetime, timezone

app = Flask(__name__)

RIPTA_URL = 'http://realtime.ripta.com:81/api/tripupdates?format=json'

# Lookup table: trip_id -> minutes from trip start_time to arrival at stop 20475
STOP_OFFSET_MINUTES = {
    '4422498': 27, '4422499': 27, '4422500': 27, '4422501': 27, '4422502': 27,
    '4422503': 28, '4422504': 29, '4422505': 29, '4422506': 29, '4422507': 30,
    '4422508': 30, '4422509': 30, '4422510': 30, '4422511': 30, '4422512': 30,
    '4422513': 32, '4422514': 32, '4422515': 32, '4422516': 33, '4422517': 33,
    '4422518': 33, '4422519': 33, '4422520': 33, '4422521': 33, '4422522': 33,
    '4422523': 33, '4422524': 33, '4422525': 33, '4422526': 33, '4422527': 33,
    '4422528': 33, '4422529': 33, '4422530': 33, '4422531': 32, '4422532': 32,
    '4422533': 32, '4422535': 31, '4422536': 31, '4422538': 30, '4422539': 30,
    '4422540': 30, '4422541': 30, '4422542': 30, '4422543': 30, '4422544': 29,
    '4422545': 28, '4422546': 27, '4563353': 26, '4563354': 26, '4563355': 26,
    '4563356': 26, '4563357': 26, '4563358': 29, '4563359': 29, '4563360': 30,
    '4563361': 31, '4563362': 31, '4563363': 32, '4563364': 33, '4563365': 33,
    '4563366': 32, '4563367': 34, '4563368': 34, '4563369': 35, '4563370': 35,
    '4563371': 35, '4563372': 35, '4563373': 37, '4563374': 37, '4563375': 37,
    '4563376': 37, '4563377': 37, '4563378': 37, '4563379': 36, '4563380': 36,
    '4563381': 36, '4563382': 36, '4563383': 36, '4563384': 36, '4563385': 37,
    '4563386': 37, '4563387': 37, '4563388': 35, '4563389': 35, '4563390': 35,
    '4563391': 35, '4563393': 35, '4563394': 34, '4563395': 35, '4563396': 35,
    '4563397': 35, '4563398': 34, '4563399': 33, '4563401': 33, '4563402': 32,
    '4563403': 30, '4563404': 30, '4571297': 28, '4571300': 36, '4571303': 34,
    '4571306': 35, '4571309': 40, '4571312': 39, '4571330': 40, '4571333': 34,
    '4571573': 31, '4571576': 34, '4571579': 35, '4571582': 38, '4571585': 41,
    '4571588': 34, '4571748': 26, '4571751': 33, '4571754': 34, '4571757': 35,
    '4571760': 38, '4571763': 40, '4571766': 33, '4571769': 31, '4571772': 28,
    '4571842': 33, '4571845': 34, '4571848': 35, '4571851': 38, '4571854': 40,
    '4571859': 31, '4571862': 30, '4571865': 26, '4571869': 29, '4571872': 35,
    '4571875': 35, '4571878': 37, '4571881': 42, '4571884': 34, '4571887': 31,
    '4571890': 29, '4571893': 26, '4571919': 41, '4571922': 39, '4571982': 28,
    '4571985': 35, '4571988': 34, '4571991': 37, '4571994': 42, '4571997': 36,
    '4572000': 31, '4572003': 29, '4572006': 26, '4572699': 28, '4572702': 36,
    '4572705': 34, '4572708': 36, '4572711': 42, '4572714': 37, '4572764': 27,
    '4572767': 34, '4572770': 34, '4572773': 35, '4572776': 39, '4572779': 39,
    '4572782': 31, '4572785': 30, '4572788': 26, '4572835': 26, '4572838': 33,
    '4572841': 34, '4572844': 35, '4572847': 38, '4572850': 40, '4572853': 31,
    '4572856': 30, '4572859': 26, '4573115': 39, '4573420': 36, '4573435': 35,
    '4573441': 28,
}


def time_str_to_minutes(t):
    parts = t.split(':')
    return int(parts[0]) * 60 + int(parts[1])


def now_minutes():
    now = datetime.now(timezone.utc).astimezone()
    return now.hour * 60 + now.minute


@app.route('/stop/20475')
def stop_20475():
    try:
        data = requests.get(RIPTA_URL, timeout=10).json()
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    current_minutes = now_minutes()
    results = []

    for entity in data.get('entity', []):
        trip_update = entity.get('trip_update')
        if not trip_update:
            continue

        trip = trip_update.get('trip', {})
        trip_id = str(trip.get('trip_id', ''))

        if trip_id not in STOP_OFFSET_MINUTES:
            continue

        start_time_str = trip.get('start_time', '')
        if not start_time_str:
            continue

        start_minutes = time_str_to_minutes(start_time_str)
        offset = STOP_OFFSET_MINUTES[trip_id]

        # Use the last stop_time_update delay as best estimate
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

        results.append({
            'destination': 'Rt 11',
            'arrival': str(minutes_away) if minutes_away > 0 else 'BRD',
        })

    results.sort(key=lambda r: int(r['arrival']) if r['arrival'] != 'BRD' else 0)

    # Return only the next 3
    return jsonify(results[:3])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
