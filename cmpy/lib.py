import api
from typing import Union


def match_lines_containing(matches: Union[str, list[str]], lines_to_match: list[api.Line], type='name') -> list[api.Line]:
    """Returns a list of lines whose name contains the match string or any of
    the match strings in the list.
    """
    matched_lines = []
    for line in lines_to_match:
        if type == 'id':
            matcher = [line.id]
        elif type == 'name':
            matcher = [line.name]
        else:
            raise ValueError("Invalid type. Must be 'id' or 'name'")

        try:
            for match in matches:
                if match in matcher:
                    matched_lines.append(line)
        except TypeError:  # not an iterable
            if match in matcher:
                matched_lines.append(line)

    return matched_lines

def get_lines_with_stops_containing(matches: Union[str, list[str]], lines_to_match: list[api.Line], type='name') -> list[api.Line]:
    """Returns a list of lines which have a route containing at least one stop
    whose name contains the match string.
    """
    matched_lines = []
    for line in lines_to_match:
        for route in line.routes:
            for way in route.ways:
                for stop in way.stops:
                    if type == 'id':
                        matcher = stop.id
                    elif type == 'name':
                        matcher = stop.name
                    else:
                        raise ValueError("Invalid type. Must be 'id' or 'name'")
                    try:
                        if isinstance(matches, str):
                            matches = [matches]
                        for match in matches:
                            if match in matcher:
                                matched_lines.append(line)
                    except TypeError:  # not an iterable
                        if match in matcher:
                            matched_lines.append(line)
    return matched_lines

def get_stops_containing(matches: Union[str, list[str]], stops_to_match: list[api.Stop], type='name') -> list[api.Stop]:
    """Returns a list of stops whose name contains the match string.
    """
    matched_stops = []
    for stop in stops_to_match:
        if type == 'id':
            matcher = stop.id
        elif type == 'name':
            matcher = stop.name
        else:
            raise ValueError("Invalid type. Must be 'id' or 'name'")
        try:
            if isinstance(matches, str):
                matches = [matches]
            for match in matches:
                if match in matcher:
                    matched_stops.append(stop)
        except TypeError:  # not an iterable
            if match in matcher:
                matched_stops.append(stop)
    return matched_stops

def get_stops_from_lines(lines: list[api.Line]) -> list[api.Stop]:
    """Returns a list of stops from a list of lines.
    """
    stops = []
    for line in lines:
        for route in line.routes:
            for way in route.ways:
                for stop in way.stops:
                    if stop not in stops:
                        stops.append(stop)
    return stops

def get_ways_with_origin_before_destination(origins: list[api.Stop], destinations: list[api.Stop], lines: list[api.Line]) -> list[api.Way]:
    """Returns a list of ways which have an origin stop before a destination stop.
    """
    ways = []
    for line in lines:
        for route in line.routes:
            for way in route.ways:
                for origin in origins:
                    for destination in destinations:
                        if way.in_sequence(origin, destination):
                            ways.append(way)
    return ways


def get_time_table_from_origin_to_destination(origins: list[api.Stop], destinations: list[api.Stop], lines: list[api.Line], day: str) -> list[api.StopTimes]:
    """Returns a list of times from a list of lines for a given day.
    """
    times = []
    for line in lines:
        for route in line.routes:
            for way in route.ways:
                for origin in origins:
                    for destination in destinations:
                        if way.in_sequence(origin, destination):
                            time_table = api.get_route_time_table(way._route, way, day)
                            # get times for origin
                            for stop_time in time_table:
                                if stop_time.stop == origin:
                                    times.append(stop_time)
    return times

def join_times(times1: list[api.StopTimes]) -> list[api.StopTimes]:
    """Joins a list of StopTimes objects into a single list of times.
    """
    times: list[api.StopTimes] = []
    for time in times1:
        for time_hhmm in time.times:
            times.append(api.StopTimes(time.stop, [time_hhmm]))

    times.sort(key=lambda x: int(x.times[0].split(':')[0])*60 + int(x.times[0].split(':')[1]))
    return times

if __name__ == "__main__":
    line_ids_carapinheira = [
        "2106",
        "2110",
        "2136",
        "2626",
        "2627",
        "2740",
        "2741",
        "2742",
        "2751",
        "2758",
        "2801",
        "2802",
        "2803",
        "2804",
        "2805",
        "2807",
    ]

    # get all lines
    lines = api.get_all_lines()
    
    # prior knowledge of line ids may be used to reduce the number of lines to 
    # be matched (optional)
    lines = match_lines_containing(line_ids_carapinheira, lines, type='id') 
    
    # get all unique stops from lines (shared stops are not duplicated)
    # there is usually one stop per way, which share the same name, but 
    # have different ids
    stops = get_stops_from_lines(lines)

    # get stops containing the match string
    # this may return many stops, so the user may need to further filter 
    # the results
    stops_carapinheira = get_stops_containing('R Dom João V 51', stops)
    stops_lisboa = get_stops_containing('Campo Grande', stops)

    # get ways (associated with a route) which have an origin stop before a
    # destination stop
    # this isn't used in this example, but may be useful for other purposes
    ways1 = get_ways_with_origin_before_destination(stops_carapinheira, stops_lisboa, lines)
    ways2 = get_ways_with_origin_before_destination(stops_lisboa, stops_carapinheira, lines)

    # day for which to get the time table
    # format: YYYY-MM-DD
    day = "2023-01-23"

    # get time table from origin to destination
    times_c_l = get_time_table_from_origin_to_destination(stops_carapinheira, stops_lisboa, lines, day=day)
    times_l_c = get_time_table_from_origin_to_destination(stops_lisboa, stops_carapinheira, lines, day=day)

    # unrolls the times (aggregated by stop (and way and route)) to a single list of times
    # input: [StopTimes(stop1, [time1, time2]), StopTimes(stop2, [time3, time4])]
    # output: [StopTimes(stop1, [time1]), StopTimes(stop1, [time2]), StopTimes(stop2, [time3]), StopTimes(stop2, [time4])]
    # the output is also sorted by time
    joint_times_c_l = join_times(times_c_l)
    joint_times_l_c = join_times(times_l_c)

    with open("carapinheira_lisboa.txt", "w", encoding='utf8') as f:
        f.write(f"Carapinheira -> Lisboa ({day}):\n")
        print(f"Carapinheira -> Lisboa ({day}):")
        for time in joint_times_c_l:
            f.write(f"{time.times[0]} - {time.stop._way._route}\n")
            print(f"{time.times[0]} - {time.stop._way._route}")
    
    with open("lisboa_carapinheira.txt", "w", encoding='utf8') as f:
        f.write(f"Lisboa -> Carapinheira ({day}):\n")
        print(f"Lisboa -> Carapinheira ({day}):")
        for time in joint_times_l_c:
            f.write(f"{time.times[0]} - {time.stop._way._route}\n")
            print(f"{time.times[0]} - {time.stop._way._route}")
