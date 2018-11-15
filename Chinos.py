import ast
import base64
import html
import json
import os
import re
import urllib.request
import requests
import logger
import urllib3.request
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests_cache
#requests_cache.install_cache('demo_cache')
# Pre Configurations
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

results = []

def setProxy():
    base_url = 'http://h.saavncdn.com'
    proxy_ip = ''
    if ('http_proxy' in os.environ):
        proxy_ip = os.environ['http_proxy']
    proxies = {
        'http': proxy_ip,
        'https': proxy_ip,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
    }
    return proxies, headers

from multiprocessing.dummy import Pool as ThreadPool
def doItParallel(method, products, threads=2):
    pool = ThreadPool(threads)
    results = pool.map(method, products)
    pool.close()
    pool.join()

def getProductDetails(product_url):
    product_url = "https://www.myntra.com/"+product_url
    try:
        proxies, headers = setProxy()
        res = requests.get(product_url, proxies=proxies, headers=headers)
    except Exception as e:
        logger.error('Error : ' + e)
    soup = BeautifulSoup(res.text, "html.parser")
    chino = json.loads(soup.find_all("script")[6].string[15:])["pdpData"]
    for obj in chino['sizes'][0]['measurements']:
        if obj['name'] == "Inseam Length" and float(obj["value"]) >= 35.0:
            print(product_url)
            results.append(product_url)


def getFilterDetails(products_url, queryparams):
    try:
        proxies, headers = setProxy()
        res = requests.get(products_url + urlencode(queryparams), proxies=proxies, headers=headers)
        json_results = json.loads(res.text)['data']['results']
        print("Filter Count: "+str(json_results['totalProductsCount']))
        pages = int(json_results['totalProductsCount']/50)
        pages = 1 if pages==0  else  pages  
        print("Total Pages: "+str(pages))
        return pages+1
    except Exception as e:
        logger.error('Error : ' + e)

def processProductsByChunks(input_url):
        proxies, headers = setProxy()
        res = requests.get(input_url, proxies=proxies, headers=headers)
        json_results = json.loads(res.text)['data']['results']
        products = []
        print('Products Found: '+ str(len(json_results['products'])))
        for obj in json_results['products']:
            products.append(obj['dre_landing_page_url'])
        doItParallel(getProductDetails, products, 4)

from urllib.parse import urlencode
if __name__ == '__main__':
    queryparams = {'f': 'price:459.0,878.0::size_facet:32,34',
                   'p':0,
                   'rows': 50
                   }
    #input_url = input('Enter the url:').strip()
    #input_url  = "https://www.myntra.com/web/v2/search/data/indian-terrain-trousers?f=size_facet:32,34&p=1&rows=200"
    #input_url = "https://www.myntra.com/web/v2/search/data/men-formal-trousers?f=Fit_article_attr:slim fit::size_facet:34&p=1&rows=48"
    input_url = "https://www.myntra.com/web/v2/search/data/men-casual-trousers?"
    chunks = []
    for i in range(1, getFilterDetails(input_url, queryparams)):
        queryparams['p'] = i
        chunks.append(input_url + urlencode(queryparams))
    doItParallel(processProductsByChunks, chunks, 4)
    results.sort()
    print('\n'.join('{}: {}'.format(*k) for k in enumerate(results)))
