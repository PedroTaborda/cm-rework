import cmpy


if __name__ == "__main__":
    lines = cmpy.get_all_lines()

    print("This script has no output. It's just a test script.")
    print("Its purpose is to test the API and make sure it works.")
    print("However, it is a good example of how to use the API.")

    lines_with_no_routes = []
    for line in lines:
        routes = cmpy.get_line_routes(line)

        if not routes:
            lines_with_no_routes.append(line)
            continue

        stops = cmpy.get_route_stops(
            routes[0], routes[0].ways[0], "2023-01-24")

        routes[0].ways[0].set_stops(stops)

        time_table = cmpy.get_route_time_table(
            routes[0], routes[0].ways[0], "2023-01-24")
