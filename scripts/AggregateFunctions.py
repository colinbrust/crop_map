import DataDownload
import datetime
import os
import glob

os.chdir('/home/colin.brust/workspace/scripts')

def daily_process(date):

    DataDownload.download_data(date)

    DataDownload.make_sum()

    [os.remove(f) for f in glob.glob("../raw_images/*.nc")]


def monthly_process():

    if datetime.datetime.today().day == 1:

        DataDownload.save_scvi()
        DataDownload.save_nass_production()
        DataDownload.update_csv()
        DataDownload.run_r_spi()
        DataDownload.save_eddi()
        DataDownload.run_r_scvi()
        DataDownload.run_r_prod()
        DataDownload.calc_scpi('spi')
        DataDownload.calc_scpi('eddi')
        #DataDownload.run_r_graph()
        #DataDownload.run_r_mouse()


[daily_process(str(d)) for d in DataDownload.download_latest()]
monthly_process()






