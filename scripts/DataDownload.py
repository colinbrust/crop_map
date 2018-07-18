from DataCollectionThredds import build_request
from argparse import Namespace
import datetime

d = datetime.date.today()

# rasterio to open NetCDF
request_inputs = Namespace(BBoxType='bbox', attributes=['precip'], base_url='http://thredds.northwestknowledge.net:8080/thredds/ncss',
                           date_end='2018-06-10', date_start='2018-06-08', east_bound=-112.0, flip=True, north_bound=49.0,
                           output_folder='/Users/cbandjelly/PycharmProjects/crop_map/raw_images/', south_bound=47.0, west_bound=-114.0)

build_request(request_inputs)

