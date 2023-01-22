import requests
import json
from cache_utils import cached
import time

auth_token = "utilizador.rest"
debug = "honey:core-sdk:*"

# get timeTable for a specific route

@cached(folder="routes")
def get_route_time_table(route_id, way_id, start_date):
    """Returns a list of dictionaries of the form
    [
        stop_id: {
            hour: [minute, minute, minute, ...],
        }
        ,
        ...
    ]
    """
    url = "https://cache.geobus.pt/admin-ajax.php"
    querystring = {
        "action":"carris_get_route_timetable2",
        "route_id":route_id,
        "way_id":way_id,
        "start_date":start_date
    }
    try:
        response = requests.request("GET", url, params=querystring, headers={'Authorization': auth_token})
    except requests.exceptions.ConnectionError:
        print("Error getting route time table")
        return []
    if not response.ok:
        if "Please slow down." in response.text:
            time.sleep(1)
            return get_route_time_table(route_id, way_id, start_date)
        print("Error getting route time table")
        return []
    time_table = response.json()['timetable']
    # if time_table is a dictionary, its keys will be integers, so just return a list with the values
    if isinstance(time_table, dict):
        return list(time_table.values())
    return time_table

@cached(folder="ways")
def get_route_ways(route_id):
    """Gets each way of a route in a list of dictionaries.
    [
        {
            id: name,
        }
    ]
    """
    url = "https://cache.geobus.pt/admin-ajax.php"
    querystring = {
        "action": "carris_get_route_ways",
        "route_id":route_id
    }
    try:
        response = requests.request("GET", url, params=querystring, headers={'Authorization': auth_token})
    except requests.exceptions.ConnectionError:
        print("Error getting route ways")
        return []
    ways = []
    if not response.ok:
        if "Please slow down." in response.text:
            time.sleep(1)
            return get_route_ways(route_id)
        print("Error getting route ways")
        return []
    for way in response.json():
        way_id = way['id']
        way_name = way['nome']
        ways.append({
            way_id: way_name
        })
    return ways

@cached(folder="stop-names")
def get_stop_name_by_id(stop_id):
    url = "https://cache.geobus.pt/admin-ajax.php"
    querystring = {
        "action":"carris_get_stop_name_by_id",
        "stop_id":stop_id
    }
    try:
        response = requests.request("GET", url, params=querystring, headers={'Authorization': auth_token})
    except requests.exceptions.ConnectionError:
        print("Error getting stop name")
        return None
    return response.text

@cached(folder="lines")
def get_all_lines():
    """Returns a list of all routes.
    Each route is a dictionary. Its the key is the route id and the value is the route name.
    {
        id: name,
    }
    """
    url = "https://cache.geobus.pt/admin-ajax.php"
    querystring = {
        "action":"carris_get_all_lines"
    }
    try:
        response = requests.request("GET", url, params=querystring, headers={
                                'Authorization': auth_token})
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []
    # save the response in a json file
    with open('linhas.json', 'w') as outfile:
        json.dump(response.json(), outfile)

    # example of element in the list
    #     {
    #    "id": "1007",
    #    "text": "<span class=\"line-number\" style=\"background-color: rgb(237,25,68);\">1007</span> <span class=\"line-name\">Amadora (Esta\u00e7\u00e3o Norte) | Circular madrugada</span>"
    #}
    # extract only the line number and name
    lines = []
    for line in response.json():
        line_id = line['id']
        line_name = line['text'].split('<span class="line-name">')[1].split('</span>')[0]
        lines.append({
            line_id: line_name
        })
    return lines

@cached(folder="line-routes")
def get_line_routes(line_id):
    """Returns a list of routes for a specific line, and its ways
    Each route is a dictionary. Its the key is the route id and the value is the route name.
    {
        id: {
            name: name,
            ways: ways (list of dictionaries {way_id: way_name})
            description: description (dict)
        }
    }
    """
    url = "https://cache.geobus.pt/admin-ajax.php"
    querystring = {
        "action": "carris_get_line_routes2",
        "line_id":line_id
    }
    try:
        response = requests.request("GET", url, params=querystring, headers={
                                'Authorization': auth_token})
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []

    response_ways = response.json()['ways']
    response_routes = response.json()['routes']

    routes = []
    for route in response_routes:
        route_id = route['route_id']
        route_name = route['name']
        route_description = route
        route_ways = []
        for way in response_ways:
            if way['id'].startswith(route_id):
                route_ways.append({
                    way['id']: way['nome']
                })
        routes.append({
            route_id: {
                'name': route_name,
                'ways': route_ways,
                'description': route_description
            }
        })

    return routes

@cached(folder="route-stops")
def get_route_stops(route_id, way_id, start_date, time_chosen):
    """Returns a list of stops for a specific route and way
    Each stop is a dictionary. Its the key is the stop id and the value is the stop name.
    {
        id: name,
    }
    """
    url = "https://cache.geobus.pt/admin-ajax.php"
    querystring = {
        "action": "carris_get_route_stops",
        "route_id":route_id,
        "way_id":way_id,
        "start_date": start_date,
        "time_choosen": time_chosen
    }
    try:
        response = requests.request("GET", url, params=querystring, headers={
                                'Authorization': auth_token})
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []
    stops = []
    if not response.ok:
        print(response.text)
        print(f"'{response.text}' at {route_id} {way_id} {start_date} {time_chosen}")
        if "Please slow down." in response.text:
            time.sleep(1)
            return get_route_stops(route_id, way_id, start_date, time_chosen)
        return stops
    for stop in response.json()['stops']:
        stop_id = stop['stop_id']
        stops.append({
            stop_id: stop
        })
    return stops


def match_lines_containing(match, lines_to_match, type='name'):
    """Returns a list of routes whose name contains the match string.
    """
    matched_lines = []
    for line in lines_to_match:
        for line_id, line_name in line.items():
            if type == 'id':
                if match in line_id:
                    matched_lines.append(line)
            elif type == 'name':
                if match in line_name:
                    matched_lines.append(line)
            else:
                raise ValueError("Invalid type. Must be 'id' or 'name")

    return matched_lines

def get_lines_with_stop(stop_id_search, lines):
    """Returns a list of routes that have a stop with the given id.
    """
    lines_with_stop = []
    error_lines = []
    for line in lines:
        line_id, line_name = list(line.items())[0]
        routes = get_line_routes(line)
        for route in routes:
            for route_id, route_info in route.items():
                if line in error_lines: # debug stuff
                    continue

                if "Circular" in line_name:
                    continue

                if not route_info['ways']:
                    ways = get_route_ways(route_id)
                    if not ways:
                        print("Error retrieving ways on route: " + route_id + " - " + route_info['name'])
                        error_lines.append(line)
                        if line_id.startswith('280'):
                            print(line_name)
                            print(f"[ways fail] route_id: {route_id}")
                        continue
                    way = ways[0]
                    
                else:
                    way = routes[0][list(route.keys())[0]]['ways'][0]

                way_id = list(way.keys())[0]

                time_table = get_route_time_table(route_id, way_id, start_date)

                if not time_table:
                    print("Error retrieving time table on route: " + route_id + " - " + route_info['name'])
                    error_lines.append(line)
                    if line_id.startswith('274') or line_id.startswith('280'):
                        print(line_name)
                        print(f"[time-table fail] route_id, way_id, start_date: {route_id}, {way_id}, {start_date}")
                    continue

                idx_find = 0
                if line_id.startswith('280') or line_id.startswith('274'):
                    idx_find = 1
                
                stop_id = list(time_table[idx_find].keys())[0]
                possible_times = time_table[idx_find][stop_id]
                # a key from possible_times
                hour_chosen = list(possible_times.keys())[0]
                minute_chosen = possible_times[hour_chosen][0]
                time_chosen = f"{int(hour_chosen):02}:{int(minute_chosen):02}"

                stops = get_route_stops(route_id, way_id, start_date, time_chosen)

                if not stops:
                    print("Error retrieving stops on route: " + route_id + " - " + route_info['name'])
                    error_lines.append(line)
                    if line_id.startswith('274') or line_id.startswith('280'):
                        print(line_name)
                        print(f"[stops fail] route_id, way_id, start_date, time_chosen: {route_id}, {way_id}, {start_date}, {time_chosen}")
                    continue

                for stop in stops:
                    for stop_id, stop_info in stop.items():
                        if stop_id == stop_id_search:
                            lines_with_stop.append(line)
                            print(len(lines_with_stop))
    return lines_with_stop, error_lines

def find_way_where_origin_before_destination(route, origin_stop_id, dest_stop_id):
    for route_id, route_info in route.items():
        ways = route_info['ways']

        if not ways:
                ways = get_route_ways(route_id)
                if not ways:
                    print("Error retrieving ways on route: " +
                        route_id + " - " + route_info['name'])
                    continue

        print(f"ways: {ways}")
        for way in ways:
            print(f"way: {way}")
            way_id = list(way.keys())[0]
            time_table = get_route_time_table(
                route_id, way_id, start_date)
            gotoNextWay = False
            origin_found = False
            dest_found = False
            for stopAndTime in time_table:
                for stop_id, possible_times in stopAndTime.items():
                    if stop_id == origin_stop_id:
                        origin_found = True
                    elif stop_id == dest_stop_id:
                        dest_found = True
                        if origin_found:
                            return way
                        else:
                            gotoNextWay = True
                            break
                if gotoNextWay:
                    break
    return None

def convert_time_table_to_list(time_table):
    """Returns a list of times from the time table.
    """
    times = []
    for stopAndTime in time_table:
        for stop_id, possible_times in stopAndTime.items():
            for hour, minutes in possible_times.items():
                for minute in minutes:
                    times.append((f"{int(hour):02}:{int(minute):02}"))
    return times

def print_time_table_stops(time_table):
    for stopAndTime in time_table:
        for stop_id, possible_times in stopAndTime.items():
            print(stop_id)
    


def get_time_table_from_origin_to_dest(stop_id_origin, stop_id_dest, lines_with_origin_and_dest):
    """Returns a list of trips that go from the origin to the destination.

    """
    # for each route, the way which has the origin before the destination is chosen.

    trip = []

    for line in lines_with_origin_and_dest:    
        routes = get_line_routes(line)
        line_id, line_name = list(line.items())[0]
        for route in routes:
            correctWay = find_way_where_origin_before_destination(route, stop_id_origin, stop_id_dest)
            if not correctWay:
                print("Didn't find a way where the origin is before the destination, on line " + line_name)
                continue
            correctWayID, correctWayName = list(correctWay.items())[0]
            time_table = get_route_time_table(route, correctWayID, start_date)


            route_id = list(route.keys())[0]
            route_info = route[route_id]
            if not time_table:
                print("Error retrieving time table on route: " + route_id + " - " + route_info['name'])
                continue

            origin_possible_times = None
            dest_possible_times = None
            for stop in time_table:
                for stop_id, possible_times in stop.items():
                    if stop_id == stop_id_origin:
                        origin_possible_times = possible_times
                    elif stop_id == stop_id_dest:
                        dest_possible_times = possible_times                
            
            if not origin_possible_times or not dest_possible_times:
                continue
            times_origin = []
            times_dest = []
            # for each of the possible times, put them in a list
            for hour_origin, minutes_origin in origin_possible_times.items():
                for minute_origin in minutes_origin:
                    times_origin.append(f"{int(hour_origin):02}:{int(minute_origin):02}")
            for hour_dest, minutes_dest in dest_possible_times.items():
                for minute_dest in minutes_dest:
                    times_dest.append(f"{int(hour_dest):02}:{int(minute_dest):02}")
            
            for time_origin, time_dest in zip(times_origin, times_dest):

                if '2804_0_1' == correctWayID:
                    print("found")
                trip.append((time_origin, time_dest, correctWayID, correctWayName))
            
    return trip

start_date = "2023-01-05"

lines = get_all_lines()

# routes = get_line_routes(lines[0])
# routes = get_line_routes(match_lines_containing('via A21', lines)[0])

# way_example = routes[0][list(routes[0].keys())[0]]['ways'][0]
# way_id = list(way_example.keys())[0]

# time_table = get_route_time_table(routes[0], way_id, start_date)

# stop_id = list(time_table[0].keys())[0]
# possible_times = time_table[0][stop_id]

# # a key from possible_times
# hour_chosen = list(possible_times.keys())[0]
# minute_chosen = possible_times[hour_chosen][0]

# time_chosen = f"{int(hour_chosen):02}:{int(minute_chosen):02}"

# stops = get_route_stops(routes[0], way_id, start_date, time_chosen)

origin_stops = ["061200", "060337"]
final_stops = ["080345", "080346"]

lines_match_1 = match_lines_containing("280", lines, type="id")
lines_match_2 = match_lines_containing("274", lines, type="id")

lines_to_search = lines_match_1 + lines_match_2

lines_with_origin = []
lines_with_origin_and_destination = []

total_trips = []
for origin_stop in origin_stops:
    for final_stop in final_stops:
        lines_with_origin, error_lines = get_lines_with_stop(origin_stop, lines_to_search)
        lines_with_origin_and_destination, error_lines2 = get_lines_with_stop(final_stop, lines_with_origin)

        trips = get_time_table_from_origin_to_dest(final_stop, origin_stop, lines_with_origin_and_destination)
        total_trips = total_trips + trips


# sort by time of origin
total_trips.sort(key=lambda x: x[0])

# remove duplicates
total_trips = list(dict.fromkeys(total_trips)) 

# save to txt file
with open('trips.txt', 'w') as f:
    for trip in total_trips:
        trip_str = ' - '.join(trip)
        f.write(f"{trip_str}\n")

