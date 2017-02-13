from bs4 import BeautifulSoup
import argparse
import svgwrite
import os
import random
import colorsys

def main(input, output):
    input_map = get_input_map(input)

    dwg = svgwrite.Drawing(output.name, profile='tiny')

    colors = get_n_colors(len(input_map))
    color_idx = 0

    parsed_input_map = parse_input_map(input_map)
    bounds = get_universal_bounds(parsed_input_map)

    for input in parsed_input_map:
        coords = points_to_coordinates(parsed_input_map[input]["points"], bounds)
        dwg.add(dwg.polyline(coords, stroke=colors[color_idx], stroke_width="3", stroke_opacity="0.6", fill="none"))
        color_idx += 1

    dwg.save()

def get_input_map(input_dir):
    input_map = {}

    for dir in os.listdir(input_dir):
        dir_path = os.path.join(input_dir,dir)
        input_map[dir] = map(lambda x: open(os.path.join(dir_path, x), 'r'), os.listdir(dir_path))

    return input_map

def parse_input_map(input_map):
    parsed_input_map = {}
    for input in input_map:
        points = []
        for file in input_map[input]:
            points.extend(get_points_from_file(file))
        bounds = get_bounds(points)
        parsed_input_map[input] = {"points": points, "bounds": bounds}
    return parsed_input_map

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

def get_universal_bounds(parsed_input_map):
    """ Gets the bounds of all recorded segments """
    min_lat = float("inf")
    max_lat = float("-inf")
    min_lon = float("inf")
    max_lon = float("-inf")

    for parsed_input in parsed_input_map:
        item = parsed_input_map[parsed_input]

        min_lat = item["bounds"]["min_lat"] if item["bounds"]["min_lat"] < min_lat else min_lat
        min_lon = item["bounds"]["min_lon"] if item["bounds"]["min_lon"] < min_lon else min_lon
        max_lat = item["bounds"]["max_lat"] if item["bounds"]["max_lat"] > max_lat else max_lat
        max_lon = item["bounds"]["max_lon"] if item["bounds"]["max_lon"] > max_lon else max_lon

    return {
        "min_lat": min_lat,
        "min_lon": min_lon,
        "max_lat": max_lat,
        "max_lon": max_lon
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

def points_to_coordinates(points, bounds, desired_width=1000):
    """ Transforms GPS points into coordinates for the desired SVG file """
    height = bounds["max_lat"] - bounds["min_lat"]
    width = bounds["max_lon"] - bounds["min_lon"]

    transform_coefficient = float(desired_width) / width # Make width 1000

    return map(lambda x: point_to_coordinate(x, bounds, transform_coefficient), points)

def get_n_colors(n):
    """ Returns N contrasting RGB fill descriptors """
    transform_constant = 1.0 / n

    rgb_colors = []

    for i in range(0, n):
        hue = i * transform_constant
        lightness = 0.5 + 0.1 * random.random()
        saturation = 0.9 + 0.1 * random.random()
        rgb = map(lambda x: x * 256.0, colorsys.hls_to_rgb(hue, lightness, saturation))
        rgb_colors.append(svgwrite.rgb(rgb[0], rgb[1], rgb[2], '%'))

    return rgb_colors


def point_to_coordinate(point, bounds, transform_coefficient):
    """ Transforms a single point into a coordinate in an SVG file """
    return ((point["lon"] - bounds["min_lon"]) * transform_coefficient,
            ((bounds["max_lat"] - bounds["min_lat"]) - (point["lat"] - bounds["min_lat"])) * transform_coefficient)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Turns a gpx file into an art.')
    parser.add_argument("-o", "--output", type=argparse.FileType('w'), required=True, help="Directs the output to a name of your choice")
    parser.add_argument("-i", "--input", required=True, help="Specifies the input directory")

    args = parser.parse_args()
    main(args.input, args.output)