import DataDownload
import datetime
import os
import glob

def daily_process(date):

    DataDownload.download_data(date)

    DataDownload.make_sum()

    [os.remove(f) for f in glob.glob("../raw_images/*.nc")]


def monthly_process():

    if datetime.datetime.today().day == 21:

        DataDownload.save_all_nass()
        DataDownload.update_csv()
        DataDownload.run_r_spi()
        DataDownload.run_r_scvi()
        DataDownload.calc_scpi('spi')



[daily_process(str(d)) for d in DataDownload.download_latest()]
monthly_process()






