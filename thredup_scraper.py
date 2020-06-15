import argparse
import requests
from lxml import html
from price_parser import Price

stats = "" 
scraped_products = [] 
available_value = 0 

def parse_available(brand):
    global stats 
    global available_value 

    page_num = 1 
    total_value = 0 
    total_count = 0 

    # change spaces in the brand name to '%20' to match the thredup url
    url_brand = (brand.replace(' ', '%20')).lower()

    while True:
        url = 'https://www.thredup.com/women?department_tags=women&sort=newest_first&text={0}&page={1}'.format(url_brand, page_num) # sorts by newly listed
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
            print("The thredUP network is unresponsive. Please try again later (or now).")
            return []

        product_listings = parser.xpath('//div[contains(@class, "grid-item")]')
 
        count = 0
        for product in product_listings:
            raw_url = product.xpath('.//a[contains(@class,"_1di0il_2VkBBwWJz9eDxoJ")]/@href')
            raw_title_and_price = product.xpath('.//div[contains(@class,"_138U7gqcrSxaloaCpyMPZg")]//text()')
            raw_title_and_price[0].encode('ascii', 'ignore')

            count = count + 1
            product_url = 'https://thredup.com' + raw_url[0]
            title = raw_title_and_price[0]
            price  = '$' + raw_title_and_price[2] 
            print("PRICE: ", price)
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
            if count < 50: # 50 items per page on thredUP
                stats = "  AVAILABLE STATS for Brand: %s   Items Scanned: %d   Value (Without sponsored): $%0.2f "%( brand, 
                total_count, total_value)
                available_value = total_value  
                print(stats)
                print("-------> DONE WITH AVAILABLE!")
                break
            page_num = page_num + 1
        else:
            print("No available product listings on thredUP")
            break
    return scraped_products

def save_scraped_data(sdata, brand):
    if sdata:
        file_name = "thredUP_" + str(brand) + ".csv"
        f = open(file_name,"w+")
        f.write("\"title\", price, sold, url\r\n")

        f.write(stats) 
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
    save_scraped_data(scraped_data, brand)
       
    # done