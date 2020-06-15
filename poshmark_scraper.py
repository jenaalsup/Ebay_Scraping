import argparse
import requests
from lxml import html
from price_parser import Price

stats = "" 
sold_stats = "" 
scraped_products = [] 
available_value = 0 
sold_value = 0 

def parse_available(brand):
    global stats 
    global available_value 

    page_num = 1 
   # scraped_products = []
    total_value = 0 
    total_count = 0 

    # change spaces in the brand name to '%20' to match the poshmark url
    url_brand = (brand.replace(' ', '%20')).lower()

    while True:
        url = 'https://poshmark.com/search?query={0}&sort_by=added_desc&max_id={1}'.format(url_brand, page_num) # sorts by just in
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
        failed = False

        # Retries 5 times for handling network errors
        for _ in range(5):
            print ("Retrieving %s\n\n"%(url)) 
            response = requests.get(url, headers=headers, verify=True)
            parser = html.fromstring(response.text)
            print("Done retrieving")

            if response.status_code!=200:
                failed = True
                continue
            else:
                print("Available page num :", page_num)
                failed = False
                break

        if failed:
            print("The Poshmark network is unresponsive. Please try again later (or now).")
            return []

        product_listings = parser.xpath('//div[contains(@class, "card card--small")]')
 
        count = 0
        for product in product_listings:
            raw_url = product.xpath('.//a[contains(@class,"tile__covershot")]/@href')
            raw_title = product.xpath('.//a[contains(@class,"tile__title")]//text()')
            raw_price = product.xpath('.//span[contains(@class,"p--t--1")]//text()')
            raw_title[0].encode('ascii', 'ignore')

            count = count + 1
            product_url = 'https://poshmark.com' + raw_url[0]
            title = ' '.join(' '.join(raw_title).split())
            price  = ' '.join(' '.join(raw_price).split())
            parsed_price = Price.fromstring(price)
            total_value = total_value + parsed_price.amount_float

            data = {
                        'url':product_url,
                        'title':title,
                        'price':price, 
                        'sold':"Available"
            }
            scraped_products.append(data)

        if scraped_products:
            total_count = total_count + count
            if count < 48: # 48 items per page on Poshmark
                stats = "  AVAILABLE STATS for Brand: %s   Items Scanned: %d   Value (Without sponsored): $%0.2f "%( brand, 
                total_count, total_value)
                available_value = total_value  
                print(stats)
                print("-------> DONE WITH AVAILABLE!")
                break
            page_num = page_num + 1
        else:
            print("No available product listings on Poshmark")
            break
    return scraped_products

def parse_sold(brand):
    global sold_stats 
    global sold_value 

    page_num = 1 
    total_value = 0 
    total_count = 0 

    # change spaces in the brand name to '%20' to match the poshmark url
    url_brand = (brand.replace(' ', '%20')).lower()

    while True:
        url = 'https://poshmark.com/search?query={0}&availability=sold_out&sort_by=added_desc&max_id={1}'.format(url_brand, page_num) # sorts by just in
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
        failed = False

        # Retries 5 times for handling network errors
        for _ in range(5):
            print ("Retrieving %s\n\n"%(url)) 
            response = requests.get(url, headers=headers, verify=True)
            parser = html.fromstring(response.text)
            print("Done retrieving")

            if response.status_code!=200:
                failed = True
                continue
            else:
                print("Sold page num :", page_num)
                failed = False
                break

        if failed:
            print("The Poshmark network is unresponsive. Please try again later (or now).")
            return []

        product_listings = parser.xpath('//div[contains(@class, "card card--small")]')
 
        count = 0
        for product in product_listings:
            raw_url = product.xpath('.//a[contains(@class,"tile__covershot")]/@href')
            raw_title = product.xpath('.//a[contains(@class,"tile__title")]//text()')
            raw_price = product.xpath('.//span[contains(@class,"p--t--1")]//text()')
            raw_title[0].encode('ascii', 'ignore')

            count = count + 1
            product_url = 'https://poshmark.com' + raw_url[0]
            title = ' '.join(' '.join(raw_title).split())
            price  = ' '.join(' '.join(raw_price).split())
            parsed_price = Price.fromstring(price)
            total_value = total_value + parsed_price.amount_float

            data = {
                        'url':product_url,
                        'title':title,
                        'price':price, 
                        'sold':"Sold"
            }
            scraped_products.append(data)

        if scraped_products:
            total_count = total_count + count
            if count < 48: # 48 items per page on Poshmark
                sold_stats = "  SOLD STATS for Brand: %s   Items Scanned: %d   Value (Without sponsored): $%0.2f "%( brand, 
                total_count, total_value)
                sold_value = total_value  
                print(sold_stats)
                print("-------> DONE WITH SOLD!")
                break
            page_num = page_num + 1
        else:
            print("No sold product listings on Poshmark")
            break
    return scraped_products

def save_scraped_data(sdata, brand):
    if sdata:
        file_name = "Poshmark_" + str(brand) + ".csv"
        f = open(file_name,"w+")
        f.write("\"title\", price, sold, url\r\n")

        total_value_stats = "  TOTAL VALUE OF AVAILABLE AND SOLD ITEMS: $" + str(available_value + sold_value)
        print(total_value_stats)
        f.write(stats) 
        f.write("\r\n")
        f.write(sold_stats)
        f.write("\r\n")
        f.write(total_value_stats)
        f.write("\r\n")

        for data in sdata:
            f.write("\"" + data['title'] + "\", ")
            new_price = data['price'].replace(',', "")
            f.write( new_price + ", ")
            f.write( data['sold'] + ", ")
            f.write( data['url'] + "\r\n")
        f.close() 
    else:
        print("No data scraped")
    return

# main code entry point
if __name__=="__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('brand',help = 'Brand Name')
    args = argparser.parse_args()

    brand = args.brand
    scraped_data = parse_available(brand)
    scraped_data = scraped_data + parse_sold(brand)
    save_scraped_data(scraped_data, brand)
       
    # done