from flask import Flask, render_template, request, redirect, url_for, session
import cmpy
import datetime

log_file = 'usr-log.txt'

app = Flask(__name__)

routes = cmpy.get_all_routes()
stops = cmpy.get_all_stops()
sendable_stops = []
for stop in stops:
    in_array = False
    for sendable_stop in sendable_stops:
        if sendable_stop['id'] == stop.id:
            in_array = True
            break
    if not in_array:
        sendable_stops.append({
            'id': stop.id,
            'name': stop.name,
            'lat': stop.lat,
            'lon': stop.lon,
            'location-identifiers': "",
        })

renewer = cmpy.start_cache_renewal_worker()

# sort alphabetically
sendable_stops.sort(key=lambda x: x['name'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/timetable', methods=['GET'])
def get_timetable():
    print(request.args)
    # get origin and destination
    originId = request.args.get('origin')
    destinationId = request.args.get('destination')
    # date comes in YYYY-MM-DD
    date = request.args.get('date')
    raw = request.args.get('raw')

    # print(f"origin: {originId}, destination: {destinationId}, date: {date}, raw: {raw}")
    origin = cmpy.get_stops_containing([originId], stops, type='id')[0]
    destination = cmpy.get_stops_containing(
        [destinationId], stops, type='id')[0]
    
    origins = cmpy.get_stops_containing([origin.name], stops)
    destinations = cmpy.get_stops_containing([destination.name], stops)

    # get time table from origin to destination
    trips = cmpy.get_trips(
        origins, destinations, routes, date.replace('-', ''))

    # convert to sendable format
    sendable_trips = []
    for trip in trips:
        sendable_trips.append(
            {
                't0': trip.origin_time,
                'tf': trip.destination_time,
                'lineId': trip.route.short_name,
                'route' : trip.route.long_name,
                'way': trip.trip.direction,
            }
        )

    raw_trips: dict = {
        'origin': {
            'id': origin.id,
            'name': origin.name,
            'lat': origin.lat,
            'lon': origin.lon,
            'location-identifiers': origin.location_identifiers,
        },
        'destination': {
            'id': destination.id,
            'name': destination.name,
            'lat': destination.lat,
            'lon': destination.lon,
            'location-identifiers': destination.location_identifiers,
        },
        'date': date,
        'trips': sendable_trips
    }

    if raw is not None:
        return raw_trips.__str__()
    
    return render_template('timetable.html', origin=origin, destination=destination, trips=sendable_trips, date=date)

# for css, javascript, images, etc.
@app.route('/<path:path>.<ext>')
def static_files(path, ext):
    return app.send_static_file(path + '.' + ext)

# list with all stops
@app.route('/stops', methods=['GET', 'OPTIONS'])
def get_stops():
    if request.method == 'OPTIONS':
        return ""
    return sendable_stops


@app.after_request
def log_user_ip(response: Flask.response_class):
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    datetime_seconds = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not request.args:
        request.args = ""
    with open(log_file, 'a') as f:
        f.write(
            f"{datetime_seconds} - {ip} - \"{request.method} {request.path} {request.args}\" {response.status_code}\n")
    return response

if __name__ == '__main__':
    # run on port 1722 on 0.0.0.0
    app.run(host="0.0.0.0", port=1722, debug=False)
