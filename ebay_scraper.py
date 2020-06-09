import argparse
from pprint import pprint
from traceback import format_exc

import requests
import unicodecsv as csv
from lxml import html

from price_parser import Price

stats = ""

def parse(brand):
    global stats
    url = 'https://www.ebay.com/sch/i.html?_nkw="{0}"&_sacat=0&_ipg=100000&_sop=15&_dmd=1&rt=nc'.format(brand)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
    failed = False

    # Retries for handling network errors
    for _ in range(5):
        print ("Retrieving %s"%(url)) 
        response = requests.get(url, headers=headers, verify=False)
        parser = html.fromstring(response.text)
        print ("Parsing page")

        if response.status_code!=200:
            failed = True
            continue
        else:
            failed = False
            break

    if failed:
        return []

    #product_listings = parser.xpath('//li[contains(@id,"results-listing")]')
    product_listings = parser.xpath('//li[contains(@class, "s-item    ")]')
    raw_result_count = parser.xpath("//h1[contains(@class,'count-heading')]//text()")
    print(">>", raw_result_count)
    result_count = ''.join(raw_result_count).strip()
    print ("Found {0} for {1}".format(result_count,brand))
    scraped_products = []

    total_value = 0

    count = 0;
    for product in product_listings:
        count = count + 1
        raw_url = product.xpath('.//a[contains(@class,"item__link")]/@href')
        raw_title = product.xpath('.//h3[contains(@class,"item__title")]//text()')
        raw_product_type = product.xpath('.//h3[contains(@class,"item__title")]/span[@class="LIGHT_HIGHLIGHT"]/text()')
        raw_price = product.xpath('.//span[contains(@class,"s-item__price")]//text()')

        price  = ' '.join(' '.join(raw_price).split())
        parsed_price = Price.fromstring(price)
        total_value = total_value + parsed_price.amount_float
        title = ' '.join(' '.join(raw_title).split())
        product_type = ''.join(raw_product_type)
        title = title.replace(product_type, '').strip()
        data = {
                    'url':raw_url[0],
                    'title':title,
                    'price':price
        }
        scraped_products.append(data)
    print("count: ", count)
    if scraped_products:
        stats = "STATS --> Brand: %s, Total Items: %d, Total Value: $%0.2f "%(brand, len(scraped_products), total_value)
        print(stats)
    return scraped_products


def save_scraped_data(sdata, brand):
    if sdata:
        print ("Writing scraped data to %s-ebay-scraped-data.csv"%(brand))
        with open('%s-ebay-scraped-data.csv'%(brand),'wb') as csvfile:
            fieldnames = ["title","price","url"]
            writer = csv.DictWriter(csvfile,fieldnames = fieldnames,quoting=csv.QUOTE_ALL)
            writer.writeheader()
            test = {
                    'url':'',
                    'title':stats,
                    'price':''
            }
            sdata.insert(0, test)
            for data in sdata:
                writer.writerow(data)
    else:
        print("No data scraped")   
    return

def process_file(file):
    return 0

# main code entry point

if __name__=="__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('brand',help = 'Brand Name')
    args = argparser.parse_args()

    if (1 == 2):
        file = args.brand
        process_file(file)
    else:
        brand = args.brand
        scraped_data = parse(brand)
        save_scraped_data(scraped_data, brand)
        
    # done
