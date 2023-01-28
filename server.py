from flask import Flask, render_template, request, redirect, url_for, session
import cmpy



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# for css, javascript, images, etc.
@app.route('/<path:path>.<ext>')
def static_files(path, ext):
    return app.send_static_file(path + '.' + ext)

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

# sort alphabetically
sendable_stops.sort(key=lambda x: x['name'])


# list with all stops
@app.route('/stops')
def get_stops():
    return sendable_stops

if __name__ == '__main__':
    # run on port 1722 on 0.0.0.0
    app.run(host="0.0.0.0", port=1722)
