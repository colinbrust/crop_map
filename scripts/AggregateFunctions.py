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


d = datetime.date(1981, 8, 1)

for i in range(13522):
    daily_process(str(d))
    d = d + datetime.timedelta(days=1)
