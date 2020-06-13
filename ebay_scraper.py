import argparse
import requests
from lxml import html
from price_parser import Price
#from pprint import pprint
#from traceback import format_exc
#import unicodecsv as csv

# keeps track of global data stats

stats = ""
stats_sold = ""
scraped_products = []
available_value = 0
sold_value = 0

def parse_available(brand):
    global stats
    global available_value

    page_num = 1
    scraped_products = []
    total_value = 0
    total_count = 0

    while True:
        #url = 'https://www.ebay.com/sch/i.html?_nkw="{0}"&_sacat=0&_dmd=1&_sop=1'.format(brand) - sorts by ending soonest
        url = 'https://www.ebay.com/sch/i.html?_nkw="{0}"&_sacat=0&_dmd=1&_sop=10&_ipg=200&_pgn={1}'.format(brand, page_num) # sorts by newly listed
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
        failed = False

        # Retries for handling network errors
        for _ in range(5):
            print ("Retrieving %s\n\n"%(url)) 
            response = requests.get(url, headers=headers, verify=True)
            parser = html.fromstring(response.text)
            print ("\n\nParsing page")

            if response.status_code!=200:
                failed = True
                continue
            else:
                failed = False
                break

        if failed:
            print("The eBay network is unresponsive. Please try again later (or now).")
            return []

        #product_listings = parser.xpath('//li[contains(@id,"results-listing")]')
        product_listings = parser.xpath('//li[contains(@class, "s-item    ")]')
        raw_result_count = parser.xpath("//h1[contains(@class,'count-heading')]//text()")

        if raw_result_count == None: 
            print("NILNILNIL")
        if len(raw_result_count) < 1:
            print("0000000000")
            continue
        #result_count = ''.join(raw_result_count).strip()
        result_count = raw_result_count[0]
        result_count = result_count.replace(',', "")
        #print ("Found {0} for {1}".format(result_count,brand))
 
        count = 0
        for product in product_listings:
            raw_url = product.xpath('.//a[contains(@class,"item__link")]/@href')
            raw_title = product.xpath('.//h3[contains(@class,"item__title")]//text()')
            raw_product_type = product.xpath('.//h3[contains(@class,"item__title")]/span[@class="LIGHT_HIGHLIGHT"]/text()')
            raw_price = product.xpath('.//span[contains(@class,"s-item__price")]//text()')
            raw_title[0].encode('ascii', 'ignore')
            sponsored = product.xpath('.//span[contains(@role,"text")]//text()')
            if (len(sponsored) > 0): # don't count sponsored products
                continue

            count = count + 1
            price  = ' '.join(' '.join(raw_price).split())
            parsed_price = Price.fromstring(price)
            total_value = total_value + parsed_price.amount_float
            title = ' '.join(' '.join(raw_title).split())
            product_type = ''.join(raw_product_type)
            title = title.replace(product_type, '').strip()

            data = {
                        'url':raw_url[0],
                        'title':title,
                        'price':price, 
                        'sold':"Available"
            }
            scraped_products.append(data)
        print("data: ", data)
        if scraped_products:
            total_count = total_count + count
            if count < 200:
                value = (total_value / total_count) * int(result_count)
                stats = "  AVAILABLE STATS for Brand: %s, Items Scanned: %d, Total Items (Including sponsored): %d Value (Without sponsored): $%0.2f "%( brand, 
                total_count, int(result_count), value) 
                available_value = value  
                print(stats)
                print("-------> DONE!")
                break
            page_num = page_num + 1
    return scraped_products

def parse_sold(brand):
    global sold_stats
    global sold_value
 
    page_num = 1
    scraped_products = []
    total_value = 0
    total_count = 0

    while True:
        #url = 'https://www.ebay.com/sch/i.html?_nkw="{0}"&_sacat=0&_dmd=1&_sop=1'.format(brand) - sorts by ending soonest
        url = 'https://www.ebay.com/sch/i.html?_nkw="{0}"&_sacat=0&_dmd=1&_sop=10&LH_Complete=1&_ipg=200&_pgn={1}'.format(brand, page_num) # sorts by newly listed
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
        failed = False

        # Retries for handling network errors
        for _ in range(5):
            print ("Retrieving %s\n\n"%(url)) 
            response = requests.get(url, headers=headers, verify=True)
            parser = html.fromstring(response.text)
            print ("\n\nParsing page")

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

        if raw_result_count == None: 
            print("NILNILNIL")
        if len(raw_result_count) < 1:
            print("0000000000")
            continue
        #result_count = ''.join(raw_result_count).strip()
        result_count = raw_result_count[0]
        result_count = result_count.replace(',', "")
        #print ("Found {0} for {1}".format(result_count,brand))
 
        count = 0
        for product in product_listings:
            raw_url = product.xpath('.//a[contains(@class,"item__link")]/@href')
            raw_title = product.xpath('.//h3[contains(@class,"item__title")]//text()')
            raw_title[0].encode('ascii', 'ignore')
            raw_product_type = product.xpath('.//h3[contains(@class,"item__title")]/span[@class="LIGHT_HIGHLIGHT"]/text()')
            raw_price = product.xpath('.//span[contains(@class,"s-item__price")]//text()')

            count = count + 1
            price  = ' '.join(' '.join(raw_price).split())
            parsed_price = Price.fromstring(price)
            total_value = total_value + parsed_price.amount_float
            title = ' '.join(' '.join(raw_title).split())
            product_type = ''.join(raw_product_type)
            title = title.replace(product_type, '').strip()

            data = {
                        'url':raw_url[0],
                        'title':title,
                        'price':price, 
                        'sold':"Sold"
            }
            scraped_products.append(data)
        print("data: ", data)
        if scraped_products:
            total_count = total_count + count
            if count < 200:
                value = (total_value / total_count) * int(result_count)
                sold_stats = "  SOLD STATS for Brand: %s, Total Sold Items: %d, Value: $%0.2f "%( brand, 
                total_count, value)   
                print(sold_stats)
                sold_value = value
                print("-------> DONE!")
                break
            page_num = page_num + 1
    return scraped_products

def save_scraped_data(sdata, brand):
    file_name = str(brand) + "_result.csv"
    f = open(file_name,"w+")
    f.write("\"title\", price, sold, url\r\n")

    total_value_stats = "  TOTAL VALUE OF AVAILABLE AND SOLD ITEMS: $" + str(available_value + sold_value)
    f.write( stats) 
    f.write("\r\n")
    f.write(sold_stats)
    f.write( "\r\n" )
    f.write(total_value_stats)
    f.write( "\r\n" )

    for data in sdata:
        f.write("\"" + data['title'] + "\", ")
        new_price = data['price'].replace(',', "")
        f.write( new_price + ", ")
        f.write( data['sold'] + ", ")
        f.write( data['url'] + "\r\n")
    f.close() 
    return

# not being called
def save_scraped_data2(sdata, brand): # with the csv library - not compatible with pyinstaller
    if sdata:
        print ("Writing scraped data to %s-ebay-scraped-data.csv"%(brand))
       # with open('%s-ebay-scraped-data.csv'%(brand),'wb') as csvfile:
           # fieldnames = ["title","price","url"]
           # writer = csv.DictWriter(csvfile,fieldnames = fieldnames,quoting=csv.QUOTE_ALL)
           # writer.writeheader()
            #test = {
                   # 'url':'',
                    #'title':stats,
                    #'price':''
           #}
            # sdata.insert(0, test)
           # for data in sdata:
               # writer.writerow(data)
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

    if (False):
        file = args.brand
        process_file(file)
    else:
        brand = args.brand
        scraped_data = parse_available(brand)
        scraped_data = scraped_data + parse_sold(brand)
        save_scraped_data(scraped_data, brand)
       
    # done