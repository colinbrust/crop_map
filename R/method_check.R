library(magrittr)

py_img_ppt <- "./mean_images/precip_1980-09-30.tif" %>%
  raster::raster() 

py_img_pet <- "./mean_images/pet_1980-09-30.tif" %>%
  raster::raster() 


py_img_ppt[py_img_ppt < 0] <- NA
py_img_pet[py_img_pet < 0] <- NA


check_agg <- list.files("./raw_images", pattern = "precip", full.names = T) %>%
  lapply(raster::raster) %>%
  raster::stack() %>%
  sum()

check_agg_et <- list.files("./raw_images", pattern = "pet", full.names = T) %>%
  lapply(raster::raster) %>%
  raster::stack() %>%
  sum()

test <- tibble::tibble(ppt_agg = py_img_ppt[],
                       pet_agg = py_img_pet[],
                       r_agg = check_agg[],
                       r_agg_pet = check_agg_et[]) %>%
  dplyr::mutate(difference_ppt = ppt_agg - r_agg,
                difference_pet = pet_agg - r_agg_pet) %>%
  dplyr::filter(!is.na(difference_ppt))

print(max(test$difference_pet))
