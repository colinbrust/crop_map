from DataCollectionThredds import build_request
from argparse import Namespace
import datetime
import glob
import rasterio as rio
import matplotlib.pyplot as plt

d = datetime.date.today() - datetime.timedelta(days = 1)

'''
# rasterio to open NetCDF
request_inputs = Namespace(BBoxType='bbox', attributes=['precip'], base_url='http://thredds.northwestknowledge.net:8080/thredds/ncss',
                           date_end=str(d), date_start=str(d), east_bound=-112.0, flip=True, north_bound=49.0,
                           output_folder='/Users/cbandjelly/PycharmProjects/crop_map/raw_images/', south_bound=47.0, west_bound=-114.0)

build_request(request_inputs)

'''

rasters = []

for f in glob.glob("../raw_images/*.nc"):

    with rio.open(f) as src:
        projection = src.transform
        data = src.read()

    plt.imshow(data[0,:,:])
    plt.show()
    print(data)


    print(f)

# cronjob


