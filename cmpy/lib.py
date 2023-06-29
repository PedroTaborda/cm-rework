from . import api
from typing import Union
import pickle
import os
from dataclasses import dataclass, asdict


def match_routes_containing(matches: Union[str, list[str]], routes_to_match: list[api.Route], type='name') -> list[api.Route]:
    """Returns a list of lines whose name contains the match string or any of
    the match strings in the list.
    """
    matched_routes = []
    for route in routes_to_match:
        if type == 'id':
            matcher = [route.id]
        elif type == 'name':
            matcher = [route.long_name]
        else:
            raise ValueError("Invalid type. Must be 'id' or 'name'")

        try:
            for match in matches:
                if match in matcher:
                    matched_routes.append(route)
                else:
                    # check if the matches are the begginings of the route name
                    for name in matcher:
                        if name.startswith(match):
                            matched_routes.append(route)
        except TypeError:  # not an iterable
            if match in matcher:
                matched_routes.append(route)

    return matched_routes

def get_routes_with_stops_containing(matches: Union[str, list[str]], routes_to_match: list[api.Route], type='name') -> list[api.Route]:
    """Returns a list of lines which have a route containing at least one stop
    whose name contains the match string.
    """
    matched_routes = []
    for route in routes_to_match:
        for stop in route.stops.values():
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
                        matched_routes.append(route)
            except TypeError:  # not an iterable
                if match in matcher:
                    matched_routes.append(route)
    return matched_routes

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

def get_stops_from_routes(routes: Union[list[api.Route], None]) -> list[api.Stop]:
    """Returns a list of stops from a list of lines.
    """
    if routes is None:
        return get_all_stops()
    stops = []
    for route in routes:
        for stop in route.stops.values():
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
        i = 0
        j = 0
        rt_i = 0
        routes = api.get_all_routes()
        rt_n = len(routes)
        for route in routes:
            rt_i += 1
            # accessing route.stops will populate the stops dicts, so doing it
            # in parallel is faster (TODO)
            for stop in route.stops.values():
                if stop not in stops:
                    stops.append(stop)
                    j += 1
                i += 1
                print(f"{i: 05d} stops processed, {j: 05d} unique stops found ({rt_i: 03d}/{rt_n: 03d} routes processed)")
        with open(cache_file, "wb") as f:
            pickle.dump(stops, f)
    return stops

def get_trips_with_origin_before_destination(origins: list[api.Stop], destinations: list[api.Stop], routes: list[api.Route]) -> list[api.Route]:
    """Returns a list of trips which have an origin stop before a destination stop.
    """
    trips = []
    for route in routes:
        for origin in origins:
            if not route.has_stop(origin):
                continue
            for destination in destinations:
                if not route.has_stop(destination):
                    continue
                # check if there is a trip where the origin stop is before the destination stop
                for trip in route.trips:
                    if trip.in_sequence(origin, destination):
                        trips.append(trip)
    return trips


def get_trips(origins: list[api.Stop], destinations: list[api.Stop], routes: list[api.Route], day: str) -> list[api.TripAB]:
    """Returns a list of tripABs from a list of lines for a given day, which
    contain an origin stop before a destination stop.
    """
    tripABs = []
    for route in routes:
        for origin in origins:
            if not route.has_stop(origin):
                continue
            for destination in destinations:
                if not route.has_stop(destination):
                    continue
                for trip in route.trips:
                    if day not in trip.dates:
                        continue
                    if trip.in_sequence(origin, destination):
                        origin_time = trip.schedule[origin.id].departure_time
                        destination_time = trip.schedule[destination.id].arrival_time
                        tripABs.append(api.TripAB(origin, destination, origin_time, destination_time, route, trip))

    tripABs.sort(key=lambda x: int(x.origin_time.split(':')[0])*60*60 + int(x.origin_time.split(':')[1])*60 + int(x.origin_time.split(':')[2]) )
    return tripABs

def get_trips_light(origins: list[api.Stop], destinations: list[api.Stop], day: str) -> list[api.TripAB]:
    tripABs = []
    i=0
    for route in api.get_all_routes_generator():
        i+=1
        print(f"Processing route {i}")
        for origin in origins:
            if not route.has_stop(origin):
                continue
            for destination in destinations:
                if not route.has_stop(destination):
                    continue
                for trip in route.trips:
                    if day not in trip.dates:
                        continue
                    if trip.in_sequence(origin, destination):
                        origin_time = trip.schedule[origin.id].departure_time
                        destination_time = trip.schedule[destination.id].arrival_time
                        tripABs.append(api.TripAB(origin, destination, origin_time, destination_time, route, trip))

    tripABs.sort(key=lambda x: int(x.origin_time.split(':')[0])*60*60 + int(x.origin_time.split(':')[1])*60 + int(x.origin_time.split(':')[2]) )
    return tripABs

db = None
def get_trips_routes_db(origins: list[api.Stop], destinations: list[api.Stop], day: str) -> list[api.TripAB]:
    """This is the most efficient implementation. The first time it is called,
    it will take a long time to build the database, but subsequent calls will be
    fast.
    The database stores all the routes, and nothing else.
    It uses the fact that routes are static and pickleable.
    """
    tripABs = []
    for route in api.get_all_routes_generator():
        for origin in origins:
            if not route.has_stop(origin):
                continue
            for destination in destinations:
                if not route.has_stop(destination):
                    continue
                for trip in route.trips:
                    if day not in trip.dates:
                        continue
                    if trip.in_sequence(origin, destination):
                        origin_time = trip.schedule[origin.id].departure_time
                        destination_time = trip.schedule[destination.id].arrival_time
                        tripABs.append(api.TripAB(origin, destination, origin_time, destination_time, route, trip))
    return tripABs

def join_times(times1: list[api.StopTimes]) -> list[api.StopTimes]:
    """Joins a list of StopTimes objects into a single list of times.
    """
    times: list[api.StopTimes] = []
    for time in times1:
        for time_hhmm in time.times:
            times.append(api.StopTimes(time.stop, [time_hhmm]))

    times.sort(key=lambda x: int(x.times[0].split(':')[0])*60 + int(x.times[0].split(':')[1]))
    return times
