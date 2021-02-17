library(magrittr)

test <- list.files("./mean_images", full.names = T, pattern = "precip")[1:5] %>%
  lapply(raster::raster)

val1 <- test[[1]][]
val2 <- test[[2]][]
val3 <- test[[3]][]
val4 <- test[[4]][]
val5 <- test[[5]][]

df <- tibble::tibble(first = val1, second = val2, third = val3, fourth = val4, fifth = val5) %>%
  dplyr::filter(!is.na(first)) %>%
  dplyr::mutate(test = first + second)
