import DataDownload
import datetime
import os
import glob

#d = str(datetime.date.today() - datetime.timedelta(days=1))

d = str(datetime.date(2018,8,2))


def daily_process(date):

    DataDownload.download_data(date)
    DataDownload.make_sum()

    for f in glob.glob("../raw_images/*.nc"):
        os.remove(f)


daily_process(d)

