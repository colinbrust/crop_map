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



for f in glob.glob("../raw_images/*.nc"):

    img_day = get_dates(f)[2]

    if img_day == '01':

        shutil.copy2(f, "../mean_images/" + get_variable(f) + "_" + str(get_dates(f)[0]) + "-" + str(get_dates(f)[1]))
'''

    with rio.open(f) as src:
        projection = src.transform
        data = src.read()

    plt.imshow(data[0,:,:])
    plt.show()
    print(data)


    print(f)

# cronjob


'''

