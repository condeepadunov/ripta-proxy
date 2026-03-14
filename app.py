import requests
from flask import Flask, jsonify
from datetime import datetime, timezone

app = Flask(__name__)

RIPTA_URL = 'http://realtime.ripta.com:81/api/tripupdates?format=json'

# Lookup table: trip_id -> minutes from trip start_time to arrival at stop 20535
STOP_OFFSET_MINUTES = {
    '4422603': 13, '4422604': 13, '4422605': 13, '4422606': 12, '4422607': 12,
    '4422608': 12, '4422609': 13, '4422610': 13, '4422611': 13, '4422612': 13,
    '4422613': 13, '4422614': 13, '4422615': 13, '4422616': 13, '4422617': 13,
    '4422618': 13, '4422619': 13, '4422620': 13, '4422621': 14, '4422622': 14,
    '4422623': 14, '4422624': 14, '4422625': 15, '4422626': 15, '4422627': 14,
    '4422628': 14, '4422629': 14, '4422630': 14, '4422631': 14, '4422632': 14,
    '4422633': 13, '4422634': 13, '4422635': 13, '4422636': 13, '4422637': 13,
    '4422638': 13, '4422639': 13, '4422640': 13, '4422641': 13, '4422642': 13,
    '4422643': 13, '4422644': 13, '4422645': 13, '4422646': 13, '4422647': 12,
    '4422648': 12, '4422649': 12, '4563407': 11, '4563461': 12, '4563462': 12,
    '4563463': 13, '4563464': 13, '4563465': 13, '4563466': 13, '4563467': 13,
    '4563468': 13, '4563469': 13, '4563470': 13, '4563471': 13, '4563472': 15,
    '4563473': 15, '4563474': 15, '4563475': 15, '4563476': 15, '4563477': 15,
    '4563478': 15, '4563479': 15, '4563480': 15, '4563481': 15, '4563482': 15,
    '4563483': 15, '4563484': 15, '4563485': 15, '4563486': 15, '4563487': 15,
    '4563488': 15, '4563489': 15, '4563490': 15, '4563491': 15, '4563492': 15,
    '4563493': 14, '4563494': 14, '4563495': 14, '4563496': 14, '4563497': 14,
    '4563498': 14, '4563499': 14, '4563500': 14, '4563501': 13, '4563502': 13,
    '4563503': 13, '4563504': 13, '4563505': 13, '4563506': 13, '4563507': 13,
    '4563508': 13, '4563509': 12, '4571299': 14, '4571302': 15, '4571305': 14,
    '4571308': 14, '4571311': 16, '4571314': 14, '4571329': 14, '4571332': 15,
    '4571383': 21, '4571385': 24, '4571572': 12, '4571575': 14, '4571578': 14,
    '4571581': 14, '4571584': 14, '4571587': 15, '4571692': 24, '4571694': 24,
    '4571696': 24, '4571698': 28, '4571700': 27, '4571702': 23, '4571750': 13,
    '4571753': 14, '4571756': 14, '4571759': 14, '4571762': 16, '4571765': 15,
    '4571768': 13, '4571771': 13, '4571774': 12, '4571841': 13, '4571844': 14,
    '4571847': 14, '4571850': 14, '4571853': 15, '4571856': 15, '4571861': 13,
    '4571864': 13, '4571868': 12, '4571871': 14, '4571874': 15, '4571877': 14,
    '4571880': 14, '4571883': 16, '4571886': 13, '4571889': 13, '4571892': 12,
    '4571921': 16, '4571981': 12, '4571984': 14, '4571987': 15, '4571990': 14,
    '4571993': 14, '4571996': 16, '4571999': 13, '4572002': 13, '4572005': 13,
    '4572698': 12, '4572701': 14, '4572704': 15, '4572707': 14, '4572710': 14,
    '4572713': 16, '4572766': 13, '4572769': 14, '4572772': 14, '4572775': 14,
    '4572778': 16, '4572781': 14, '4572784': 13, '4572787': 13, '4572790': 12,
    '4572837': 13, '4572840': 14, '4572843': 14, '4572846': 14, '4572849': 16,
    '4572852': 15, '4572855': 13, '4572858': 13, '4572861': 12, '4573114': 16,
    '4573117': 15, '4573431': 14, '4573434': 13, '4573604': 23, '4573606': 24,
    '4573608': 24, '4574102': 24, '4574104': 25, '4574106': 27, '4574108': 27,
    '4574110': 21,
}


def time_str_to_minutes(t):
    parts = t.split(':')
    return int(parts[0]) * 60 + int(parts[1])


def now_minutes():
    now = datetime.now(timezone.utc).astimezone()
    return now.hour * 60 + now.minute


@app.route('/debug')
def debug():
    try:
        data = requests.get(RIPTA_URL, timeout=10).json()
    except Exception as e:
        return jsonify({'error': str(e)}), 502

    current_minutes = now_minutes()
    route_11_trips = []

    for entity in data.get('entity', []):
        trip_update = entity.get('trip_update')
        if not trip_update:
            continue
        trip = trip_update.get('trip', {})
        if str(trip.get('route_id', '')) != '11':
            continue
        trip_id = str(trip.get('trip_id', ''))
        route_11_trips.append({
            'trip_id': trip_id,
            'start_time': trip.get('start_time'),
            'in_lookup': trip_id in STOP_OFFSET_MINUTES,
        })

    return jsonify({
        'current_minutes_since_midnight': current_minutes,
        'route_11_trips_in_feed': route_11_trips,
    })


@app.route('/stop/20535')
def stop_20535():
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
    return jsonify(results[:3])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
