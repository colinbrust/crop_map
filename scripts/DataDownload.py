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
import subprocess
from scipy import signal

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


# stacks and sums numpy arrays which are then written back out as geotiffs.
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


# reads the master dataframe csv and detrends precip and pet data by county.
def detrend_data():

    dat = pd.read_csv("../data_frames/master_df.csv", index_col=0)
    dat = dat[dat.state.notnull()]
    dat['date'] = pd.to_datetime(dat['date'], format='%Y-%m-%d')
    dat = dat.sort_values(by=['date'])
    dat = dat.groupby(['state', 'county_name', 'variable'])

    dat_out = dat['value'].apply(lambda x: signal.detrend(x))

    return pd.DataFrame({'info': dat_out.index,
                         'values': dat_out.values})

# R script that calculates SPI and saves out a csv.
# The SPI package for python only works on python 3
def run_r_spi():

    subprocess.call(["/usr/bin/Rscript", "--vanilla", "../R/calc_spi.R"])


# Detrends and passes scvi values through spi function in R.
def run_r_scvi():

    subprocess.call(["/usr/bin/Rscript", "--vanilla", "../R/detrend_standard_scvi.R"])


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
                  "reference_period_desc": "MARKETING YEAR",
                  "agg_level_desc": "STATE",
                  "state_alpha": state,
                  "short_desc": data_item,
                  "commodity_desc": crop,
                  "domain_desc": "TOTAL"
                  }

    response = requests.get('http://quickstats.nass.usda.gov/api/api_GET/'
                            '?key=41C2FA23-531A-3899-B471-871B13C2748C',
                            params=parameters)

    return response.json()['data']


# takes the json file returned from NASS API and turns it into a pandas dataframe
def parse_nass_data(dat):

    state, year, crop, value = [], [], [], []

    for item in dat:
        state.append(item['state_alpha'])
        year.append(item['year'])
        crop.append(item['commodity_desc'])
        value.append(item['Value'])

    return pd.DataFrame(
        {'state': state,
         'year': year,
         'crop': crop,
         'value': value
         })


# creates combination of all possible NASS entries and then saves out to csv using parse_nass_data function.
def save_all_nass():

    crops = ["BARLEY", "WHEAT", "HAY"]
    states = ["MT", "ID", "WY", "ND", "SD"]
    year = datetime.datetime.today().year

    all_data = []

    for state in states:
        for crop in crops:

            dat = get_nass_data(crop, year, state)
            all_data.append(dat)

    dat_out = pd.concat(map(parse_nass_data, all_data), ignore_index=True)

    out_name = "../data_frames/nass_data.csv"

    dat_out.to_csv(out_name)


def manage_current_year(stat):

    if int(datetime.datetime.today().month) == 1:
        return pd.DataFrame()

    dat = pd.read_csv("../data_frames/spi_out.csv")
    dat = dat[dat['year'] == datetime.datetime.today().year]

    opt = pd.read_csv("../data_frames/best_month_coeffs.csv")
    opt = opt.rename(index=str, columns={"lag": "window"})

    dat_nass = pd.read_csv("../data_frames/scvi_detrended.csv")

    merged = pd.merge(dat, opt, how='right',
                    left_on=['state', 'month', 'window', 'county'],
                    right_on=['state', 'month', 'window', 'county'])

    complete = merged[merged.spi.notnull()]
    incomp = merged[merged.spi.isnull()]
    incomp = incomp.drop(['variable', 'spi', 'year', 'month', 'window',
                          'alpha', 'beta', 'gamma', 'rmse'], axis=1)
    incomp['month'] = int(datetime.datetime.today().month) - 1

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
    dat = dat.assign(scpi=(dat.alpha * dat.spi) + (dat.beta * dat.scvi) + dat.gamma)
    dat = dat[dat['stat'] == stat]
    return dat


def calc_scpi(stat):

    # data frames containing all necessary data.
    dat_spi = pd.read_csv("../data_frames/spi_out.csv")
    dat_nass = pd.read_csv("../data_frames/scvi_detrended.csv")
    dat_coeff = pd.read_csv("../data_frames/best_month_coeffs.csv")
    dat_coeff = dat_coeff[dat_coeff['stat'] == stat]
    dat_coeff = dat_coeff.rename(index=str, columns={"lag": "window"})

    dat = pd.merge(dat_spi, dat_nass, how='left',
                   left_on=['state', 'year'],
                   right_on=['state', 'year'])

    dat = pd.merge(dat, dat_coeff, how='right',
                   left_on=['state', 'month', 'window', 'county', 'crop'],
                   right_on=['state', 'month', 'window', 'county', 'crop'])

    dat = dat.assign(scpi=(dat.alpha*dat.spi) + (dat.beta*dat.scvi) + dat.gamma)
    dat = dat[dat['year'] < 2018]

    dat = dat.append(manage_current_year(stat), sort=False)

    dat.to_csv("../data_frames/master_scpi.csv")

"""

# returns the spi for a county based on optimal lag period.
def get_matching_spi(dat, state, county, lag, yyyymm):

    if (county not in dat['county_name'].values) or np.isnan(lag):
        return np.nan

    else:
        dat = dat[(dat['state'] == state) &
                  (dat['county_name'] == county) &
                  (dat['window'] == lag) &
                  (dat['date'] == yyyymm)]

        return dat.spi.values[0]


# returns a scvi for a given crop, year and state
def get_corresponding_nass(dat, crop, year, state):

    dat = dat[(dat['state'] == state) &
              (dat['crop'] == crop) &
              (dat['year'] == year)]

    if dat.empty:
        return np.nan
    else:
        return dat.value.values[0]


def calc_county_scpi(dat_spi, dat_nass, yyyymm, crop):

    year = yyyymm.split("-")[0]
    month = yyyymm.split("-")[1]

    boundaries = ["../boundaries/state_boundaries/MT.geojson",
                  "../boundaries/state_boundaries/ID.geojson",
                  "../boundaries/state_boundaries/ND.geojson",
                  "../boundaries/state_boundaries/SD.geojson",
                  "../boundaries/state_boundaries/WY.geojson"]

    if crop == "BARLEY":
        short = "bar"
    elif crop == "WHEAT":
        short = "whe"
    elif crop == "HAY":
        short = "alf"
    out_dict = {}

    for bnd in boundaries:

        state = bnd.split("/")[-1].replace(".geojson", "")

        with open(bnd) as shp:
            data = json.load(shp)

        # just calculating from spi for the time being.
        for feat in data['features']:

            name = feat['properties']['NAME'].lower().replace(" ", "_").replace("&", "and")

            add_name = state + "_" + name
            coeffs = get_best_coef(crop=short, state=state, variable='spi',
                                   county=name, month=int(month))

            spi = get_matching_spi(dat=dat_spi, state=state, county=name,
                                   lag=coeffs['lag'], yyyymm=yyyymm)

            scvi = get_corresponding_nass(dat=dat_nass, crop=crop, year=int(year), state=state)

            if np.isnan(spi):

                new_dict = {'state': state,
                            'county': name,
                            'date': yyyymm,
                            'crop': crop,
                            'alpha': np.nan,
                            'beta': np.nan,
                            'gamma': np.nan,
                            'spi': np.nan,
                            'scvi': np.nan,
                            'scpi': np.nan}

                out_dict[add_name] = new_dict

            else:

                scpi = coeffs['alpha']*spi + coeffs['beta']*scvi + coeffs['gamma']

                # also get the RMSE

                new_dict = {'state': state,
                            'county': name,
                            'date': yyyymm,
                            'crop': crop,
                            'alpha': coeffs['alpha'],
                            'beta': coeffs['beta'],
                            'gamma': coeffs['gamma'],
                            'spi': spi,
                            'scvi': scvi,
                            'scpi': scpi}

                out_dict[add_name] = new_dict

    return pd.DataFrame.from_dict(out_dict, orient='index')


def update_scpi_csv():

    dat_spi = pd.read_csv("../data_frames/spi_out.csv")
    dat_nass = pd.read_csv("../data_frames/.csv", index_col=0)

    crops = ['BARLEY', 'WHEAT', 'HAY']
    all_dates = dat_spi.date.unique()

    dat = pd.read_csv("../data_frames/master_scpi.csv", index_col=0)

    for yyyymm in all_dates:

        for crop in crops:

            if yyyymm not in dat.date.unique():

                print(dat)
                dat = dat.append(calc_county_scpi(dat_nass=dat_nass, dat_spi=dat_spi,
                                                  yyyymm=yyyymm, crop=crop))

    dat.to_csv("../data_frames/master_scpi.csv")

# not sure if this is necessary. Returns a range of dates.
def get_date_range():

    dat = pd.read_csv("../data_frames/master_df.csv", index_col=0)
    dat = dat[dat.state.notnull()]
    dat['date'] = pd.to_datetime(dat['date'], format='%Y-%m-%d')
    dat = dat.sort_values(by=['date'])

    dates = dat['date'].unique()

    start = datetime.datetime.utcfromtimestamp(dates[0].tolist()/1e9).date()
    end = datetime.datetime.utcfromtimestamp(dates[-1].tolist()/1e9).date()

    # taken from stack exchange: https://stackoverflow.com/questions/34898525/generate-list-of-months-between-
    # interval-in-python
    daterange = pd.date_range(str(start), str(end), freq='1M')
    daterange = [d.strftime('%Y-%m') for d in daterange]

    return daterange

# ASK ABOUT WINDOW TYPE
# function that calculates SPI
def calc_spi(dat, start_mo, win):

    spi = SPI()
    spi.set_rolling_window_params(
        span=win,
        window_type='boxcar',
        center=True
    )

    spi.set_distribution_params(dist_type='gam')

    return spi.calculate(dat, starting_month=start_mo)


def apply_all_spi():

    dat = detrend_data().values[0]

    state = dat[0][0]
    county = dat[0][1].lower().replace(" ", "-")
    variable = dat[0][2]

    months = get_date_range()
    win_sizes = range(1, 16)

    # for mon in months:
    #     for win in win_sizes:
    #         start = int(mon.split("-")[-1])
    #         print(calc_spi(dat, start, win))

Returns the coefficient value and optimal lag time based on inputs
def get_best_coef(crop, state, variable, county, month):

    # I am finding lowest RMSE and then selecting corresponding values. Make sure this is correct.
    dat1 = pd.read_csv("../data_frames/coeffs/%s_%s_%s_Allcoeffs_ML.csv" % (crop, state, variable),
                      index_col=0)

    if county not in dat1.index:

        return {"alpha": np.nan,
                "beta": np.nan,
                "gamma": np.nan,
                "lag": np.nan}

    else:

        dat1 = dat1.filter(regex="_month" + str(month) + "_")
        dat1 = dat1.filter(regex="^" + county + "$", axis=0)

        dat = dat1.filter(regex="rmse").T

        lag = dat.idxmin().values[0].split("_")[-1].replace("lag", "")

        alpha = dat1.filter(regex='alpha').filter(regex="_lag" + lag + "$").T.values[0][0]
        beta = dat1.filter(regex='beta').filter(regex="_lag" + lag + "$").T.values[0][0]
        gamma = dat1.filter(regex='gamma').filter(regex="_lag" + lag + "$").T.values[0][0]

        return {"alpha": alpha,
                "beta": beta,
                "gamma": gamma,
                "lag": int(lag)}
"""