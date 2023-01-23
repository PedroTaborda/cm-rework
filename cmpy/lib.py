from . import api
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
