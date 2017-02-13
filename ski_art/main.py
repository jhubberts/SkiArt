from bs4 import BeautifulSoup
import argparse
import svgwrite

def main(inputs, output):
    dwg = svgwrite.Drawing(output.name, profile='tiny')

    points = []
    for file in inputs:
        points.extend(get_points_from_file(file))

    bounds = get_bounds(points)

    height = bounds["max_lat"] - bounds["min_lat"]
    width = bounds["max_lon"] - bounds["min_lon"]

    transform_coefficient = 1000.0 / width # Make width 1000

    for point in points:
        point["x"] = (point["lon"] - bounds["min_lon"]) * transform_coefficient
        point["y"] = (point["lat"] - bounds["min_lat"]) * transform_coefficient

    coords = map(lambda x: (x["x"], x["y"]), points)
    dwg.add(dwg.polyline(coords, stroke="black", stroke_width="3", fill="white"))
    dwg.save()

def get_points_from_file(file):
    """ Parses a GPX file, and returns an array of all GPS points described by that file """
    parsed = BeautifulSoup(file.read(), 'html.parser')
    segments = parsed.trk.findAll("trkseg")
    points = []

    for segment in segments:
        segment_points = segment.findAll("trkpt")
        points.extend(map(lambda x: transform_bs4_point(x), segment_points))

    return points

def transform_bs4_point(bs4_point):
    """ Transforms a single BeautifulSoup node representing a node in the GPS coordinate graph
    into a dictionary representing the elements we care about """
    return {
        "lat": float(bs4_point["lat"]), # Degrees
        "lon": float(bs4_point["lon"]), # Degrees
        "ele": float(bs4_point.ele.string), # Meters?
        "time": bs4_point.time.string # ISO8601
    }

def get_bounds(points):
    """ Returns the min and max lat and lon within an array of points """
    min_lat = float("inf")
    max_lat = float("-inf")
    min_lon = float("inf")
    max_lon = float("-inf")

    for point in points:
        min_lat = point["lat"] if point["lat"] < min_lat else min_lat
        min_lon = point["lon"] if point["lon"] < min_lon else min_lon
        max_lat = point["lat"] if point["lat"] > max_lat else max_lat
        max_lon = point["lon"] if point["lon"] > max_lon else max_lon

    return {
        "min_lat": min_lat,
        "min_lon": min_lon,
        "max_lat": max_lat,
        "max_lon": max_lon
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Turns a gpx file into an art.')
    parser.add_argument("-o", "--output", type=argparse.FileType('w'), required=True, help="Directs the output to a name of your choice")
    parser.add_argument('inputs', type=argparse.FileType('r'), nargs='+')

    args = parser.parse_args()
    main(args.inputs, args.output)