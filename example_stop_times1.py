import cmpy
import tracemalloc



if __name__ == "__main__":
    # tracemalloc.start()
    route_ids_carapinheira = [
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
    routes = cmpy.get_all_routes()

    
    # snapshot1 = tracemalloc.take_snapshot()

    # prior knowledge of line ids may be used to reduce the number of lines to
    # be matched (optional)
    #routes = cmpy.match_routes_containing(
    #    route_ids_carapinheira, routes, type='id')

    # get all unique stops from lines (shared stops are not duplicated)
    # there is usually one stop per way, which share the same name, but
    # have different ids
    # if provided with None, all stops are returned
    stops = cmpy.get_stops_from_routes(None)
    # snapshot2 = tracemalloc.take_snapshot()

    # get stops containing the match string
    # this may return many stops, so the user may need to further filter
    # the results
    stops_carapinheira = cmpy.get_stops_containing('R Dom João V 51', stops)
    stops_lisboa = cmpy.get_stops_containing('Campo Grande', stops)

    # day for which to get the time table
    # format: YYYY-MM-DD
    day = "2023-06-29"

    day = day.replace('-', '')
    # get time table from origin to destination
    trips_c_l = cmpy.get_trips(
        stops_carapinheira, stops_lisboa, routes, day=day)
    trips_l_c = cmpy.get_trips(
        stops_lisboa, stops_carapinheira, routes, day=day)

    # snapshot3 = tracemalloc.take_snapshot()
    with open("carapinheira_lisboa.txt", "w", encoding='utf8') as f:
        f.write(f"Carapinheira -> Lisboa ({day}):\n")
        print(f"Carapinheira -> Lisboa ({day}):")
        for tripAB in trips_c_l:
            f.write(
                f"{tripAB.origin_time} -> {tripAB.destination_time}: {tripAB.trip.direction} - {tripAB.route.long_name} ({tripAB.route.id})\n")
            print(
                f"{tripAB.origin_time} -> {tripAB.destination_time}: {tripAB.trip.direction} - {tripAB.route.long_name} ({tripAB.route.id})")

    with open("lisboa_carapinheira.txt", "w", encoding='utf8') as f:
        f.write(f"Lisboa -> Carapinheira ({day}):\n")
        print(f"Lisboa -> Carapinheira ({day}):")
        for tripAB in trips_l_c:
            f.write(
                f"{tripAB.origin_time} -> {tripAB.destination_time}: {tripAB.trip.direction} - {tripAB.route.long_name} ({tripAB.route.id})\n")
            print(
                f"{tripAB.origin_time} -> {tripAB.destination_time}: {tripAB.trip.direction} - {tripAB.route.long_name} ({tripAB.route.id})")

    # for stat in snapshot2.compare_to(snapshot1, 'lineno'):
    #     print(stat)
    # for stat in snapshot3.compare_to(snapshot2, 'lineno'):
    #     print(stat)  

    # tracemalloc.stop()          
