from . import api
from typing import Union
import pickle
import os


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

def get_stops_from_lines(lines: Union[list[api.Line], None]) -> list[api.Stop]:
    """Returns a list of stops from a list of lines.
    """
    if lines is None:
        return get_all_stops()
    stops = []
    for line in lines:
        for route in line.routes:
            for way in route.ways:
                for stop in way.stops:
                    if stop not in stops:
                        stops.append(stop)
    return stops


def get_all_stops(cache_dir="cache") -> list[api.Stop]:
    """Returns a list of all stops. Cache the result, as it is static and slow to
    retrieve.
    """
    cache_file = os.path.join(cache_dir, "stops.pkl")
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            stops = pickle.load(f)
    else:
        stops = []
        for line in api.get_all_lines():
            for route in line.routes:
                for way in route.ways:
                    for stop in way.stops:
                        if stop not in stops:
                            stops.append(stop)
        with open(cache_file, "wb") as f:
            pickle.dump(stops, f)
    return stops

def get_ways_with_origin_before_destination(origins: list[api.Stop], destinations: list[api.Stop], lines: list[api.Line]) -> list[api.Way]:
    """Returns a list of ways which have an origin stop before a destination stop.
    """
    ways = []
    for line in lines:
        for route in line.routes:
            for way in route.ways:
                for origin in origins:
                    if not way.contains_stop(origin):
                        continue
                    for destination in destinations:
                        if not way.contains_stop(destination):
                            continue
                        if way.in_sequence(origin, destination):
                            ways.append(way)
    return ways


def get_trips(origins: list[api.Stop], destinations: list[api.Stop], lines: list[api.Line], day: str) -> list[api.Trip]:
    """Returns a list of trips from a list of lines for a given day, which
    contain an origin stop before a destination stop.
    """
    trips = []
    for line in lines:
        for route in line.routes:
            for way in route.ways:
                for origin in origins:
                    if not way.contains_stop(origin):
                        continue
                    for destination in destinations:
                        if not way.contains_stop(destination):
                            continue
                        if way.in_sequence(origin, destination):
                            time_table = api.get_route_time_table(way._route, way, day)
                            origin_times = []
                            destination_times = []
                            # get times for origin and destination stops
                            for stop_time in time_table:
                                if not isinstance(stop_time, api.StopTimes):
                                    continue
                                if stop_time.stop == origin:
                                    origin_times = stop_time.times
                                if stop_time.stop == destination:
                                    destination_times = stop_time.times
                            # get trips for each origin/destination time
                            for origin_time, destination_time in zip(origin_times, destination_times):
                                trips.append(api.Trip(origin, destination, origin_time, destination_time, way))

    trips.sort(key=lambda x: int(x.origin_time.split(':')[0])*60 + int(x.origin_time.split(':')[1]))
    return trips

def join_times(times1: list[api.StopTimes]) -> list[api.StopTimes]:
    """Joins a list of StopTimes objects into a single list of times.
    """
    times: list[api.StopTimes] = []
    for time in times1:
        for time_hhmm in time.times:
            times.append(api.StopTimes(time.stop, [time_hhmm]))

    times.sort(key=lambda x: int(x.times[0].split(':')[0])*60 + int(x.times[0].split(':')[1]))
    return times
