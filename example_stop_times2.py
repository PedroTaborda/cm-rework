import cmpy

if __name__ == "__main__":
    # get all lines
    lines = cmpy.get_all_lines()

    # get all unique stops
    stops = cmpy.get_all_stops()

    # get stops containing the match string
    # this may return many stops, so the user may need to further filter
    # the results
    stops_b_sousas = cmpy.get_stops_containing('Av 25 Abril 1 (B Sousas)', stops)
    stops_lisboa = cmpy.get_stops_containing('Campo Grande', stops)

    # get ways (associated with a route) which have an origin stop before a
    # destination stop
    # this isn't used in this example, but may be useful for other purposes
    ways1 = cmpy.get_ways_with_origin_before_destination(
        stops_b_sousas, stops_lisboa, lines)
    ways2 = cmpy.get_ways_with_origin_before_destination(
        stops_lisboa, stops_b_sousas, lines)

    # day for which to get the time table
    # format: YYYY-MM-DD
    day = "2023-01-30"

    # get time table from origin to destination
    trips_o_d = cmpy.get_trips(
        stops_b_sousas, stops_lisboa, lines, day=day)
    trips_d_o = cmpy.get_trips(
        stops_lisboa, stops_b_sousas, lines, day=day)

    with open(f"b_sousas_lisboa_{day}.txt", "w", encoding='utf8') as f:
        f.write(f"B Sousas -> Lisboa ({day}):\n")
        print(f"B Sousas -> Lisboa ({day}):")
        for trip in trips_o_d:
            f.write(
                f"{trip.origin_time} -> {trip.destination_time}: {trip.way} - {trip.way._route.name} ({trip.way._route._line.id})\n")
            print(
                f"{trip.origin_time} -> {trip.destination_time}: {trip.way} - {trip.way._route.name} ({trip.way._route._line.id})")

    with open(f"lisboa_b_sousas_{day}.txt", "w", encoding='utf8') as f:
        f.write(f"Lisboa -> B Sousas ({day}):\n")
        print(f"Lisboa -> B Sousas ({day}):")
        for trip in trips_d_o:
            f.write(
                f"{trip.origin_time} -> {trip.destination_time}: {trip.way} - {trip.way._route.name} ({trip.way._route._line.id})\n")
            print(
                f"{trip.origin_time} -> {trip.destination_time}: {trip.way} - {trip.way._route.name} ({trip.way._route._line.id})")
