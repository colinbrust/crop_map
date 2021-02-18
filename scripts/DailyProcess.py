import sys
sys.path.append('/mnt/e/PycharmProjects/old_misc_projects/crop_map/scripts')
import DataDownload
import datetime
import os
import glob

os.chdir('/mnt/e/PycharmProjects/old_misc_projects/crop_map/scripts')

def daily_process(date):

    DataDownload.download_data(date)

    DataDownload.make_sum()

    [os.remove(f) for f in glob.glob("../raw_images/*.nc")]


def monthly_process():

    if datetime.datetime.today().day == 29:

        DataDownload.save_scvi()
        print('NASS SCVI data saved')
        DataDownload.save_nass_production()
        print('NASS production saved')
        DataDownload.update_csv()
        print('Updated master dataframe')
        DataDownload.run_r_spi()
        print('Calculated Monthly SPI in R')
        DataDownload.save_eddi()
        print('Calculated Monthly EDDI')
        DataDownload.run_r_scvi()
        print('Calculated SCVI in R')
        DataDownload.run_r_prod()
        print('Normalized production in R')
        DataDownload.calc_scpi('spi')
        print('Calculated SCPI using SPI')
        DataDownload.calc_scpi('eddi')
        print('Calculated SCPI using EDDI')
        DataDownload.run_r_graph()
        print('Ran R code to add popup graph data')
        DataDownload.run_r_mouse()
        print('Ran R code to add mouseover data')
        DataDownload.run_r_thin()
        print('Thinned final data frame')


[daily_process(str(d)) for d in DataDownload.download_latest()]
# monthly_process()
print('Complete')





