import DataDownload
import utilsRaster
import datetime
import os
import glob
import numpy as np


def daily_process(date):

    DataDownload.download_data(date)

    DataDownload.make_sum()

    [os.remove(f) for f in glob.glob("../raw_images/*.nc")]


def monthly_process(date):

    return 0


def annual_process(date):

    return 0




[daily_process(str(d)) for d in DataDownload.download_latest()]

