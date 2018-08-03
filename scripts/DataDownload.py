from DataCollectionThredds import build_request
from argparse import Namespace
import datetime
import glob
import rasterio as rio
import matplotlib.pyplot as plt
import shutil
import fiona


def download_data():

    d = str(datetime.date.today() - datetime.timedelta(days=1))

    request_inputs = Namespace(BBoxType='vectorFile', attributes=['precip', 'tempmax', 'tempmin'],
                               base_url='http://thredds.northwestknowledge.net:8080/thredds/ncss', date_end=d,
                               date_start=d, filename="../boundaries/state_boundaries/MT.geojson", flip=True,
                               output_folder='../raw_images/')

    build_request(request_inputs)


#download_data()


def get_dates(fname):

    return fname.split("/")[-1].split("_")[1].replace("F", "").split("-")


def get_variable(fname):

    return fname.split("/")[-1].split("_")[0]


def get_mean_date(fname):

    return fname.split("/")[-1].split("_")[1]


def new_mean_img(mean_img, daily_img):

    n = int(get_mean_date(fname)[2])

    return (n*mean_img + daily_img)/(n + 1)


for f in glob.glob("../raw_images/*.nc"):

    if get_dates(f)[2] == '01':

        # figure out what doesn't work with this
        shutil.copy2(f, "../mean_images/" + get_variable(f) + "_" + "-".join(get_dates(f)))

    else:

        variable = get_variable(f)

        with rio.open(f) as src:
            day_img = src.read()

        old_mean = glob.glob("../mean_images/" + variable + "*")[0]

        with rio.open(old_mean) as src:
            mean_img = src.read()

        new_mean = new_mean_img(mean_img, day_img)




# cronjob




