# -*- coding: utf-8 -*-
"""
Created on Wed Aug 24 09:26:32 2022

@author: michaelbr.manuel
"""
#DEPENDENCIES
import os
import pandas as pd
import time
import re
import locale
from bs4 import BeautifulSoup as bs
import datetime 
import concurrent.futures
from time import perf_counter
from selenium.webdriver.common.keys import Keys
import requests
import json
#Install packages
from seleniumwire import webdriver
from seleniumwire.undetected_chromedriver import Chrome, ChromeOptions
import uuid
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from datetime import date
from urllib.request import urlopen
from .scraper import *


############################ FUNCTION FOR GETTING LOCAL IP ADDRESS ###########################
def localmachine_IP():
    ip = requests.get('https://api.ipify.org', verify=False).content.decode('utf8')
    return ip

############################ FUNCTION FOR REGISTER YOUR IP ADDRESS TO THE WHITELIST ###########################
def registerIPAddress(IP_ADDRESS):
    for i in range(20):
        try:
            base_url_proxy = 'https://api.proxycrawl.com/proxy/whitelist_ips?token=ZjYgC1daKwZNtRlfmkB0HA&ip={}'.format(IP_ADDRESS)
            register = requests.post(base_url_proxy)
            status = json.loads(register.content)['status']
            print(f"Done Register the IP_ADDRESS : {IP_ADDRESS} to the whitelist....")
            break
        except:
            time.sleep(2)
            pass
            
        
############################ FUNCTION FOR UNREGISTER YOUR IP ADDRESS TO THE WHITELIST ###########################
def unregisterIPAddress(IP_ADDRESS):
    for i in range(20):
        try:
            base_url_proxy = 'https://api.proxycrawl.com/proxy/whitelist_ips?token=ZjYgC1daKwZNtRlfmkB0HA&ip={}'.format(IP_ADDRESS)
            delete_ip_address = requests.delete(base_url_proxy)
            status = json.loads(delete_ip_address.content)['status']
            print(f"Done Unregister the IP_ADDRESS : {IP_ADDRESS} to the whitelist....")
            break
        except:
            time.sleep(2)
            pass
     

############################ FUNCTION FOR CALCULATING AUTHENTICITY BASED ON OLD CRAWLER ###########################
def get_authenticity(df):
    authentic = "authentic"
    likely_fake = "likely fake"
    need_confirm = "need confirmation"
    
    df["is_authentic"] = need_confirm

    df["warranty"] = df["warranty"].astype(str)
    df.loc[df["warranty"].str.lower() == "no warranty", "is_authentic"] = likely_fake
    df.loc[df["seller_rating"] < 3.0, "is_authentic"] = likely_fake
    df.loc[(df["item_rating"] < 3.0) & (df["item_rating_count"] > 10), "is_authentic"] = likely_fake

    df.loc[df["shopee_verified"].notna() & df["shopee_verified"], "is_authentic"] = authentic
    df.loc[df["is_official_shop"].notna() & df["is_official_shop"], "is_authentic"] = authentic
    return df

############################ FUNCTION FOR SCRAPING THE VOUCHER DISCOUNT ###########################      
def voucherDiscount(voucherDict):
    if len(voucherDict) == 0:
        return ''
    else:
        lst_voucher = []
        for i in range(len(voucherDict)):
            voucher = voucherDict[1]['discount_value']/100000
            lst_voucher.append(voucher)
        return sum(lst_voucher)

############################ FUNCTION FOR SCRAPING THE ITEM WARRANTY ###########################    
def modelWarranty(dict_attribute):
    for i in range(len(dict_attribute)):
        name = dict_attribute[i]['name']
        if name == 'Warranty Duration':
            try:
                return dict_attribute[i]['value']
            except:
                return ''
        else:
            pass
    return ''

############################ FUNCTION FOR SCRAPING THE ITEM MODEL CONTRIBUTION ###########################  
def modelContribution(model_stock, stock):
    return model_stock/stock

############################ FUNCTION FOR SCRAPING THE ITEM MODEL SALES UNITS ###########################  
def modelSalesUnits(contri, sold):
    return round(contri*sold)

############################# BACK-CONNECT PROXY ############################### 

def get_proxy():
    while True:
        try:
            backconnet_api = 'https://api.proxycrawl.com/proxy/static?token=ZjYgC1daKwZNtRlfmkB0HA'
            proxy = requests.get(backconnet_api).json()
            print(proxy)
            
            hostname = proxy['host']
            port = proxy['port']
            
            proxy_request = {
                'http':f'http://{hostname}:{port}',
                'https':f'http://{hostname}:{port}',
            }
            
            proxy_selenium = '{}:{}'.format(hostname, port)
            return proxy_request, proxy_selenium
            break
        except:
            pass
            time.sleep(60)
    

def get_headers():
    while True:
        try:
            handler = urlopen('https://api.proxycrawl.com/user_agents?token=ZjYgC1daKwZNtRlfmkB0HA')
            agent_raw = handler.read().decode('utf-8')
            json_acceptable_string = agent_raw.replace("'", "\"")
            
            agent_dict = json.loads(json_acceptable_string)
            print(agent_dict)
            agent = agent_dict['agents'][0]
            header_request = {'User-Agent': agent}
            header_selenium = 'User-Agent={}'.format(agent)
            return header_request, header_selenium
            break
        except:
            print('trying to fetching header in proxy crawler...')
            pass
            time.sleep(60)

############################# FUNCTION FOR CREATING FOLDER FOR THE TEMPFOLDER DIRECTORY #############################
def outputDir(date_crawled):
    os.makedirs('./output/{}'.format(date_crawled))
    #MAKE DIRECTORY FOR ITEM-URL TEMPFILES
    os.makedirs('./output/{}/item_url'.format(date_crawled))
    item_url_directory = './output/{}/item_url'.format(date_crawled)
    #MAKE DIRECTORY FOR PRODUCT DATA TEMPFILES
    os.makedirs('./output/{}/prod_data'.format(date_crawled))
    product_data_directory = './output/{}/prod_data'.format(date_crawled)
    #print('DONE CREATING TEMP FILES....')
    #MAKE DIRECTORY FOR SELLER DATA TEMPFILES
    os.makedirs('./output/{}/seller_data'.format(date_crawled))
    seller_data_directory = './output/{}/seller_data'.format(date_crawled)
    #print('DONE CREATING TEMP FILES....')
    #MAKE DIRECTORY FOR DF FILES DATA TEMPFILES
    os.makedirs('./output/{}/excelfiles'.format(date_crawled))
    excel_data_directory = './output/{}/excelfiles'.format(date_crawled)
    print('DONE CREATING TEMP FILES....')
    return item_url_directory , product_data_directory, seller_data_directory, excel_data_directory
        
############################# FUNCTION FOR SAVING DATA TO THE TEMPFOLDER #############################
def saveTempfile(dict_data, savedir, typeData, filename):
    with open('{}/{}.json'.format(savedir,filename), 'w') as outfile:
        json.dump(dict_data, outfile)
        print('DONE SAVING {}'.format(typeData))

############################# FUNCTION FOR SCRAPING SHOPPE FROM SELLER TO PROD API #############################
def crawlProdData(crawl_nav, proxy, header, shopDir, prodDir, excelDir):
    shop_data = scrapeSellerInfo(crawl_nav, proxy, header, shopDir)
    time.sleep(2)
    prod_data = scrapeProdPage(shop_data[1][0], shop_data[1][1], shop_data[1][2], shop_data[1][3], prodDir, excelDir)
    return prod_data[0], prod_data[1]

########################### MULTITHREADING THE SCRAPING SHOPPE ##########################
def scrapeShoppeData(scrape_nav):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = {executor.submit(crawlProdData, input_[0], 
                                    input_[1], input_[2],input_[3], 
                                    input_[4],input_[5]): input_ 
                                    for input_ in scrape_nav}
        prod_data = []
        df_data = []
        for f in concurrent.futures.as_completed(results):
            prod_data.append(f.result()[0])
            df_data.append(f.result()[1])
            
    return prod_data, df_data




















