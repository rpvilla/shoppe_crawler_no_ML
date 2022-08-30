# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 07:14:15 2022

@author: michaelbr.manuel
"""

import pandas as pd
import os
from scripts.scraper_functions import *
from scripts.scraper import *
import timeit
import json

#START TIME
start = timeit.default_timer()

#INPUT FILE FOR RECRAWLING
filename = os.listdir('./recrawling_input')[0]
df_recrawl = pd.read_excel(f"./recrawling_input/{filename}")
print(df_recrawl)
#DATA DICT TRANSFORMATION
lst_data_dict = recrawl_inputData(df_recrawl)
num_data = len(lst_data_dict)
print(f"TOTAL NUMBER TO BE CRAWLED: {num_data}")

#REGISTER YOUR LOCAL IP ADDRESS IN WHITELIST
LOCAL_IP_ADDRESS = localmachine_IP()
print('LOCAL MACHINE IP ADDRESS : ', LOCAL_IP_ADDRESS)
registerIPAddress(LOCAL_IP_ADDRESS)

#DATE CRAWLED 
today = date.today()
date_crawled = today.strftime("%Y%m%d")

#CREATE OUTPUT FILE DIRECTORY FOR TEMPFILES
createDir = outputDir_recrawl(date_crawled)

#PROXIES 
proxy = get_proxy()
header = get_headers()

#DATA DICT TRANSFORMATION
lst_data_dict = recrawl_inputData(df_recrawl)
num_data = len(lst_data_dict)

input_data_recrawl = []
for data_dict in lst_data_dict:
    data = [data_dict, proxy[1], header[1], createDir[1], createDir[2] , createDir[3]]
    input_data_recrawl.append(data)

print('Start crawling..........')
print(input_data_recrawl)
#SCRAPED SHOPPE
#MULTITHREADING SCRAPING DATA FROM SELLER TO PRODUCT API
recrawl_data = scrapeShoppeData(input_data_recrawl)
fail_to_scrape = recrawl_data[2]
df_fail_to_scrape = pd.DataFrame.from_dict(fail_to_scrape, orient='columns')

try:
    #MERGED THE DATA PER PG/UNIQUE NAME
    df_merge = pd.concat(recrawl_data[1]).reset_index().drop(['index'], axis=1)
    df_merge = df_merge[['date_crawled', 'unique_name', 'cat_0', 'cat_1', 'cat_2', 'shopid',
       'itemid', 'brand', 'item_name', 'item_desc', 'orig_price', 'sale_price',
       'item_price', 'stock', 'historical_sold', 'sold', 'model_itemid',
       'modelid', 'model_name', 'model_orig_price', 'model_sale_price',
       'model_stock', 'model_sold',
       'voucher_discount', 'final_price', 'model_count', 'total_model_sold',
       'model_contribution', 'sales_units', 'item_rating', 'item_rating_count',
       'warranty', 'seller_name', 'seller_rating', 'seller_follower_count',
       'shopee_verified', 'is_preferred_plus_seller', 'is_official_shop',
       'show_original_guarantee', 'is_authentic', 'url', 'country',
       'product group']]
    
    df_merge.to_excel(f"./output/{date_crawled}-recrawl/recrawled_data_{date_crawled}.xlsx", index = False)
except Exception as e:
    print('ERROR AT MERGING: ', e)
    pass

#UNREGISTER YOUR LOCAL IP ADDRESS IN WHITELIST
unregisterIPAddress(LOCAL_IP_ADDRESS)

#SAVE THE FAILED TO SCRAPED PRODUCT
df_final_merge = pd.concat(df_fail_to_scrape).reset_index().drop(['index'], axis=1)
df_final_merge.to_excel(f"./output/{date_crawled}/PROD-FAIL-TO-SCRAPE {date_crawled}.xlsx", index = False)   
print('DONE CRAWLING....')

#RUNTIME
stop = timeit.default_timer()
runtime = stop - start
dict_timelapse = {f"RUNTIME-recrawling for {num_data} OF ITEM" : runtime}
with open("./runtime/runtime-recrawling.txt", mode='w', encoding='UTF-8', errors='strict', buffering=1) as f:
    f.write(str(dict_timelapse))

