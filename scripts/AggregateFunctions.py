import DataDownload
import utilsRaster
import datetime
import os
import glob
import numpy as np

#

d = str(datetime.date(2018, 8, 3))


def daily_process(date):

    DataDownload.download_data(date)
    DataDownload.make_sum()

    [os.remove(f) for f in glob.glob("../raw_images/*.nc")]


d = datetime.date(1980, 1, 1)

for i in range(14098):
    daily_process(d)
    d = d + datetime.timedelta(days = 1)
