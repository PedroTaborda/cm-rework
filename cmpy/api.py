import requests
import urllib
import os
import pickle
from dataclasses import dataclass, field

DAY_FOR_STATIC_DATA = "2023-06-06"

@dataclass
class Stop:
    id: str    # unique (number)
    name: str
    lat: float
    lon: float
    sequence: int  # order in the route
    location_identifiers: list[str] = field(init=False, default_factory=list)
    _way: "Way" = field(init=False, default=None)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Stop):
            return self.id == o.id and self.sequence == o.sequence
        return False

    def __str__(self) -> str:
        if self._way is not None:
            return f"({self.id}) {self.name} [{self.sequence} in {self._way.name}]"
        
        return f"{self.name} ({self.id})"
    
    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class StopTimes:
    stop: Stop
    times: list[str]

@dataclass
class RouteStops:
    stops: list[Stop]

@dataclass
class Way:
    id: str
    name: str
    stops: list[Stop] = field(init=False, default_factory=list)
    timetable: dict[str, StopTimes] = field(init=False, default_factory=dict)  # key is the day
    _has_stops: bool = field(init=False, default=False)
    _has_timetable: bool = field(init=False, default=False)
    _route: "Route" = field(init=False, default=None)

    def in_sequence(self, stop1: Stop, stop2: Stop) -> bool:
        """Returns True if stop1 is before stop2 in the way.
        """
        # find the stops in the way
        stop1_in_way = None
        stop2_in_way = None
        for stop in self.stops:
            if stop == stop1:
                stop1_in_way = stop
            if stop == stop2:
                stop2_in_way = stop
            if stop1_in_way is not None and stop2_in_way is not None:
                break
        if stop1_in_way is not None and stop2_in_way is not None:
            return stop1_in_way.sequence < stop2_in_way.sequence
        else:
            return False

    def set_stops(self, stops: list[Stop]):
        self.stops = stops
        self._has_stops = True
        for stop in stops:
            stop._way = self
    
    def add_timetable(self, day: str, stop_times: StopTimes):
        self.timetable[day] = stop_times
        if not self._has_timetable:
            self._has_timetable = True
    
    def populate_stops(self):
        if not self._has_stops:
            stops = get_route_stops(self._route, self, DAY_FOR_STATIC_DATA)
            self.set_stops(stops)
    
    def populate_timetable(self, route, day):
        timetable = get_route_time_table(route, self, day)
        self.add_timetable(day, timetable)
    
    def __getattribute__(self, __name: str):
        if __name == "stops":
            if not self._has_stops:
                self.populate_stops()
        return super().__getattribute__(__name)
    
    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Route:
    id: str
    name: str
    destination: str
    origin: str
    ways: list[Way] = field(init=False, default_factory=list)
    _has_ways: bool = field(init=False, default=False)
    _line: "Line" = field(init=False, default=None)

    def set_ways(self, ways: list[Way]):
        self.ways = ways
        for way in ways:
            way._route = self
        self._has_ways = True

    def populate_ways(self, day):
        if not self._has_ways:
            ways = get_route_ways(self)
            self.set_ways(ways)
    
    def __getattribute__(self, __name: str):
        if __name == "ways":
            if not self._has_ways:
                self.populate_ways()
        return super().__getattribute__(__name)

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    def __repr__(self) -> str:
        return self.__str__()
            
@dataclass
class Line:
    id: str
    name: str
    routes: list[Route] = field(init=False, default_factory=list)
    _has_routes: bool = field(init=False, default=False)

    def populate_routes(self):
        if not self._has_routes:
            self.routes = get_line_routes(self)
            self._has_routes = True
    
    def __getattribute__(self, __name: str):
        if __name == "routes":
            if not self._has_routes:
                self.populate_routes()
        return super().__getattribute__(__name)

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    def __repr__(self) -> str:
        return self.__str__()

@dataclass
class Trip:
    origin_stop: Stop
    destination_stop: Stop
    origin_time: str
    destination_time: str
    way: Way

def _cached_request(url: str, params: dict[str, str], cache_dir="cache") -> str:
    """Cache the request in a file with the same name as the url"""
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    filename = urllib.parse.urlencode(params) + ".pkl"
    filename = os.path.join(cache_dir, filename)
    try:
        with open(filename, "rb") as f:
            response = pickle.load(f)
    except FileNotFoundError:
        response = requests.request("GET", url, params=params)
        if not response.ok:
            print(f"Error {response.status_code} for {params}")
            raise requests.exceptions.ConnectionError
        with open(filename, "wb") as f:
            pickle.dump(response, f)

    return response

def _delete_cached_request(url: str, params: dict[str, str], cache_dir="cache"):
    """Delete the cached request"""
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    filename = urllib.parse.urlencode(params) + ".pkl"
    filename = os.path.join(cache_dir, filename)
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass

def get_all_lines() -> list[Line]:
    url = "https://horarios.carrismetropolitana.pt"
    querystring = {
        "action":"cmet_get_all_lines"
    }
    try:
        response = _cached_request(url, params=querystring)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []

    # example response.text:
    # '[
    # {"id":"1001","line_id":"1001","line_name":"Alfragide (Estrada do Seminario) - Reboleira (Esta\\u00e7\\u00e3o)","text":"<span class=\\"line-number\\" style=\\"background-color: rgb(250,50,80);\\">1001<\\/span> <span class=\\"line-name\\">Alfragide (Estrada do Seminario) - Reboleira (Esta\\u00e7\\u00e3o)<\\/span>"},
    # {"id":"1002","line_id":"1002","line_name":"Alfragide (Igreja) - Amadora (Esta\\u00e7\\u00e3o Norte)","text":"<span class=\\"line-number\\" style=\\"background-color: rgb(250,50,80);\\">1002<\\/span> <span class=\\"line-name\\">Alfragide (Igreja) - Amadora (Esta\\u00e7\\u00e3o Norte)<\\/span>"},
    # {"id":"1003","line_id":"1003","line_name":"Amadora (Esta\\u00e7\\u00e3o Norte) - Amadora Este (Metro)","text":"<span class=\\"line-number\\" style=\\"background-color: rgb(250,50,80);\\">1003<\\/span> <span class=\\"line-name\\">Amadora (Esta\\u00e7\\u00e3o Norte) - Amadora Este (Metro)<\\/span>"}
    # ]'

    # convert the response to a list of lines
    lines = []
    for line in response.json():
        if line['line_id'] != line['id']:
            print(f"line_id != id: {line['line_id']} != {line['id']}")
        line_id = line['id']
        line_name = line['line_name']
        lines.append(Line(line_id, line_name))
    
    return lines

def get_line_routes(line: Line) -> list[Route]:
    url = "https://horarios.carrismetropolitana.pt"
    querystring = {
        "action": "cmet_get_line_routes",
        "line_id": line.id
    }
    try:
        response = _cached_request(url, params=querystring)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []

    response_ways = response.json()['ways'] # only returns the ways for the first route
    response_routes = response.json()['routes']

    routes: list[Route] = []
    first_route = True
    for route in response_routes:
        if line.id != route['line_id']:
            print(f"line_id != id: {line.id} != {route['line_id']}")

        route_id = route['route_id']
        route_name = route['name']
        route_origin = route['origin']
        route_destination = route['destination']
        new_route = Route(route_id, route_name, route_destination, route_origin)
        new_route._line = line
        routes.append(new_route)

        if first_route:
            route_ways = []
            for way in response_ways:
                way_id = way['id']
                way_name = way['nome']
                route_ways.append(Way(way_id, way_name))
            routes[0].set_ways(route_ways)
            first_route = False
        else:
            ways = get_route_ways(routes[-1])
            routes[-1].set_ways(ways)

    return routes

def get_route_ways(route: Route) -> list[Way]:
    if route._has_ways:
        return route.ways
    
    url = "https://horarios.carrismetropolitana.pt"
    querystring = {
        "action": "cmet_get_route_ways",
        "route_id": route.id
    }
    try:
        response = _cached_request(url, params=querystring)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []

    ways = []
    for way in response.json():
        way_id = way['id']
        way_name = way['nome']
        ways.append(Way(way_id, way_name))

    return ways


def get_route_stops(route: Route, way: Way, start_date: str) -> list[Stop]:
    """Returns a list of stops for a specific way in a route.
    start_date is a string in the format "YYYY-MM-DD" and is used to get the stops for a specific day.
    """
    url = "https://horarios.carrismetropolitana.pt"
    querystring = {
        "action": "cmet_get_route_stops",
        "route_id": route.id,
        "way_id": way.id,
        "start_date": start_date
    }
    try:
        response = _cached_request(url, params=querystring)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []
    response_stops = response.json()['stops']
    response_hours = response.json()['hours']
    stops = []
    for stop in response_stops:
        stop_id = stop['stop_id']
        stop_name = stop['stop_name']
        stop_lat = stop['stop_lat']
        stop_lon = stop['stop_lon']
        stop_sequence = int(stop['stop_sequence'])
        new_stop = Stop(stop_id, stop_name, stop_lat, stop_lon, stop_sequence)
        new_stop._way = way
        if new_stop not in stops:
            stops.append(new_stop)
    return stops

def get_route_time_table(route: Route, way: Way, start_date: str) -> list[StopTimes]:
    url = "https://horarios.carrismetropolitana.pt"
    querystring = {
        "action": "cmet_get_route_timetable",
        "route_id": route.id,
        "way_id": way.id,
        "start_date": start_date
    }
    try:
        # get url-encoded string with the query parameters
        response = _cached_request(url, params=querystring)
    except requests.exceptions.ConnectionError:
        print("Error getting route time table")
        return []
    time_table_response = response.json()['timetable']

    if len(time_table_response) == 0:
        # no times for this route in this day
        return []

    if len(time_table_response) != len(way.stops):
        print(f"route: {route.name} - way: {way.name}")
        print(f"time_table_response and way.stops have different lengths ({len(time_table_response)} != {len(way.stops)})")

    time_table = [None]*max([len(time_table_response), len(way.stops)])

    # sometimes the response is a dict and sometimes it's a list
    if isinstance(time_table_response, dict):
        time_table_response = [val for val in time_table_response.values()]
    
    for stop_sequence, stop in enumerate(time_table_response):
        # stop is a dict with {stopId: {hour: [minutes] } }
        # the dict has only one stopId which is the id of the stop
        stop_id = list(stop.keys())[0]
        stop = stop[stop_id]
        times = []

        for idx, hour in enumerate(stop):
            for minute in stop[hour]:
                hour = int(hour)
                minute = int(minute)
                times.append(f"{hour:02d}:{minute:02d}")
        
        try:
            time_table[int(stop_sequence)] = StopTimes(way.stops[int(stop_sequence)], times)
        except IndexError as e:
            print(f"Tried to access stop_sequence {stop_sequence} in way.stops with length {len(way.stops)}")
            raise e
    return time_table

