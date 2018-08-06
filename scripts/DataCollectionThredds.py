
from __future__ import print_function
import urllib as urllib2
import argparse
import dateutil.parser
import fiona
import sys
import subprocess

'''

Use this command to use the proper anaconda environment

source activate crop_map

Use this command to download data

python DataCollectionThredds.py -de 2018-06-10 -ds 2018-06-08 -aprecip bbox -nb 49 -sb 47 -eb -112 -wb -114
'''

def chunk_report(bytes_so_far):
    sys.stdout.write("Downloaded %d bytes)\r" % bytes_so_far)


def copyfileobj(fsrc, fdst, callback, length=4*1024):
    copied = 0
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        copied += len(buf)
        callback(copied)


class DataCollectionThredds:

    def __init__(self, base_url, date_start, date_end, attributes, bounds, flip=False):
        self.base_url = base_url
        self.date_start = dateutil.parser.parse(date_start) #todo error handling
        self.date_end = dateutil.parser.parse(date_end) #todo error handling
        self.attributes = attributes
        self.bounds = bounds
        self.flip = flip

    def build_url_filename(self, local_path, attribute):

        filename = local_path + attribute + '_F' + self.date_start.strftime('%Y-%m-%d') + '_T' + self.date_end.strftime('%Y-%m-%d') + '.nc'
        result = switch(attribute)

        start = self.date_start.strftime('%Y-%m-%dT%H%%3A%M%%3A%SZ')
        end = self.date_end.strftime('%Y-%m-%dT%H%%3A%M%%3A%SZ')

        url = self.base_url + '/agg_met_' + result.get('abbreviation') + '_1979_CurrentYear_CONUS.nc?' + result.get('variable') \
            + '&north=' + str(self.bounds.get('north')) + '&west=' + str(self.bounds.get('west')) \
            + '&east=' + str(self.bounds.get('east')) + '&south=' + str(self.bounds.get('south')) \
            + '&disableProjSubset=on&horizStride=1' + '&time_start=' + start + '&time_end=' + end \
            + '&timeStride=1&addLatLon=true&accept=netcdf4'

        return url, filename

    def download(self, local_path):

        for attribute in self.attributes:

            url, filename = self.build_url_filename(local_path, attribute)
            try:
                response = urllib2.urlopen(url)
                #chunk_read(response, report_hook=chunk_report)
                with open(filename, 'wb') as out_file:
                    copyfileobj(response, out_file, chunk_report)

            except urllib2.URLError, err:
                print('error ', err.reason)
            finally:
                try:
                    response.close()
                except NameError:
                    pass

            if self.flip:
                cmd = 'ncpdq -a lat,lon --ovr ' + filename + " " + filename
                try:
                    subprocess.check_call(cmd, shell=True)
                except subprocess.CalledProcessError as e:
                    print(e.args)
                    print("WARNING: couldnt swap coordinate of file " + filename +
                          " with exception error " + e.message)




def switch(x):
    return {
        'precip': {'abbreviation': 'pr', 'variable': 'var=precipitation_amount'},
        'tempmax': {'abbreviation': 'tmmx', 'variable': 'var=daily_maximum_temperature'},
        'tempmin': {'abbreviation': 'tmmn', 'variable': 'var=daily_minimum_temperature'},
        'pet':    {'abbreviation': 'pet', 'variable': 'var=daily_mean_reference_evapotranspiration_grass'}
    }.get(x, None)


def build_request(inp):

    if inp.BBoxType == 'vectorFile':
        with fiona.open(inp.filename, 'r') as src:
            bnds = src.bounds

        bounds = {
            'north': round(bnds[3]) + 1,
            'south': round(bnds[1]) - 1,
            'east': round(bnds[2]) + 1,
            'west': round(bnds[0]) - 1
        }
    else:
        bounds = {
            'north': inp.north_bound,
            'south': inp.south_bound,
            'east': inp.east_bound,
            'west': inp.west_bound
            }
    dc = DataCollectionThredds(inp.base_url, inp.date_start, inp.date_end, set(inp.attributes), bounds, inp.flip)

    dc.download(inp.output_folder)


if __name__ == "__main__":
    """
    http://thredds.northwestknowledge.net:8080/thredds/ncss/agg_met_pr_1979_CurrentYear_CONUS.nc?disableLLSubset=on&disableProjSubset=on&horizStride=1&time_start=1979-01-01T00%3A00%3A00Z&time_end=2017-01-01T00%3A00%3A00Z&timeStride=1&addLatLon=true&accept=netcdf
    """
    parser = argparse.ArgumentParser(prog='DataCollectionThredds')

    parser.add_argument('-u',
                        default='http://thredds.northwestknowledge.net:8080/thredds/ncss',
                        dest='base_url', type=str,
                        help='base url of NetCDF data source. '
                             'Defaults to the Aggregated NKN Thredds server')
    parser.add_argument('-de', dest='date_end', type=str, help='date end yyy-mm-dd', required=True)
    parser.add_argument('-ds', dest='date_start', type=str, help='date start yyy-mm-dd', required=True)
    parser.add_argument('-a', dest='attributes', nargs='+', help='variables: precip, tempmax or tempmin', required=True)
    parser.add_argument('-of', default='./', dest='output_folder', type=str,
                        help='output folder. Defaults to current folder')
    parser.add_argument('--flip', dest='flip', action='store_true',
                        help='flip netcdf file coordinates (Needed for the NKN REACCH [metdata] dataset)')


    sp = parser.add_subparsers(dest='BBoxType')
    groupa = sp.add_parser('bbox', help='Bounding Box coordinates')
    groupa.add_argument('-nb', dest='north_bound', type=float, help='north bound', required=True)
    groupa.add_argument('-sb', dest='south_bound', type=float, help='south bound', required=True)
    groupa.add_argument('-eb', dest='east_bound', type=float, help='east bound', required=True)
    groupa.add_argument('-wb', dest='west_bound', type=float, help='west bound', required=True)

    groupb = sp.add_parser('vectorFile', help='Bounding Box coordinates from vector file')
    groupb.add_argument('filename', type=str, help='vector File with area to be covered by climate data')

    #args = parser.parse_args("-ds 2009-08-30 -de 2009-09-1 -aprecip vectorFile ../tests/test_data/mt_network.shp".split(" "))
    args = parser.parse_args()

    print(args)
    # build_request(args)

    # To rotate the netcdfs from the metdata dataset use the line below in the command line
    # after installing cdo. To do this use 'conda install cdo -c conda-forge'
    #ncpdq -a lat,lon precip_F2009-08-10_T2009-09-01.nc precip_F2009-08-10_T2009-09-01b.nc
