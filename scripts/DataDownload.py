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
import sys
import subprocess
from functools import partial
import rasterio

# given a date, this function downloads pet and precip images for the area surrounding Montana.
def download_data(d):

    request_inputs = Namespace(BBoxType='vectorFile', attributes=['precip', 'pet'],
                               base_url='http://thredds.northwestknowledge.net:8080/thredds/ncss', date_end=d,
                               date_start=d, filename="../boundaries/all_bounds.geojson", flip=True,
                               output_folder='../raw_images/')

    build_request(request_inputs)


# returns the date of the images in the "raw_images" folder.
def get_raw_date():

    fname = glob.glob("../raw_images/*.nc")[0]

    return fname.split("/")[-1].split("_")[1].replace("F", "").split("-")


# returns the variable of an image based on filename.
def get_var(fname):

    return fname.split("/")[-1].split("_")[0]


# returns the date of a mean image.
def get_mean_date(fname):

    return fname.split("/")[-1].split("_")[1].replace(".tif", "")


# determines whether the latest daily image downloaded was from the first day of the month.
def check_date():

    if get_raw_date()[2] == '01':
        return True
    return False


# function that will be triggered if there is an error that occurs when downloading images
def remove_latest(variable):

    date_in = glob.glob("../mean_images/" + variable + "*")
    date_in = sorted(date_in, key=lambda x: datetime.datetime.strptime(
        x.split("/")[-1].split("_")[-1].replace(".tif", ""), '%Y-%m-%d'
    ))

    os.remove(date_in[-1])

# stacks and sums numpy arrays which are then written back out as geotiffs.
def sum_images(variable):

    date_use = "-".join(get_raw_date())
    date_use = datetime.datetime.strptime(date_use, "%Y-%m-%d").date()
    date_use_old = date_use - datetime.timedelta(days=1)

    summed_image = glob.glob("../mean_images/" + variable + "*" + str(date_use_old) + "*")[0]
    summed_image = utilsRaster.RasterParameterIO(summed_image)

    current_image = glob.glob("../raw_images/" + variable + "*")[0]

    try:
        current_image = utilsRaster.RasterParameterIO(current_image)

        new_image = summed_image.array + current_image.array

        out_name = "../mean_images/" + variable + "_" + str(date_use) + ".tif"
        del_name = "../mean_images/" + variable + "_" + str(date_use_old) + ".tif"

        summed_image.write_array_to_geotiff(out_name, np.squeeze(new_image))

        os.remove(del_name)

    except rasterio.errors.RasterioIOError as e:
        print e.args
        print "There seems to be an issue with the downloaded raster. The download process will stop " \
              "now and repeat tomorrow."
        remove_latest('precip')
        remove_latest('pet')
        [os.remove(f) for f in glob.glob("../raw_images/*.nc")]
        sys.exit(1)


# depending on whether or not it is the first day of the month, either copies over an image or sums it.
def make_sum():

    if check_date():

        for f in glob.glob("../raw_images/*.nc"):

            first_image = utilsRaster.RasterParameterIO(f)
            out_name = "../mean_images/" + get_var(f) + "_" + "-".join(get_raw_date()[0:3]) + ".tif"
            first_image.write_array_to_geotiff(out_name, np.squeeze(first_image.array))

    else:

        sum_images("precip")
        sum_images("pet")


# takes a string formatted as a date and returns a datetime.date object
def str_to_date(date):

    return datetime.datetime.strptime(date, "%Y-%m-%d").date()


# taken from stack exchange. Determines whether or not a date is the last day of the month.
def last_day_of_month(date):

    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)


# if an image is complete (has all days of the month), returns True given a filename
def is_img_complete(f):

    img_date = get_mean_date(f)
    img_date = datetime.datetime.strptime(img_date, "%Y-%m-%d").date()
    fin_date = last_day_of_month(img_date)

    if img_date == fin_date:
        return True
    return False


# returns a list of dates from the last downloaded image to today
def download_latest():

    date_in = glob.glob("../mean_images/precip*")
    print date_in
    start = []

    for date in date_in:
        start.append(date.split("/")[-1].split("_")[-1].replace(".tif", ""))

    start = max(map(str_to_date, start)) + datetime.timedelta(days=1)

    end = datetime.datetime.today() - datetime.timedelta(days=1)
    end = end.date()

    return [start + datetime.timedelta(days=x) for x in range(0, (end - start).days)]

# returns the name of the state given a geojson filename.
def state_from_fname(fname):

    return fname.split("/")[-1].replace(".geojson", "")


# return a list of properties given a geojson file.
def list_from_json(j):

    return [j['properties']['NAME'], j['properties']['mean']]


# given a filename of a summed monthly image, reduce the image at state county levels.
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


# updates the master dataframe csv file with newly completed monthly totals.
def update_csv():

    csv = pd.read_csv("../data_frames/master_df.csv", index_col=0)

    ppt = csv['variable'] == 'precip'
    ppt = csv[ppt]
    ppt_date = ppt['date'].tolist()


    pet = csv['variable'] == 'pet'
    pet = csv[pet]
    pet_date = pet['date'].tolist()

    for f in glob.glob("../mean_images/precip*"):

        if is_img_complete(f) and (get_mean_date(f) not in ppt_date):

            dat = agg_by_county(f)
            csv = csv.append(dat, ignore_index=True)
            print(f)

    for f in glob.glob("../mean_images/pet*"):

        if is_img_complete(f) and (get_mean_date(f) not in pet_date):

            dat = agg_by_county(f)
            csv = csv.append(dat, ignore_index=True)
            print(f)

    csv.to_csv("../data_frames/master_df.csv", sep=",")


# reads the master dataframe csv and reorders it into a dict by each county.
def reorder_data():

    dat = pd.read_csv("../data_frames/master_df.csv", index_col=0)
    dat = dat[dat.state.notnull()]
    pet = dat['variable'] == 'pet'
    dat = dat[pet]

    dat = dat.assign(county_name=dat.county_name.str.replace(" ", "_").str.replace("&", "and").str.lower())

    dat['state_county'] = dat.state.str.cat(dat.county_name, sep="_")
    dat = dat.drop(columns=['county_name', 'state'])

    unqs = dat.state_county.unique()

    # create a data frame dictionary to store your data frames
    dict = {elem: pd.DataFrame for elem in unqs}

    for key in dict.keys():
        dict[key] = dat[:][dat.state_county == key]

    for df in dict.keys():
        dict[df]['date'] = pd.to_datetime(dict[df]['date'], format='%Y-%m-%d')
        dict[df] = dict[df].sort_values(by=['date'])
        #dict[df]['value'] = signal.detrend(dict[df]['value'])
        dict[df] = dict[df].set_index('date')

    return dict

# calc prob_eoi
def prob_eoi(i, n):
    prob_eoi = (i - 0.33) / (n + 0.33)
    return prob_eoi

# calc eddi based on prob_eoi
def eddi(x):
    C0 = 2.515517
    C1 = 0.802853
    C2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.00130

    if x <= 0.5:
        W = np.sqrt(-2. * np.log(x))
        E = W - (C0 + C1 * W + C2 * W ** 2) / (1 + d1 * W + d2 * W ** 2 + d3 * W ** 3)
    if x > 0.5:
        W = np.sqrt(-2. * np.log(1 - x))
        E = -1. * (W - (C0 + C1 * W + C2 * W ** 2) / (1 + d1 * W + d2 * W ** 2 + d3 * W ** 3))

    return E

# merges two previous functions
def eddi_apply(i, n):

    prob = prob_eoi(i, n)

    return eddi(prob)


# calculates eddi for all counties in study area. Method taken from Patrick Wurstner.
def eddi_calc(df):

    name = df.state_county.unique()

    print(name)

    df = df.drop(columns=['variable', 'state_county'])

    df_final = pd.DataFrame()

    for lag in np.arange(1, 16):

        df_new = df.rolling(window=lag).sum()
        df_new = df_new.dropna()
        df_new = df_new.sort_values(by='value', ascending=False)

        size = len(df_new)

        df_new['rank'] = np.arange(1, len(df_new) + 1)
        df_new['size'] = np.repeat(size, size)
        df_new['eddi'] = df_new.apply(lambda x: eddi_apply(x['rank'], x['size']), axis=1)
        df_new['window'] = np.repeat(lag, size)
        df_new['state_county'] = np.repeat(name, size)

        df_new = df_new.reset_index()

        df_new['date'] = df_new['date'].dt.strftime('%Y-%m-%d')

        df_new['state'], df_new['county'] = df_new['state_county'].str.split('_', 1).str
        df_new['year'], df_new['month'], df_new['day'] = df_new['date'].str.split('-').str

        df_new = df_new.drop(columns=['state_county', 'rank', 'size', 'date', 'day', 'value'])
        df_final = df_final.append(df_new, ignore_index=True)

    return df_final

# combines reorder data function and eddi_calc function to save a df of eddi values.
def save_eddi():

    dat = reorder_data()
    dat_out = pd.DataFrame()

    for df in dat.keys():

        eddi_out = eddi_calc(dat[df])
        dat_out = dat_out.append(eddi_out, ignore_index=True)

    dat_out.to_csv("../data_frames/eddi_out.csv")


# returns the data from the NASS Quickstats API given a crop, year and state input.
def get_nass_data(crop, year, state):

    if crop == "BARLEY":
        data_item = "BARLEY - PRICE RECEIVED, MEASURED IN $ / BU"
    elif crop == "WHEAT":
        data_item = "WHEAT - PRICE RECEIVED, MEASURED IN $ / BU"
    elif crop == "HAY":
        data_item = "HAY, ALFALFA - PRICE RECEIVED, MEASURED IN $ / TON"

    parameters = {"source_desc": "SURVEY",
                  "year__LE": year,
                  "agg_level_desc": "STATE",
                  "state_alpha": state,
                  "short_desc": data_item,
                  "commodity_desc": crop,
                  "domain_desc": "TOTAL",
                  "freq_desc": "ANNUAL",
                  "reference_period_desc": "MARKETING YEAR"
                  }

    response = requests.get('http://quickstats.nass.usda.gov/api/api_GET/'
                            '?key=41C2FA23-531A-3899-B471-871B13C2748C',
                            params=parameters)

    return response.json()['data']


# uses the NASS Quickstats API to get actual production for every crop
def get_nass_production(crop, state):

    if crop == "BARLEY":
        data_item = "BARLEY - PRODUCTION, MEASURED IN BU"
    elif crop == "WHEAT":
        data_item = "WHEAT - PRODUCTION, MEASURED IN BU"
    elif crop == "HAY":
        data_item = "HAY, ALFALFA - PRODUCTION, MEASURED IN TONS"

    parameters = {"source_desc": "SURVEY",
                  "year__LE": datetime.datetime.today().year,
                  "agg_level_desc": "COUNTY",
                  "state_alpha": state,
                  "short_desc": data_item,
                  "commodity_desc": crop,
                  "domain_desc": "TOTAL",
                  "freq_desc": "ANNUAL",
                  "reference_period_desc": "YEAR"
                  }

    response = requests.get('http://quickstats.nass.usda.gov/api/api_GET/'
                            '?key=41C2FA23-531A-3899-B471-871B13C2748C',
                            params=parameters)

    return response.json()['data']


# takes the json file returned from NASS API and turns it into a pandas dataframe
def parse_nass_data(dat, data_type):

    state, county, year, crop, value = [], [], [], [], []

    for item in dat:

        state.append(item['state_alpha'])
        year.append(item['year'])
        crop.append(item['commodity_desc'])
        value.append(item['Value'])

        if data_type == 'prod':
            county.append(item['county_name'])

    if data_type == 'prod':
        return pd.DataFrame(
            {'state': state,
             'year': year,
             'crop': crop,
             'value': value,
             'county': county
             })

    return pd.DataFrame(
        {'state': state,
         'year': year,
         'crop': crop,
         'value': value,
         })


# uses the parse_nass_data function to save out crop production from NASS API.
def save_nass_production():

    crops = ["BARLEY", "WHEAT", "HAY"]
    states = ["MT", "ID", "WY", "ND", "SD"]

    all_data = []

    for state in states:
        for crop in crops:

            dat = get_nass_production(crop, state)
            all_data.append(dat)

    dat_out = pd.concat(map(partial(parse_nass_data, data_type='prod'), all_data), ignore_index=True)

    out_name = "../data_frames/nass_production.csv"

    dat_out.to_csv(out_name)


# creates combination of all possible NASS entries and then saves out to csv using parse_nass_data function.
def save_scvi():

    crops = ["BARLEY", "WHEAT", "HAY"]
    states = ["MT", "ID", "WY", "ND", "SD"]
    year = datetime.datetime.today().year

    all_data = []

    for state in states:
        for crop in crops:

            dat = get_nass_data(crop, year, state)
            all_data.append(dat)

    dat_out = pd.concat(map(partial(parse_nass_data, data_type='val'), all_data), ignore_index=True)

    out_name = "../data_frames/nass_data.csv"

    dat_out.to_csv(out_name)


# For the current year, it is possible that the optimal month hasn't yet been reached to calculate the SCPI.
# To fix the issue, this function looks the optimal month/lag of a county and determines if it has been reached yet.
# If it has, the optimal month and lag is used. If it hasn't, the current month and most optimal lag for the current
# month is used.
def manage_current_year(stat):

    if int(datetime.datetime.today().month) == 1:
        return pd.DataFrame()

    dat = pd.read_csv("../data_frames/%s_out.csv" % stat, index_col=0)
    dat = dat[dat['year'] == datetime.datetime.today().year]

    opt = pd.read_csv("../data_frames/best_month_coeffs.csv", index_col=0)
    opt = opt.rename(index=str, columns={"lag": "window"})

    dat_nass = pd.read_csv("../data_frames/scvi_detrended.csv")

    merged = pd.merge(dat, opt, how='right',
                    left_on=['state', 'month', 'window', 'county'],
                    right_on=['state', 'month', 'window', 'county'])

    complete = merged[merged[stat].notnull()]
    incomp = merged[merged[stat].isnull()]
    incomp = incomp.drop([stat, 'year', 'month', 'window',
                          'alpha', 'beta', 'gamma', 'rmse'], axis=1)

    if datetime.datetime.today().month == 1:
        incomp['month'] = 12
    else:
        incomp['month'] = int(datetime.datetime.today().month - 1)

    for_merge = pd.read_csv("../data_frames/tidy_coeffs.csv")

    for_merge = pd.merge(incomp, for_merge, how='left',
                    left_on=['state', 'month', 'stat', 'county', 'crop'],
                    right_on=['state', 'month', 'stat', 'county', 'crop'])
    for_merge = for_merge.rename(index=str, columns={"lag": "window"})

    merged = pd.merge(dat, for_merge, how='right',
                      left_on=['state', 'month', 'window', 'county'],
                      right_on=['state', 'month', 'window', 'county'])

    dat = complete.append(merged)
    dat = pd.merge(dat, dat_nass, how='left',
                   left_on=['state', 'year', 'crop'],
                   right_on=['state', 'year', 'crop'])
    dat = dat.assign(scpi=(dat.alpha * dat[stat]) + (dat.beta * dat.scvi) + dat.gamma)
    dat = dat[dat['stat'] == stat]
    return dat


def calc_scpi(stat):

    # data frames containing all necessary data.
    dat_in = pd.read_csv("../data_frames/%s_out.csv" % stat, index_col=0)
    dat_nass = pd.read_csv("../data_frames/scvi_detrended.csv")
    dat_coeff = pd.read_csv("../data_frames/best_month_coeffs.csv")
    dat_coeff = dat_coeff[dat_coeff['stat'] == stat]
    dat_coeff = dat_coeff.rename(index=str, columns={"lag": "window"})

    dat = pd.merge(dat_in, dat_nass, how='left',
                   left_on=['state', 'year'],
                   right_on=['state', 'year'])

    dat = pd.merge(dat, dat_coeff, how='right',
                   left_on=['state', 'month', 'window', 'county', 'crop'],
                   right_on=['state', 'month', 'window', 'county', 'crop'])

    dat = dat.assign(scpi=(dat.alpha*dat[stat]) + (dat.beta*dat.scvi) + dat.gamma)
    dat = dat[dat['year'] < datetime.datetime.today().year]

    dat = dat.append(manage_current_year(stat), sort=False,
                     ignore_index=True)

    dat.to_csv("../data_frames/master_%s_scpi.csv" % stat)


# Functions that are written in R. These either use the SPEI package or use R specific functions to
# create objects for the shiny app.

# R script that calculates SPI and saves out a csv.
# The SPI package for python only works on python 3
def run_r_spi():

    subprocess.call(["/home/MARCO/anaconda2/envs/test/bin/Rscript", "--vanilla", "../R/calc_spi.R"])


# Detrends and passes scvi values through spi function in R.
def run_r_scvi():

    subprocess.call(["/home/MARCO/anaconda2/envs/test/bin/Rscript", "--vanilla", "../R/detrend_standard_scvi.R"])


# detrends and passes crop production values through spi function in R.
def run_r_prod():

    subprocess.call(["/home/MARCO/anaconda2/envs/test/bin/Rscript", "--vanilla", "../R/detrend_standard_prod.R"])


# creates HTML graph objects to be used in the shiny app.
def run_r_graph():

    subprocess.call(["/home/MARCO/anaconda2/envs/test/bin/Rscript", "--vanilla", "../R/save_popups.R"])


# creates HTML table objects to be used in the shiny app.
def run_r_mouse():

    subprocess.call(["/home/MARCO/anaconda2/envs/test/bin/Rscript", "--vanilla", "../R/add_mouseover_data.R"])

