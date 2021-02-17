#!/bin/bash

cd /home/colin.brust/workspace/scpi_map/scripts
conda run -n crop_map python -c 'import DataDownload; DataDownload.save_scvi()'
echo scvi saved
conda run -n crop_map python -c 'import DataDownload; DataDownload.save_nass_production()'
echo nass production saved
conda run -n crop_map python -c 'import DataDownload; DataDownload.update_csv()'
echo updated master csv
conda run -n r_new python -c 'import DataDownload; DataDownload.run_r_spi()'
echo SPI calculated in R
conda run -n crop_map python -c 'import DataDownload; DataDownload.save_eddi()'
echo EDDI saved
conda run -n r_new python -c 'import DataDownload; DataDownload.run_r_scvi()'
echo SCVI calculated in R
conda run -n r_new python -c 'import DataDownload; DataDownload.run_r_prod()'
echo Production calculated in R
conda run -n crop_map python -c 'import DataDownload; DataDownload.calc_scpi("spi")'
echo SCPI calculated for SPI
conda run -n crop_map python -c 'import DataDownload; DataDownload.calc_scpi("eddi")'
echo SCPI calculated for EDDI
conda run -n r_new python -c 'import DataDownload; DataDownload.run_r_graph()'
echo Generated R popup graphs
conda run -n r_new python -c 'import DataDownload; DataDownload.run_r_mouse()'
echo Generated R mouseover icons
conda run -n r_new python -c 'import DataDownload; DataDownload.run_r_thin()'
echo Thinned final dataframe

