from DataCollectionThredds import build_request
from argparse import Namespace
import numpy as np
import glob
import rasterio as rio
import rasterstats
import utilsRaster
import pandas as pd
import requests
import datetime
import os
from scipy import signal


def download_data(d):

    request_inputs = Namespace(BBoxType='vectorFile', attributes=['precip', 'pet'],
                               base_url='http://thredds.northwestknowledge.net:8080/thredds/ncss', date_end=d,
                               date_start=d, filename="../boundaries/all_bounds.geojson", flip=True,
                               output_folder='../raw_images/')

    build_request(request_inputs)


def get_raw_date():

    fname = glob.glob("../raw_images/*.nc")[0]

    return fname.split("/")[-1].split("_")[1].replace("F", "").split("-")


def get_var(fname):

    return fname.split("/")[-1].split("_")[0]


def get_mean_date(fname):

    return fname.split("/")[-1].split("_")[1].replace(".tif", "")


def check_date():

    if get_raw_date()[2] == '01':
        return True
    return False


def sum_images(variable):

    date_use = "-".join(get_raw_date())
    date_use = datetime.datetime.strptime(date_use, "%Y-%m-%d").date()
    date_use_old = date_use - datetime.timedelta(days=1)

    summed_image = glob.glob("../mean_images/" + variable + "*" + str(date_use_old) + "*")[0]
    summed_image = utilsRaster.RasterParameterIO(summed_image)

    current_image = glob.glob("../raw_images/" + variable + "*")[0]
    current_image = utilsRaster.RasterParameterIO(current_image)

    new_image = summed_image.array + current_image.array

    out_name = "../mean_images/" + variable + "_" + str(date_use) + ".tif"
    del_name = "../mean_images/" + variable + "_" + str(date_use_old) + ".tif"

    summed_image.write_array_to_geotiff(out_name, np.squeeze(new_image))

    os.remove(del_name)


def make_sum():

    if check_date():

        for f in glob.glob("../raw_images/*.nc"):

            first_image = utilsRaster.RasterParameterIO(f)
            out_name = "../mean_images/" + get_var(f) + "_" + "-".join(get_raw_date()[0:3]) + ".tif"
            first_image.write_array_to_geotiff(out_name, np.squeeze(first_image.array))

    else:

        sum_images("precip")
        sum_images("pet")


def download_latest():

    date_in = glob.glob("../mean_images/precip*")[-1]
    date_in = get_mean_date(date_in)
    date_in = datetime.datetime.strptime(date_in, "%Y-%m-%d") + datetime.timedelta(days=1)

    end = datetime.datetime.today() - datetime.timedelta(days=1)
    return [date_in.date() + datetime.timedelta(days=x) for x in range(0, (end - date_in).days)]



def state_from_fname(fname):

    return fname.split("/")[-1].replace(".geojson", "")


def list_from_json(j):

    return [j['properties']['NAME'], j['properties']['mean']]


def agg_by_county(f):

    variable = get_var(f)
    date = get_mean_date(f)

    dat = utilsRaster.RasterParameterIO(f)
    dat.affine = rio.Affine(0.041666666666666664, 0.0, -117.03749996666667,
                            0.0, -0.0416666666666667, 49.42083333333334)

    boundaries = ["../boundaries/state_boundaries/MT.geojson",
                  "../boundaries/state_boundaries/ID.geojson",
                  "../boundaries/state_boundaries/ND.geojson",
                  "../boundaries/state_boundaries/SD.geojson",
                  "../boundaries/state_boundaries/WY.geojson"]

    df = pd.DataFrame(columns=['county_name', 'value', 'variable', 'date', 'state'])

    for shp in boundaries:

        j = rasterstats.zonal_stats(shp,
                                    np.squeeze(dat.array),
                                    stats="mean",
                                    affine=dat.affine,
                                    geojson_out=True)

        var_mean_dict = map(list_from_json, j)

        df_app = pd.DataFrame(data=var_mean_dict, columns=['county_name', 'value'])
        df_app['variable'] = variable
        df_app['date'] = date
        df_app['state'] = state_from_fname(shp)

        df = df.append(df_app)

    return df


def make_master_df():

    # add timestap
    ppt_df = map(agg_by_county, glob.glob("../mean_images/precip*"))
    ppt_df = pd.concat(ppt_df)

    pet_df = map(agg_by_county, glob.glob("../mean_images/pet*"))
    pet_df = pd.concat(pet_df)

    return pd.concat([ppt_df, pet_df])


def detrend_data(dat):

    dat_out = dat.groupby(['state', 'county_name', 'variable'])
    dat_out = dat_out['value'].apply(lambda x: signal.detrend(x))

    return pd.DataFrame({'info': dat_out.index,
                         'values': dat_out.values})

# unstack





def get_nass_data():


    # build dictionary with key value pairs to put into requests
    test = 'http://quickstats.nass.usda.gov/api/get_counts/?key=41C2FA23-531A-3899-B471-871B13C2748C&commodity_desc=CORN&year__GE=2012&state_alpha=VA'#&format=CSV'
    return requests.get(test)



# test = make_master_df()
#
# print(detrend_data(test))

# #test2 = get_nass_data()
#
# #print(test2.content
# test = pd.read_csv("../test/pd_test.csv", sep=",")
# test = test.loc[test['state'] == "MT"]
# test = detrend_data(test)

# images = glob.glob("../mean_images/precip*")
#
# test = [(get_mean_date(x)) for x in images]

