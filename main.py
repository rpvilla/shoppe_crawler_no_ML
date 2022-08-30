# -*- coding: utf-8 -*-
"""
Created on Wed Aug 24 09:24:52 2022

@author: michaelbr.manuel
"""
from scripts.scraper_functions import *
from scripts.scraper import *
import pandas as pd
import os
import timeit
import json

#START TIME
start = timeit.default_timer()

#IMPORT INPUT FILES
INPUT_FILENAME = os.listdir('./input_data')
df_input = pd.read_excel('./input_data/{}'.format(INPUT_FILENAME[0]), sheet_name='main')

#SORT THE URL THAT NEEDED TO BE CRAWLED
df_input = df_input[df_input['to crawl']== 'YES'].reset_index()
print('lIST OF UNIQUE_NAME THAT NEED TO BE CRAWLED...')
for u in df_input['unique name'].tolist():
    print(u)

#DATE CRAWLED 
today = date.today()
date_crawled = today.strftime("%Y%m%d")

#CREATE OUTPUT FILE DIRECTORY FOR TEMPFILES
createDir = outputDir(date_crawled)

#REGISTER YOUR LOCAL IP ADDRESS IN WHITELIST
LOCAL_IP_ADDRESS = localmachine_IP()
print('LOCAL MACHINE IP ADDRESS : ', LOCAL_IP_ADDRESS)
registerIPAddress(LOCAL_IP_ADDRESS)


#PROXIES 
proxy = get_proxy()
header = get_headers()

print('Start crawling..........')
#SCRAPED SHOPPE
df_scraped_data = []
df_fail_scraped_data = []
for i in range(len(df_input['product group'])):
    start_pg = timeit.default_timer()
    url = df_input['url'][i]
    pg = df_input['product group'][i]
    unique_name = df_input['unique name'][i]
    page_num = df_input['num pages'][i]
    country = df_input['country'][i]
    folder_lst = ['item_url', 'prod_data', 'seller_data', 'excelfiles', 'merged_files']
    #MAKE DIRECTORY FOR PRODUCT DATA 
    for f in folder_lst:
        os.makedirs('./output/{}/{}/{}'.format(date_crawled, f, unique_name))
        
    #CRAWL DATA IN THE NAVIGATION PAGE
    data = ShoppeCrawler(url, pg, unique_name, page_num, proxy[1], header[1], country, createDir[0], createDir[1], createDir[2] , createDir[3])
    crawl_nav = ShoppeCrawler.scrapeNAVPAGE(data)
    
    #MULTITHREADING SCRAPING DATA FROM SELLER TO PRODUCT API
    seller_data = scrapeShoppeData(crawl_nav[1])
    fail_to_scrape = seller_data[2]
    df_fail_to_scrape = pd.DataFrame.from_dict(fail_to_scrape, orient='columns')
    df_fail_scraped_data.append(df_fail_to_scrape)
    

    
    try:
        #MERGED THE DATA PER PG/UNIQUE NAME
        df_merge = pd.concat(seller_data[1]).reset_index().drop(['index'], axis=1)
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
        
        df_scraped_data.append(df_merge)
        
        df_merge.to_excel(f"./output/{date_crawled}/merged_files/{pg} ({unique_name})-{i}.xlsx", index = False)
    except Exception as e:
        print('ERROR AT MERGING: ', e)
        pass
    
    #RUNTIME
    stop_pg = timeit.default_timer()
    runtime_pg = stop_pg - start_pg
    dict_timelapse = {'RUNTIME' : runtime_pg}
    with open(f"./runtime/{pg}-runtime.txt", mode='w', encoding='UTF-8', errors='strict', buffering=1) as f:
        f.write(str(dict_timelapse))
    
    i += 1

#UNREGISTER YOUR LOCAL IP ADDRESS IN WHITELIST
unregisterIPAddress(LOCAL_IP_ADDRESS)

#SAVE THE FAILED TO SCRAPED PRODUCT
df_final_merge = pd.concat(df_fail_scraped_data).reset_index().drop(['index'], axis=1)
df_final_merge.to_excel(f"./output/{date_crawled}/PROD-FAIL-TO-SCRAPE {date_crawled}.xlsx", index = False)

#MERGING ALL DATA THAT HAS BEEN CRAWLED IN ONE EXCEL FILE
df_final_merge = pd.concat(df_scraped_data).reset_index().drop(['index'], axis=1)
df_final_merge.to_excel(f"./output/{date_crawled}/{date_crawled}.xlsx", index = False)
print('DONE CRAWLING....')

#RUNTIME
stop = timeit.default_timer()
runtime = stop - start
dict_timelapse = {'RUNTIME' : runtime}
with open("./runtime/TOTAL-runtime.txt", mode='w', encoding='UTF-8', errors='strict', buffering=1) as f:
    f.write(str(dict_timelapse))












