from DataCollectionThredds import build_request
from argparse import Namespace
import datetime
import os
import numpy as np
import glob
import rasterio as rio
import matplotlib.pyplot as plt
import shutil
import fiona
import utilsRaster

def download_data(d):

    request_inputs = Namespace(BBoxType='vectorFile', attributes=['precip', 'pet'],
                               base_url='http://thredds.northwestknowledge.net:8080/thredds/ncss', date_end=d,
                               date_start=d, filename="../boundaries/state_boundaries/MT.geojson", flip=True,
                               output_folder='../raw_images/')

    build_request(request_inputs)


def get_raw_date():

    fname = glob.glob("../raw_images/*.nc")[0]

    return fname.split("/")[-1].split("_")[1].replace("F", "").split("-")


def get_raw_var(fname):

    return fname.split("/")[-1].split("_")[0]


def check_date():

    if get_raw_date()[2] == '01':
        return True
    return False


def sum_images(variable):

    summed_image = glob.glob("../mean_images/" + variable + "*" + "-".join(get_raw_date()[0:2]) + "*")[0]
    summed_image = utilsRaster.RasterParameterIO(summed_image)

    current_image = glob.glob("../raw_images/" + variable + "*")[0]
    current_image = utilsRaster.RasterParameterIO(current_image)

    new_image = summed_image.array + current_image.array

    out_name = "../mean_images/" + variable + "_" + "-".join(get_raw_date()[0:2]) + ".tif"

    summed_image.write_array_to_geotiff(out_name, np.squeeze(new_image))


def make_sum():

    if check_date():

        for f in glob.glob("../raw_images/*.nc"):

            first_image = utilsRaster.RasterParameterIO(f)
            out_name = "../mean_images/" + get_raw_var(f) + "_" + "-".join(get_raw_date()[0:2]) + ".tif"
            first_image.write_array_to_geotiff(out_name, np.squeeze(first_image.array))

    else:

        sum_images("precip")
        sum_images("pet")
