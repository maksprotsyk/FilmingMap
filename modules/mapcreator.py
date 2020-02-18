from pandas import read_csv
from geopy.geocoders import Nominatim
import ssl
import folium
from countryinfo import CountryInfo
from country_converter import CountryConverter
from copy import copy


ssl._create_default_https_context = ssl._create_unverified_context
GEOLOCATOR = Nominatim(user_agent='name')


def bordering_countries(country_name: str) -> set:
    """
    Finds bordering countries for the given country
    """
    rename_dct = {'United States': 'USA', 'United Kingdom': 'UK'}
    try:
        country = CountryInfo(country_name)
        converter = CountryConverter(include_obsolete=True)
        countries = converter.convert(country.borders(), to='name_short')
        if type(countries) == str:
            countries = {countries}
        else:
            countries = set(countries)
            countries.add(country_name)
        for name in rename_dct:
            if name in countries:
                countries.remove(name)
                countries.add(rename_dct[name])
        return countries
    except Exception:
        print('Invalid Country')


def open_file(locations_file: str, year: int) -> dict:
    """
    Opens csv file and gets information about
    all films filmed in the given year
    """
    year = str(year)
    data = read_csv(locations_file, error_bad_lines=False, warn_bad_lines=False)
    data = data.drop("add_info", axis=1).drop_duplicates()
    data = data.loc[data['year'] == year].drop("year", axis=1)
    data = data.drop(data[data['location'] == 'NO DATA'].index)
    names = data['movie']
    locations = data['location']
    locations_dct = {}
    for name, location in zip(names, locations):
        if location in locations_dct:
            locations_dct[location].add(name)
        else:
            locations_dct[location] = {name}
    for location in locations_dct:
        locations_dct[location] = tuple(locations_dct[location])
    return locations_dct


def possible_locations(locations_dct, location):
    """
    Finds at most 10 locations of filming with the most
    words in common with the given location
    """
    locations_dct = copy(locations_dct)
    current_location = list(map(lambda x: x.strip(), location.split(',')))
    coincidence_dct = {}
    for location in locations_dct:
        coincidence = 0
        for part in current_location:
            if part in location:
                coincidence += 1
        if coincidence:
            coincidence_dct[location] = coincidence
    coincidence_tuple = list(coincidence_dct.items())
    coincidence_tuple.sort(key=lambda x: x[1], reverse=True)
    coincidence_lst = [x[0] for x in coincidence_tuple]
    places = 0
    good_locations = []
    for item in coincidence_lst:
        places += 1
        good_locations.append(item)
        if places >= 10:
            break
    return [(x, locations_dct[x][0]) for x in good_locations]


def find_current_location(coordinates):
    """
    Return location name by its coordinates
    """
    location = GEOLOCATOR.reverse(coordinates, language='en')
    return location.address


def find_location_by_name(name):
    """
    Find coordinates of location by its name
    """
    location = GEOLOCATOR.geocode(name)
    if location is not None:
        return location.latitude, location.longitude


def full_search(year, coordinates):
    """
    Finds at most 10 locations where were filmed
    films near given location
    """
    location = find_current_location(coordinates)
    films = possible_locations(open_file('locations.csv', year), location)
    res_list = []
    for film in films:
        film_loc = find_location_by_name(film[0])
        if film_loc is not None:
            res_list.append((film[1], film_loc))
    return res_list


def create_map(year, coordinates, country):
    """
    Creates html file with locations got from
    full search function and locations of bordering
    countries to the given country
    """
    films = full_search(year, coordinates)
    coord = coordinates.split()
    neighbours = bordering_countries(country)
    map_obj = folium.Map(location=(float(coord[0]), float(coord[1])), zoom_start=5)

    fg = folium.FeatureGroup(name="Films locations")
    for item in films:
        fg.add_child(folium.CircleMarker(location=item[1],
                                         radius=15,
                                         popup=item[0],
                                         color='red',
                                         fill_color='black'))
    countries = folium.FeatureGroup(name="Countries")
    for item in neighbours:
        loc = find_location_by_name(item)
        countries.add_child(folium.CircleMarker(location=loc,
                                                radius=20,
                                                color='green',
                                                fill_color='yellow'))
    map_obj.add_child(fg)
    map_obj.add_child(countries)
    map_obj.save(f'map{year}.html')


def main():
    coordinates = input("ENTER YOUR COORDINATES: ")
    year = int(input('ENTER THE YEAR:'))
    country = input("Enter country to find its neighbours: ")
    create_map(year, coordinates, country)
    print('Map created')