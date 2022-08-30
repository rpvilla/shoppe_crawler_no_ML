# -*- coding: utf-8 -*-
"""
Created on Wed Aug 24 09:25:19 2022

@author: michaelbr.manuel
"""
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
from .scraper_functions import *
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
import requests


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

############################# FUNCTION TRANSFORMATION THE DATAFRAME DATA TO DICT #############################
def recrawl_inputData(df_recrawl):
    col = df_recrawl.columns.values.tolist()
    lst_dict_data = []
    for i in range(len(df_recrawl['date_crawled'])):
        dict_data = {}
        for c in col:
            dict_data[c] = df_recrawl[c][i]
        i+=1
        lst_dict_data.append(dict_data)
    return lst_dict_data


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

############################# FUNCTION FOR CREATING FOLDER FOR THE TEMPFOLDER DIRECTORY #############################
def outputDir_recrawl(date_crawled):
    os.makedirs('./output/{}-recrawl'.format(date_crawled))
    #MAKE DIRECTORY FOR ITEM-URL TEMPFILES
    os.makedirs('./output/{}-recrawl/item_url'.format(date_crawled))
    item_url_directory = './output/{}-recrawl/item_url'.format(date_crawled)
    #MAKE DIRECTORY FOR PRODUCT DATA TEMPFILES
    os.makedirs('./output/{}-recrawl/prod_data'.format(date_crawled))
    product_data_directory = './output/{}-recrawl/prod_data'.format(date_crawled)
    #print('DONE CREATING TEMP FILES....')
    #MAKE DIRECTORY FOR SELLER DATA TEMPFILES
    os.makedirs('./output/{}-recrawl/seller_data'.format(date_crawled))
    seller_data_directory = './output/{}-recrawl/seller_data'.format(date_crawled)
    #print('DONE CREATING TEMP FILES....')
    #MAKE DIRECTORY FOR DF FILES DATA TEMPFILES
    os.makedirs('./output/{}-recrawl/excelfiles'.format(date_crawled))
    excel_data_directory = './output/{}-recrawl/excelfiles'.format(date_crawled)
    print('DONE CREATING TEMP FILES....')
    return item_url_directory , product_data_directory, seller_data_directory, excel_data_directory
        
############################# FUNCTION FOR SAVING DATA TO THE TEMPFOLDER #############################
def saveTempfile(dict_data, savedir, typeData, filename):
    with open('{}/{}.json'.format(savedir,filename), 'w') as outfile:
        json.dump(dict_data, outfile, default=str)
        print('DONE SAVING {}'.format(typeData))

############################# FUNCTION FOR SCRAPING SHOPPE FROM SELLER TO PROD API #############################
def crawlProdData(crawl_nav, proxy, header, shopDir, prodDir, excelDir):
    try:
        shop_data = scrapeSellerInfo(crawl_nav, proxy, header, shopDir)
        time.sleep(2)
        prod_data = scrapeProdPage(shop_data[1][0], shop_data[1][1], shop_data[1][2], shop_data[1][3], prodDir, excelDir)
        return prod_data[0], prod_data[1]
    except:
        return crawl_nav

########################### MULTITHREADING THE SCRAPING SHOPPE ##########################
def scrapeShoppeData(scrape_nav):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = {executor.submit(crawlProdData, input_[0], 
                                    input_[1], input_[2],input_[3], 
                                    input_[4],input_[5]): input_ 
                                    for input_ in scrape_nav}
        prod_data = []
        df_data = []
        list_prod_fail = []
        for f in concurrent.futures.as_completed(results):
            try:
                prod_data.append(f.result()[0])
                df_data.append(f.result()[1])
            except:
                list_prod_fail.append(f.result())
                
            
    return prod_data, df_data, list_prod_fail


############################ FUNCTION FOR USING SELENIUM FOR OPENING NAVC PAGE ###########################
def openChrome(url, proxy, header):
    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--proxy-server=%s' % proxy)
    chrome_options.add_argument(header)
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    driver.get(url)
    driver.maximize_window()
    #driver.refresh()
    return driver

############################ FUNCTION FOR USING SELENIUM FOR OPENING API PAGE ###########################
def getJSON_API_SELENIUM(url, proxy, header):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--proxy-server=%s' % proxy)
    chrome_options.add_argument(header)
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    driver.get(url)
    time.sleep(0.2)
    i = 0
    for i in range(5):
        try:
            jsonAPI = json.loads(bs(driver.page_source, 'lxml').text)
            x = jsonAPI['data']
            return jsonAPI
            break
        except:
            if i % 2 == 0:
                driver.refresh()
                time.sleep(0.25)
            else:
                driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
                driver.get(url)
                time.sleep(0.2)
                
############################ FUNCTION FOR USING REQUESTS FOR OPENING API PAGE ###########################
def getJSON_API_REQUESTS(url):
    for i in range(5):
        r = requests.get(url, verify = False)
        try:
            try:
                soup_api = bs(r.content, 'lxml')
                api_dict = soup_api.p.text
                json_api = json.loads(api_dict)
                api = json_api['data']
                return json_api
                print(' ')
                print(api)
                print('====================')
                break
            except:
                json_api = json.loads(r.content)
                api = json_api['data']
                return json_api
                print(' ')
                print(api)
                print('====================')
                break
        except:
            time.sleep(3)
            pass        


#################################### CLASS FOR SCRAPING THE NAVIGATION PAGE ####################################
class ShoppeCrawler(object):
    def __init__(self, url, pg, unique_name, num_page, proxy, header, country, outputDir, shopDir, prodDir, excelDir):
        self.url = url
        self.pg = pg
        self.proxy = proxy
        self.header = header
        self.num_page = num_page
        self.unique_name = unique_name
        self.country = country
        self.outputDir = outputDir
        self.shopDir = shopDir
        self.prodDir = prodDir
        self.excelDir = excelDir
        
    def scrapeNAVPAGE(self):
        driver_nav = openChrome(self.url, self.proxy, self.header)
        self.all_navITEM = []
        self.input_data = []
        for i in range(self.num_page):
            try:
                if i > 0:
                    url_new = '{}&page={}'.format(self.url, i)
                    driver_nav.get(url_new)
                    print('GO TO PAGE: {}'.format(i+1))
                    time.sleep(10)
                else:
                    pass
                #GO TO THE BOTTOM OF THE WEBPAGE
                for k in range(35):
                    try:
                        time.sleep(0.5) 
                        driver_nav.find_element_by_xpath('//body').send_keys(Keys.PAGE_DOWN)
                    except:
                        pass
                soup = bs(driver_nav.page_source, 'lxml')
                lst_navdata = []
                lst_data_input = []
                for data in soup.findAll('script', type='application/ld+json'):
                    try:
                        item_json = json.loads(data.string)
                        dict_data = {}
                        today = date.today()
                        date_crawled = today.strftime("%Y%m%d")
                        dict_data['date_crawled'] = date_crawled
                        dict_data['item_name'] = item_json['name']
                        dict_data['url'] = item_json['url']
                        dict_data['shopid'] = item_json['url'].split('.')[-2]
                        dict_data['itemid'] = item_json['productID']
                        dict_data['model_itemid'] = item_json['productID']
                        try:
                            dict_data['sale_price'] = float(item_json['offers']['lowPrice'])
                            dict_data['item_price'] = float(item_json['offers']['lowPrice'])
                            dict_data['high_price'] = float(item_json['offers']['highPrice'])
                        except:
                            dict_data['sale_price'] = float(item_json['offers']['price'])
                            dict_data['item_price'] = float(item_json['offers']['price'])
                            dict_data['high_price'] = float(item_json['offers']['price'])
                        dict_data['brand'] = item_json['brand']
                        dict_data['item_rating'] = float(item_json['aggregateRating']['ratingValue'])
                        dict_data['item_rating_count'] = float(item_json['aggregateRating']['ratingCount'])
                        dict_data['product group'] = self.pg
                        dict_data['unique_name'] = self.unique_name
                        dict_data['country'] = self.country
                        lst_navdata.append(dict_data)
                        data_input = [dict_data, self.proxy, self.header, self.shopDir, self.prodDir, self.excelDir]
                        lst_data_input.append(data_input)
                    except:
                        pass
                #time.sleep(5)
                if lst_navdata == []:
                    j = 0
                    for j in range(4):
                        if j == 4:
                            break
                        else:
                            j+=1
                            pass
                self.all_navITEM = self.all_navITEM + lst_navdata
                #SAVE THE DICTIONARY DATA ON NAVIGATION PAGE TO THE TEMPFILE FOLDER
                comment = '{} ({}) - page#: {} TO THE TEMPFILE DIRECTORY....'.format(self.pg, self.unique_name,i+1)
                filename = '{} ({})-{}-page#{}'.format(self.pg, self.unique_name, date_crawled, i+1)
                saveTempfile(lst_navdata, '{}/{}'.format(self.outputDir, self.unique_name), comment, filename)
                self.input_data = self.input_data  + lst_data_input
                
                print('PAGE NUMBER: ', i+1)
                print(lst_navdata)
                print('=========')
                print(' ')
                i+=1
            #INPUT FOR THE ML BINARY FILE
            except Exception as e:
                #print(url_new)
                print(e)
                break
            #STORE ALL THE 
            
        return self.all_navITEM, self.input_data

#################################### FUNCTION FOR SCRAPING THE SELLER API ####################################
def scrapeSellerInfo(data_dict, proxy, header, outputDir):
    #PRODUCT URL IN API
    seller_dict = {}
    seller_dict.update(data_dict)
    website_domain = data_dict['url'].split('/')[2]
    seller_url = 'https://{}/api/v4/product/get_shop_info?shopid={}'.format(website_domain, data_dict['shopid'])
    """THIS IS PART WHERE USING REQUEST FOR REQUESTING A RESPONSE IN API WITH NO PROXY"""
    json_api = getJSON_API_REQUESTS(seller_url)
    """THIS IS PART WHERE USING REQUEST FOR REQUESTING A RESPONSE IN API WITH NO PROXY"""
    #json_api = getJSON_API_SELENIUM(seller_url, proxy, header)
    try:
        #SELLER NAME
        seller_dict['seller_name'] = json_api['data']['account']['username']
        #SELLER RATING
        seller_dict['seller_rating'] = json_api['data']['rating_star']
        #SELLER FOLLOWER COUNT
        seller_dict['seller_follower_count'] = json_api['data']['follower_count']
        #SHOPPE VERIFIED
        try:
            seller_dict['shopee_verified'] = json_api['data']['is_shopee_verified']
        except:
            seller_dict['shopee_verified'] = None
        #SHOPPE IS PREFERRED PLUS SELLER
        seller_dict['is_preferred_plus_seller'] = json_api['data']['is_preferred_plus_seller']
        #SHOPPE IS OFFICIAL SHOP
        seller_dict['is_official_shop'] = json_api['data']['is_official_shop']
        #SAVE THE DICTIONARY DATA ON SELLER API TO THE TEMPFILE FOLDER
        try:
            comment = '{} ({}) - itemid: {} TO THE TEMPFILE DIRECTORY....'.format(seller_dict['product group'], seller_dict['unique_name'], seller_dict['itemid'])
            filename = '{} ({})-{}-{}'.format(seller_dict['product group'], seller_dict['unique_name'], seller_dict['itemid'], seller_dict['date_crawled'])
            saveTempfile(seller_dict, '{}/{}'.format(outputDir, seller_dict['unique_name']), comment, filename)
        except:
            comment = '{} ({}) - itemid: {} TO THE TEMPFILE DIRECTORY....'.format(seller_dict['product group'], seller_dict['unique_name'], seller_dict['itemid'])
            filename = '{} ({})-{}-{}'.format(seller_dict['product group'], seller_dict['unique_name'], seller_dict['itemid'], seller_dict['date_crawled'])
            saveTempfile(seller_dict, outputDir, comment, filename)
        output = [data_dict, proxy, header, seller_dict]
        #print(seller_dict)
        return seller_dict, output
    except Exception as e:
        print(json_api)
        print('ERROR AT THE SELLER PAGE API: ', seller_url)
        print('ERROR: ', e)

#################################### FUNCTION FOR SCRAPING THE PRODUCT API ####################################
def scrapeProdPage(data_dict, proxy, header, shop_data_dict, outputDir, df_outputDir):
    #PRODUCT URL IN API
    website_domain = data_dict['url'].split('/')[2]
    prod_url = 'https://{}/api/v4/item/get?itemid={}&shopid={}'.format(website_domain, data_dict['itemid'], data_dict['shopid'])
    """THIS IS PART WHERE USING REQUEST FOR REQUESTING A RESPONSE IN API WITH NO PROXY"""
    json_api = getJSON_API_REQUESTS(prod_url)
    """THIS IS PART WHERE USING REQUEST FOR REQUESTING A RESPONSE IN API WITH NO PROXY"""
    #json_api = getJSON_API_SELENIUM(prod_url, proxy, header)
    try:
        #ITEM DESCRIPTION
        try:
            item_desc = json_api['data']['description']
        except:
            item_desc = None
        #ORIGINAL PRICE
        orig_price = json_api['data']['price_before_discount']/100000
        #TOTAL STOCK OF AN ITEM
        stock = json_api['data']['stock']
        #HISTORICAL SOLD
        historical_sold = json_api['data']['historical_sold']
        #TOTAL SOLD
        sold = json_api['data']['sold']
        #CATEGORIES
        cat_lst = []
        for i in range(3):
            try:
               cat_lst.append(json_api['data']['categories'][i]['display_name'])
               i+=1
            except:
                cat_lst.append('')
        #CHECK HOW MANY VARIANT THE ITEM HAVE
        num_variant = len(json_api['data']['tier_variations'][0]['options'])
        list_variant_data = [] #THIS IS THE TOTAL DATA FOR EACH VARIANT MODEL OF AN ITEM
        i = 0
        for i in range(num_variant):
            dict_variant = {}
            #APPEND ALL THE CATEGORIES DATA OF EACH ITEM IN DICT_VARIANT
            dict_variant['cat_0'] = cat_lst[0]
            dict_variant['cat_1'] = cat_lst[1]
            dict_variant['cat_2'] = cat_lst[2]
            dict_variant['modelid'] = json_api['data']['models'][i]['modelid'] 
            #APPEND ALL THE DICTIONARY DATA OF EACH ITEM
            #dict_variant.update(data_dict)
            #APPEND ALL THE DICTIONARY DATA OF SELLER
            dict_variant.update(shop_data_dict)
            #APPEND THE ITEM DESCRIPTION TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['item_desc'] = item_desc
            try:
            #APPEND THE ORIGINAL PRICE TO THE DICTIONARY DATA OF EACH ITEM
                dict_variant['orig_price'] = orig_price
            except:
                dict_variant['orig_price'] = None
            #APPEND THE TOTAL STOCK TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['stock'] = stock
            #APPEND THE HISTORICAL SOLD TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['historical_sold'] = historical_sold
            #APPEND THE TOTAL SOLD TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['sold'] = sold
            #APPEND THE MODEL COUNT TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['model_count'] = num_variant
            #APPEND THE MODEL STOCK TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['model_stock'] = json_api['data']['models'][i]['stock']
            #APPEND THE MODEL NAME TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['model_name'] = json_api['data']['models'][i]['name']
            #APPEND THE MODEL ORIGINAL PRICE TO THE DICTIONARY DATA OF EACH ITEM
            dict_variant['model_orig_price'] = json_api['data']['models'][i]['price_before_discount']/100000
            #APPEND THE MODEL SALE AND FINAL PRICE TO THE DICTIONARY DATA OF EACH ITEM
            try:
                dict_variant['model_sale_price'] = json_api['data']['models'][i]['price']/100000
                dict_variant['final_price'] = json_api['data']['models'][i]['price']/100000
            except:
                dict_variant['model_sale_price'] = ''
                dict_variant['final_price'] = dict_variant['model_orig_price']/100000
            #APPEND THE MODEL SOLD TO THE DICTIONARY DATA OF EACH ITEM   
            dict_variant['model_sold'] = 0
            #APPEND THE TOTAL MODEL SOLD TO THE DICTIONARY DATA OF EACH ITEM   
            dict_variant['total_model_sold'] = 0
            try:
                #APPEND THE TOTAL VOUCHER DISCOUNT TO THE DICTIONARY DATA OF EACH ITEM   
                dict_variant['voucher_discount'] = voucherDiscount(json_api['data']['shop_vouchers'])
            except:
                dict_variant['voucher_discount'] = None
            #APPEND THE MODEL CONTRIBUTION TO THE DICTIONARY DATA OF EACH ITEM   
            dict_variant['model_contribution'] = modelContribution(dict_variant['model_stock'], dict_variant['stock'])
            #APPEND THE MODEL SALES UNITS TO THE DICTIONARY DATA OF EACH ITEM   
            dict_variant['sales_units'] = modelSalesUnits(dict_variant['model_contribution'], dict_variant['sold'])
            #APPEND THE TOTAL MODEL WARRANTY TO THE DICTIONARY DATA OF EACH ITEM
            try:
                dict_variant['warranty'] = modelWarranty(json_api['data']['attributes'])
            except:
                dict_variant['warranty'] = None
            #APPEND THE SHOW ORIGINAL GUARANTEE TO THE DICTIONARY DATA OF EACH ITEM 
            dict_variant['show_original_guarantee'] = json_api['data']['show_original_guarantee']
            list_variant_data.append(dict_variant)
        #print(list_variant_data)
        #SAVE THE DICTIONARY DATA ON SELLER API TO THE TEMPFILE FOLDER
        try:
            comment = '{} ({}) - itemid: {} TO THE TEMPFILE DIRECTORY....'.format(shop_data_dict['product group'], shop_data_dict['unique_name'], shop_data_dict['itemid'])
            filename = '{} ({})-{}-{}'.format(shop_data_dict['product group'], shop_data_dict['unique_name'], shop_data_dict['itemid'], shop_data_dict['date_crawled'])
            saveTempfile(list_variant_data, '{}/{}'.format(outputDir, shop_data_dict['unique_name']), comment, filename)
            #AUTHENTICITY 
            df = pd.DataFrame.from_dict(list_variant_data)
            df = get_authenticity(df)
            df.to_excel(f"{df_outputDir}/{shop_data_dict['unique_name']}/{shop_data_dict['product group']} ({shop_data_dict['unique_name']})-{shop_data_dict['itemid']}-{shop_data_dict['date_crawled']}.xlsx")
            #df.to_excel('{}/{}/{} ({})-{}-{}.xlsx'.format(df_outputDir, shop_data_dict['product group'],shop_data_dict['product group'], shop_data_dict['unique name'], shop_data_dict['itemid'], shop_data_dict['date_crawled'])
        except:
            comment = '{} ({}) - itemid: {} TO THE TEMPFILE DIRECTORY....'.format(shop_data_dict['product group'], shop_data_dict['unique_name'], shop_data_dict['itemid'])
            filename = '{} ({})-{}-{}'.format(shop_data_dict['product group'], shop_data_dict['unique_name'], shop_data_dict['itemid'], shop_data_dict['date_crawled'])
            saveTempfile(list_variant_data, outputDir, comment, filename)
            #AUTHENTICITY 
            df = pd.DataFrame.from_dict(list_variant_data)
            df = get_authenticity(df)
            df.to_excel(f"{df_outputDir}/{shop_data_dict['product group']} ({shop_data_dict['unique_name']})-{shop_data_dict['itemid']}-{shop_data_dict['date_crawled']}.xlsx")
            #df.to_
        print(df)
        return list_variant_data, df
    except Exception as e:
        print(json_api)
        print('ERROR AT THE PRODUCT PAGE API: ', prod_url)
        print('ERROR: ', e)







