from typing import Generator, Union
import requests
import urllib
import os
import pickle
import datetime
from dataclasses import dataclass, field
import msgspec
import multiprocessing
import itertools
import sys
import sqlite3

json_decoder = msgspec.json.Decoder()

DAYS_FOR_STATIC_DATA = ["2023-06-06", "2023-01-31"]
routes_database_file = os.path.join("cache", "routes.db")
db = None

@dataclass
class Stop:
    id: str    # unique (number)
    name: str
    lat: float
    lon: float
    location_identifiers: list[str] = field(init=False, default_factory=list)
    _route: "Route" = field(init=False, default=None)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Stop):
            return self.id == o.id
        return False

    def __str__(self) -> str:
        if self._route is not None:
            return f"({self.id}) {self.name} [in {self._route.long_name}]"
        
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
class Route:
    id: str
    short_name: str
    long_name: str
    color: str
    text_color: str
    _has_stops_and_trips: bool = field(init=False, default=False)
    stops: dict[str, Stop] = field(init=False, default_factory=dict)
    trips: list["Trip"] = field(init=False, default_factory=list)

    def __post_init__(self):
        self._has_stops_and_trips = True
        self.trips = get_route_stops_and_trips(self)

    def has_stop(self, stop: Union[Stop, str]) -> bool:
        if isinstance(stop, Stop):
            stop = stop.id
        return stop in self.stops
    
    def get_stop(self, stop_id) -> Stop:
        return self.stops[stop_id]
    
    def add_stop(self, stop: Stop) -> None:
        self.stops[stop.id] = stop

    def __str__(self) -> str:
        return f"{self.long_name} ({self.id})"

    def __repr__(self) -> str:
        return self.__str__()

    def _sz(self) -> int:
        size = 0
        for trip in self.trips:
            size += sys.getsizeof(trip)
            for sched in trip.schedule.values():
                size += sys.getsizeof(sched)
        for stop in self.stops.values():
            size += sys.getsizeof(stop)
        return size + sys.getsizeof(self) + sys.getsizeof(self.stops) + sys.getsizeof(self.trips)

@dataclass
class TripAB:
    origin_stop: Stop
    destination_stop: Stop
    origin_time: str
    destination_time: str
    route: Route
    trip: "Trip"

@dataclass
class TimedStop:
    stop_id: str
    stop_name: str
    stop_sequence: int
    arrival_time: str
    departure_time: str
@dataclass
class Trip:
    trip_id: str
    service_id: str
    schedule: dict[str, TimedStop] # for O(1) stop lookup
    dates: list[str]
    direction: str

    def in_sequence(self, stopA: Union[Stop, str], stopB: Union[Stop, str]):
        """Returns true if stopA is before stopB in the trip"""
        if isinstance(stopA, Stop):
            stopA = stopA.id
        if isinstance(stopB, Stop):
            stopB = stopB.id
        if stopA not in self.schedule or stopB not in self.schedule:
            return False
        return self.schedule[stopA].stop_sequence < self.schedule[stopB].stop_sequence
        


def __cached_request(url: str, key: str, cache_dir="cache", overwrite=False) -> str:
    """Cache the request in a file with the same name as the url"""
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    filename = key + ".pkl"
    filename = os.path.join(cache_dir, filename)
    try:
        if overwrite:
            # delete file first, to ensure it's not corrupted
            os.remove(filename)
            raise FileNotFoundError
        with open(filename, "rb") as f:
            response = pickle.load(f)
    except FileNotFoundError:
        response = requests.request("GET", url)
        if not response.ok:
            print(f"Error {response.status_code} for {url}")
            raise requests.exceptions.ConnectionError
        with open(filename, "wb") as f:
            pickle.dump(response, f)

    return response

cache_dict = {}
def _cached_request(url: str, key: str, cache_dir: os.PathLike="cache", overwrite=False) -> str:
    """Uses __cached_request, but places the response in a more accessible dict
    """
    # not right now
    return __cached_request(url, key, cache_dir, overwrite)
    # if not os.path.isdir(cache_dir):
    #     os.mkdir(cache_dir)
    # filename = urllib.parse.urlencode(params) + ".pkl"
    # filename = os.path.join(cache_dir, filename)
    # if filename not in cache_dict:
    #     cache_dict[filename] = __cached_request(url, params, cache_dir)
    # return cache_dict[filename]

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

def _delete_older_than(days: int, cache_dir="cache"):
    """Delete all cached requests older than days"""
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    for filename in os.listdir(cache_dir):
        if filename.endswith(".pkl"):
            filepath = os.path.join(cache_dir, filename)
            file_age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(filepath))).days
            if file_age > days:
                os.remove(filepath)

def get_all_routes() -> list[Route]:
    summary_url = "https://schedules.carrismetropolitana.pt/api/routes/summary"
    try:
        response = _cached_request(summary_url, "routes_summary", overwrite=False)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []

    # example response.text:
    # '[
    # {
    #     "_id": "6474e02e155a72200ee0dcf1",
    #     "route_id": "4902_0",
    #     "__v": 0,
    #     "createdAt": "2023-05-29T17:26:06.621Z",
    #     "municipalities": [
    #         {
    #             "id": "10",
    #             "value": "Montijo",
    #             "_id": "649aa998fc1045004438bdc0"
    #         },
    #         {
    #             "id": "13",
    #             "value": "Palmela",
    #             "_id": "649aa998fc1045004438bdc1"
    #         },
    #         {
    #             "id": "19",
    #             "value": "CIM Alentejo Central",
    #             "_id": "649aa998fc1045004438bdc2"
    #         }
    #     ],
    #     "route_color": "#ED1944",
    #     "route_long_name": "Landeira - Pegões",
    #     "route_short_name": "4902",
    #     "route_text_color": "#FFFFFF",
    #     "updatedAt": "2023-06-27T09:19:22.084Z"
    # },
    # {
    #     "_id": "6474e02e155a72200ee0da75",
    #     "route_id": "4905_0",
    #     "__v": 0,
    #     "createdAt": "2023-05-29T17:26:06.251Z",
    #     "municipalities": [
    #         {
    #             "id": "10",
    #             "value": "Montijo",
    #             "_id": "649aa997fc1045004438a68b"
    #         },
    #         {
    #             "id": "13",
    #             "value": "Palmela",
    #             "_id": "649aa997fc1045004438a68c"
    #         },
    #         {
    #             "id": "19",
    #             "value": "CIM Alentejo Central",
    #             "_id": "649aa997fc1045004438a68d"
    #         }
    #     ],
    #     "route_color": "#BB3E96",
    #     "route_long_name": "Faias - Vendas Novas",
    #     "route_short_name": "4905",
    #     "route_text_color": "#FFFFFF",
    #     "updatedAt": "2023-06-27T09:19:22.199Z"
    # },
    # ]'

    # convert the response to a list of routes
    routes = []
    # use msgspec to decode the json
    for route in json_decoder.decode(response.text):
        route_id = route['route_id']
        route_short_name = route['route_short_name']
        route_long_name = route['route_long_name']
        route_color = route['route_color']
        route_text_color = route['route_text_color']
        routes.append(Route(route_id, route_short_name, route_long_name, route_color, route_text_color))
    
    return routes

def _process_chunk(chunk: list[dict]) -> list[Route]:
    routes = []
    for route in chunk:
        route_id = route['route_id']
        route_short_name = route['route_short_name']
        route_long_name = route['route_long_name']
        route_color = route['route_color']
        route_text_color = route['route_text_color']
        routes.append(Route(route_id, route_short_name, route_long_name, route_color, route_text_color))
    return routes

def get_all_routes_pool(chunksize: int=10, n_workers: int=4) -> list[Route]:
    # in order for the JSON decoder to release all the memory used to the OS, it's
    # necessary to run this in a subprocess
    # not doing so will cause the memory to be kept by the parent process
    # to prevent doing it all at once, we split the work into chunks of chunksize
    # and run each chunk in a subprocess
    # we process the chunks in parallel using n_workers processes
    summary_url = "https://schedules.carrismetropolitana.pt/api/routes/summary"
    try:
        response = _cached_request(summary_url, "routes_summary", overwrite=False)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []

    summary_json = response.json()

    chunks = [summary_json[i:i + chunksize] for i in range(0, len(summary_json), chunksize)]

    with multiprocessing.Pool(n_workers) as pool:
        routes = pool.map(_process_chunk, chunks)
        
    return list(itertools.chain.from_iterable(routes))


def _process_and_queue_chunk(chunk: list[dict], queue: multiprocessing.Queue) -> None:
    routes = _process_chunk(chunk)
    queue.put(routes)
    # terminate the process
    # import sys
    # sys.exit(0)
    

def get_all_routes_ephemeral_processes(chunksize: int=10, workers: int=4) -> list[Route]:
    # same as get_all_routes_pool, but using new processes for each chunk, ensuring
    # that the memory is released to the OS
    summary_url = "https://schedules.carrismetropolitana.pt/api/routes/summary"
    try:
        response = _cached_request(summary_url, "routes_summary", overwrite=False)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []

    summary_json = response.json()

    chunks = [summary_json[i:i + chunksize] for i in range(0, len(summary_json), chunksize)]
    queue = multiprocessing.Queue()

    routes = []
    N = len(chunks)
    i = 0
    for j in range(0, N, workers):
        i += workers
        print(f"Processing chunks {i}/{N}", flush=True)
        n_chunks = min(workers, N - j)
        batch = chunks[j:j + n_chunks]
        # flush
        p: list[multiprocessing.Process] = []
        for chunk in batch:
            process = multiprocessing.Process(target=_process_and_queue_chunk, args=(chunk, queue))
            p.append(process)
        for process in p:
            process.start()
        for process in p:
            routes.extend(queue.get())
        for process in p:
            process.join()


    return routes

def get_route_stops_and_trips(route: Route) -> list[Trip]:
    url = f"https://schedules.carrismetropolitana.pt/api/routes/route_short_name/{route.short_name}"
    try:
        response = _cached_request(url, route.short_name)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return []
    
    # example response.text:
    # '[
    # {
    # "trip_id":"p0_1002_0_1_0730_0759_0_7",
    # "service_id":"p0_7",
    # "dates":
    # [
    #    "20230703","20230704","20230705","20230706","20230707","20230710","20230711","20230712","20230713","20230714","20230717","20230718","20230719","20230720","20230721","20230724","20230725","20230726","20230727","20230728","20230731","20230801","20230802","20230803","20230804","20230807","20230808","20230809","20230810","20230811","20230814","20230815","20230816","20230817","20230818","20230821","20230822","20230823","20230824","20230825","20230828","20230829","20230830","20230831"
    # ],
    # "schedule":
    # [
    #   {
    #       "stop_sequence":"1",
    #       "stop_id":"030064",
    #       "stop_name":"Alfragide (Força Aérea)",
    #       "stop_lon":"-9.218330",
    #       "stop_lat":"38.740175",
    #       "arrival_time":"07:46:00",
    #       "arrival_time_operation":"07:46:00",
    #       "departure_time":"07:46:00",
    #       "departure_time_operation":"07:46:00",
    #       "_id":"649aa720fc10450044c498d1"
    #   },
    #   {
    #       "stop_sequence":"2",
    #       "stop_id":"030752",
    #       "stop_name":"Av F Aerea Portuguesa (Força Aerea)",
    #       "stop_lon":"-9.215718",
    #       "stop_lat":"38.739757",
    #       "arrival_time":"07:46:00",
    #       "arrival_time_operation":"07:46:00",
    #       "departure_time":"07:46:00",
    #       "departure_time_operation":"07:46:00",
    #       "_id":"649aa720fc10450044c498d2"
    #   },
    #   {
    #       "stop_sequence":"3",
    #       "stop_id":"030063",
    #       "stop_name":"Av Força Aérea Port (Passagem Peões)",
    # ...
    trips = []
    for direction in json_decoder.decode(response.text)[0]['directions']:
        for trip in direction['trips']:
            trip_id = trip['trip_id']
            service_id = trip['service_id']
            dates = trip['dates']
            direction_str = direction['headsign']
            schedule = {}
            for stop in trip['schedule']:
                if not route.has_stop(stop['stop_id']):
                    route.add_stop(Stop(stop['stop_id'], stop['stop_name'], stop['stop_lat'], stop['stop_lon']))
                stop_id = stop['stop_id']
                stop_name = stop['stop_name']
                stop_sequence = stop['stop_sequence']
                arrival_time = stop['arrival_time']
                departure_time = stop['departure_time']
                timedStop = TimedStop(stop_id, stop_name, stop_sequence, arrival_time, departure_time)
                schedule[stop_id] = timedStop
            trips.append(Trip(trip_id, service_id, schedule, dates, direction_str))

    return trips

def get_all_routes_naive_generator() -> Generator[Route, None, None]:
    summary_url = "https://schedules.carrismetropolitana.pt/api/routes/summary"
    try:
        response = _cached_request(summary_url, "routes_summary", overwrite=False)
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return

    for route in json_decoder.decode(response.text):
        route_id = route['route_id']
        route_short_name = route['route_short_name']
        route_long_name = route['route_long_name']
        route_color = route['route_color']
        route_text_color = route['route_text_color']
        yield Route(route_id, route_short_name, route_long_name, route_color, route_text_color)

def build_route_db():    
    global db
    if db is None:
        # check if the database exists
        if os.path.exists(routes_database_file):
            db = sqlite3.connect(routes_database_file)
            print("Found existing database")
        else:
            # build the database
            print("Building database")
            i = 0
            db = sqlite3.connect(routes_database_file)
            db.execute("CREATE TABLE routes (id TEXT PRIMARY KEY, route BLOB)")
            db.commit()
            for route in get_all_routes_naive_generator():
                i += 1
                print(f"Processing route {i}", end="\r")
                idx = route.id
                val = pickle.dumps(route)
                db.execute("INSERT INTO routes (id, route) VALUES (?, ?)", (idx, val))
            db.commit()
            print("\nBuilt database")

def get_route(route_id: str) -> Route:
    global db
    if db is None:
        build_route_db()
    cursor = db.execute("SELECT route FROM routes WHERE id = ?", (route_id,))
    route = cursor.fetchone()
    if route is None:
        return None
    else:
        return pickle.loads(route[0])

def get_all_routes_generator() -> Generator[Route, None, None]:
    global db
    if db is None:
        build_route_db()
    cursor = db.execute("SELECT route FROM routes")
    # get 10 routes at a time, for memory efficiency
    while True:
        routes = cursor.fetchmany(1)
        if len(routes) == 0:
            break
        for route in routes:
            yield pickle.loads(route[0])

def start_cache_renewal_worker(period_seconds: int=120):
    import threading
    import time
    def worker():
        summary_url = "https://schedules.carrismetropolitana.pt/api/routes/summary"
        try:
            response = _cached_request(summary_url, "routes_summary", overwrite=False)
        except requests.exceptions.ConnectionError:
            print("Connection error")
            return []
        route_short_names = []
        for route in json_decoder.decode(response.text):
            route_short_name = route['route_short_name']
            route_short_names.append(route_short_name)
        
        i = 0
        while True:
            route_short_name = route_short_names[i%len(route_short_names)]
            url = f"https://schedules.carrismetropolitana.pt/api/routes/route_short_name/{route_short_name}"
            try:
                response = _cached_request(url, route_short_name, overwrite=True)
            except requests.exceptions.ConnectionError:
                print(f"Connection error for route {route_short_name}")
            if i % 1000 == 0:
                try:
                    response = _cached_request(summary_url, "routes_summary", overwrite=True)
                except requests.exceptions.ConnectionError:
                    print("Connection error for summary")
            i += 1
            # update the database
            db = sqlite3.connect("routes.db")
            db.execute("UPDATE routes SET route = ? WHERE id = ?", (response.content, route_short_name))
            db.commit()
            time.sleep(period_seconds)

    renewer = threading.Thread(target=worker, daemon=True)
    renewer.start()

    return renewer
