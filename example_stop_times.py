import cmpy

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
    lines = cmpy.get_all_lines()

    # prior knowledge of line ids may be used to reduce the number of lines to
    # be matched (optional)
    #lines = cmpy.match_lines_containing(
    #    line_ids_carapinheira, lines, type='id')

    # get all unique stops from lines (shared stops are not duplicated)
    # there is usually one stop per way, which share the same name, but
    # have different ids
    stops = cmpy.get_stops_from_lines(None)

    # get stops containing the match string
    # this may return many stops, so the user may need to further filter
    # the results
    stops_carapinheira = cmpy.get_stops_containing('R Dom João V 51', stops)
    stops_lisboa = cmpy.get_stops_containing('Campo Grande', stops)

    # get ways (associated with a route) which have an origin stop before a
    # destination stop
    # this isn't used in this example, but may be useful for other purposes
    ways1 = cmpy.get_ways_with_origin_before_destination(
        stops_carapinheira, stops_lisboa, lines)
    ways2 = cmpy.get_ways_with_origin_before_destination(
        stops_lisboa, stops_carapinheira, lines)

    # day for which to get the time table
    # format: YYYY-MM-DD
    day = "2023-01-23"

    # get time table from origin to destination
    times_c_l = cmpy.get_time_table_from_origin_to_destination(
        stops_carapinheira, stops_lisboa, lines, day=day)
    times_l_c = cmpy.get_time_table_from_origin_to_destination(
        stops_lisboa, stops_carapinheira, lines, day=day)

    # unrolls the times (aggregated by stop (and way and route)) to a single list of times
    # input: [StopTimes(stop1, [time1, time2]), StopTimes(stop2, [time3, time4])]
    # output: [StopTimes(stop1, [time1]), StopTimes(stop1, [time2]), StopTimes(stop2, [time3]), StopTimes(stop2, [time4])]
    # the output is also sorted by time
    joint_times_c_l = cmpy.join_times(times_c_l)
    joint_times_l_c = cmpy.join_times(times_l_c)

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
