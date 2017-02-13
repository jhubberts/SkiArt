from bs4 import BeautifulSoup
import argparse
import svgwrite

import random
import colorsys

def main(inputs, output):
    dwg = svgwrite.Drawing(output.name, profile='tiny')

    colors = get_n_colors(len(inputs))
    color_idx = 0

    parsed_inputs = parse_inputs(inputs)
    bounds = get_universal_bounds(parsed_inputs)

    for input in parsed_inputs:
        coords = points_to_coordinates(input["points"], bounds)
        dwg.add(dwg.polyline(coords, stroke=colors[color_idx], stroke_width="3", stroke_opacity="0.6", fill="none"))
        color_idx += 1

    dwg.save()

def parse_inputs(inputs):
    parsed_inputs = []
    for input in inputs:
        points = get_points_from_file(input)
        bounds = get_bounds(points)
        parsed_inputs.append({"points": points, "bounds": bounds})
    return parsed_inputs

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

def get_universal_bounds(parsed_inputs):
    """ Gets the bounds of all recorded segments """
    min_lat = float("inf")
    max_lat = float("-inf")
    min_lon = float("inf")
    max_lon = float("-inf")

    for parsed_input in parsed_inputs:
        min_lat = parsed_input["bounds"]["min_lat"] if parsed_input["bounds"]["min_lat"] < min_lat else min_lat
        min_lon = parsed_input["bounds"]["min_lon"] if parsed_input["bounds"]["min_lon"] < min_lon else min_lon
        max_lat = parsed_input["bounds"]["max_lat"] if parsed_input["bounds"]["max_lat"] > max_lat else max_lat
        max_lon = parsed_input["bounds"]["max_lon"] if parsed_input["bounds"]["max_lon"] > max_lon else max_lon

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
    parser.add_argument('inputs', type=argparse.FileType('r'), nargs='+')

    args = parser.parse_args()
    main(args.inputs, args.output)