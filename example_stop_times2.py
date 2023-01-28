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
    times_o_d = cmpy.get_time_table_from_origin_to_destination(
        stops_b_sousas, stops_lisboa, lines, day=day)
    times_d_o = cmpy.get_time_table_from_origin_to_destination(
        stops_lisboa, stops_b_sousas, lines, day=day)

    # unrolls the times (aggregated by stop (and way and route)) to a single list of times
    # input: [StopTimes(stop1, [time1, time2]), StopTimes(stop2, [time3, time4])]
    # output: [StopTimes(stop1, [time1]), StopTimes(stop1, [time2]), StopTimes(stop2, [time3]), StopTimes(stop2, [time4])]
    # the output is also sorted by time
    joint_times_o_d = cmpy.join_times(times_o_d)
    joint_times_d_o = cmpy.join_times(times_d_o)

    with open(f"b_sousas_lisboa_{day}.txt", "w", encoding='utf8') as f:
        f.write(f"B Sousas -> Lisboa ({day}):\n")
        print(f"B Sousas -> Lisboa ({day}):")
        for time in joint_times_o_d:
            f.write(f"{time.times[0]} - {time.stop._way._route}\n")
            print(f"{time.times[0]} - {time.stop._way._route}")

    with open(f"lisboa_b_sousas_{day}.txt", "w", encoding='utf8') as f:
        f.write(f"Lisboa -> B Sousas ({day}):\n")
        print(f"Lisboa -> B Sousas ({day}):")
        for time in joint_times_d_o:
            f.write(f"{time.times[0]} - {time.stop._way._route}\n")
            print(f"{time.times[0]} - {time.stop._way._route}")
