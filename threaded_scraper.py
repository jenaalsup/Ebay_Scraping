import argparse
import requests
from lxml import html
from price_parser import Price

# threading
from multiprocessing import Pool
import multiprocessing

stats = "" # available total value stats
sold_stats = "" # sold total value stats
#available_value = 0
sold_value = 0
final_global_value = 0

global brand
brand = ""



# xsmall, small, medium, large, xlarge, unknown
sizes = [0, 0, 0, 0, 0, 0]

# header for requests
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}


ebay_scraped_products = []
ebay_max_page = 111   # > max possible pages for start
ebay_page_size = 200
ebay_count = 0
ebay_total_value = 0
ebay_result_count = 0
ebay_available_value = 0

ebay_sold_value = 0
ebay_sold_max_page = 111
ebay_sold_count = 0
ebay_sold_result_count = 0

def ebay_parse_available(page_list):
  global sizes
  global ebay_max_page
  global ebay_count
  global ebay_result_count
  total_value = 0
 
  if page_list == None:
    print("   >>>> Hun?")
    return
  page_num = page_list[0]
  brand = page_list[1]
  # scraped_products = page_list[2]
  scraped_products = []
 
  if page_num > ebay_max_page:  # end reached - disable further processing
    return None

  url = 'https://www.ebay.com/sch/i.html?_nkw="{0}"&_sacat=0&_dmd=1&_sop=10&_ipg=200&_pgn={1}'.format(brand, page_num) # sorts by newly listed
  failed = False

  # Retries 5 times for handling network errors
  for _ in range(5):
    print ("Retrieving page: ", page_num, "%s"%(url)) 
    try: 
      response = requests.get(url, headers=headers, verify=True, timeout=2)
    except: # max retries or timeout exception because website is slow
      print("MAX RETRIES OR TIMEOUT EXCEPTION BECAUSE WEBSITE IS SLOW")
      return
    parser = html.fromstring(response.text)

    #print("    Response code:", response.status_code )
    if response.status_code!=200: 
      print("eBay URL request failed to respond, retrying...")
      failed = True
      continue
    else:
      #print("Available page num :", page_num+1)
      failed = False
      break

  if failed:
    print("The eBay network is unresponsive. Please try again later (or now).")
    return None

  product_listings = parser.xpath('//li[contains(@class, "s-item    ")]')
  raw_result_count = parser.xpath("//h1[contains(@class,'count-heading')]//text()")

  if raw_result_count == None: 
    print("    >> NIL raw_result_count")
    return None
  if len(raw_result_count) == 0:
    print("   >> raw_result_count = 0")
    return None

  result_count = raw_result_count[0]
  result_count = result_count.replace( ',', "" )
  if int(result_count) == 0:  # were done
    return None
  if int(result_count) < (page_num-1) * ebay_page_size:
    print("     >>> Page ", page_num, "Result Count ", int(result_count), " ignored - past data threshold" )
    return  None # were done here

  count = 0
  total_value = 0
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

    # check for sizes in product title
    if title.lower().find('xsmall') >= 0:
      size = 'Xsmall'
      sizes[0] = sizes[0] + 1
    elif title.lower().find('small') >= 0:
      size = 'Small'
      sizes[1] = sizes[1] + 1
    elif title.lower().find('medium') >= 0:
      size = 'Medium'
      sizes[2] = sizes[2] + 1
    elif title.lower().find('large') >= 0:
      size = 'Large'
      sizes[3] = sizes[3] + 1
    elif title.lower().find('xlarge') >= 0:
      size = 'XLarge'
      sizes[4] = sizes[4] + 1
    else:  
      size = 'Unknown'
      sizes[5] = sizes[5] + 1
    data = {
      'page':page_num,
      'url':raw_url[0],
      'title':title,
      'price':price, 
      'sold':"Available",
      'size':size
    }
    scraped_products.append(data)

  #print("    >>>> COUNT: ", count)
  max_page = -1
  if product_listings != None:
    if count < 200:
      print("  EBAY: REACHED LAST PAGE AT: ", page_num)
      max_page = page_num
  else:
    if (page_num == 0):
      print("  EBAY: No available product listings on eBay")
    else:
      print("  EBAY: REACHED LAST PAGE AT: ", page_num)
      max_page = page_num
  #print("     >>>>>>>  totals: ", count, total_value )
  list = {'page': page_num, 'max_page': max_page, 'count': count, 'value': total_value, 'result_count': result_count, 'products' : scraped_products}
  return list

def ebay_available_stats(brand):
  global ebay_available_value
  global ebay_count
  global ebay_result_count
  global ebay_total_value

  if ebay_count == 0:
    print("  EBAY RESULTS ARE 0")
    return
  value = (ebay_total_value / ebay_count) * int(ebay_result_count)
  stats = "  AVAILABLE STATS for Brand: %s   Items Scanned: %d   Total Items (Including sponsored): %d   Value (Without sponsored): $%0.2f "%( brand, 
          ebay_count, int(ebay_result_count), value) 
  ebay_available_value = value  
  print(stats)

def ebay_process_available_data(name_brand):
  global ebay_count
  global ebay_total_value
  global ebay_result_count
  global ebay_max_page

  print("name brand ", name_brand)
  ebay_pagenum_list = []
  for i in range(200):
    ebay_pagenum_list.append( [i+1, name_brand] )
  POOL_NUM = 8
  #print(">>> ", ebay_pagenum_list )
  with Pool(POOL_NUM) as p:
    data = p.map( ebay_parse_available, ebay_pagenum_list )
    print( ">>> ", len(data) )
    for l in data:
      if l == None:
        continue
      #print( "    >>", l )
      page = l['page']
      temp = l["max_page"]
      if temp >= 0:
          if ebay_max_page == -1:
            ebay_max_page = temp
          if temp < ebay_max_page:
            ebay_max_page = temp
      products = l['products']
      count = l['count']
      ebay_count = ebay_count + count
      ebay_result_count = l['result_count']
      ebay_total_value = ebay_total_value + l['value']
      # Now copy each entry to master list
      start = (page - 1) * ebay_page_size
      j = 0
      # note that products may not appear in the order they do on the ebay web site search
      for i in range(start, start + count):
        products[j]['page'] = page
        ebay_scraped_products.append(products[j])
        j = j + 1
      #print( ebay_scraped_products)
    print(">>>> DONE with ebay thread processing")
  ebay_available_stats(name_brand)
  return 

def ebay_parse_sold(brand):
  global sizes
  global ebay_sold_max_page
  global ebay_sold_count
  global ebay_sold_result_count
  total_value = 0

  page_num = 1
  scraped_products = []
  total_value = 0
 # total_count = 0

  while True:
    url = 'https://www.ebay.com/sch/i.html?_nkw="{0}"&_sacat=0&_dmd=1&_sop=10&LH_Complete=1&_ipg=200&_pgn={1}'.format(brand, page_num) # sorts by newly listed
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
    failed = False

    # Retries 5 times for handling network errors
    for _ in range(5):
      print ("Retrieving %s"%(url)) 
      try: 
        response = requests.get(url, headers=headers, verify=True, timeout=2)
      except: # max retries or timeout exception because website is slow
        print("MAX RETRIES OR TIMEOUT EXCEPTION BECAUSE WEBSITE IS SLOW")
        return scraped_products
      parser = html.fromstring(response.text)

      if response.status_code!=200:
        print("eBay URL request failed to respond, retrying...")
        failed = True
        continue
      else:
        print("Sold page num :", page_num)
        failed = False
        break

    if failed:
      print("The eBay network is unresponsive. Please try again later (or now).")
      return []

    product_listings = parser.xpath('//li[contains(@class, "s-item    ")]')
    raw_result_count = parser.xpath("//h1[contains(@class,'count-heading')]//text()")

    if raw_result_count == None: 
        print("NILNILNIL")
    if len(raw_result_count) < 1:
        print("0000000000")
        continue
    result_count = raw_result_count[0]
    result_count = result_count.replace(',', "")

    count = 0
    for product in product_listings:
      raw_url = product.xpath('.//a[contains(@class,"item__link")]/@href')
      raw_title = product.xpath('.//h3[contains(@class,"item__title")]//text()')
      raw_title[0].encode('ascii', 'ignore')
      raw_product_type = product.xpath('.//h3[contains(@class,"item__title")]/span[@class="LIGHT_HIGHLIGHT"]/text()')
      raw_price = product.xpath('.//span[contains(@class,"s-item__price")]//text()')
      raw_sold_date = product.xpath('.//span[contains(@class,"s-item__ended-date")]//text()')

      count = count + 1
      price  = ' '.join(' '.join(raw_price).split())
      parsed_price = Price.fromstring(price)
      total_value = total_value + parsed_price.amount_float
      title = ' '.join(' '.join(raw_title).split())
      product_type = ''.join(raw_product_type)
      title = title.replace(product_type, '').strip()
      sold_date = raw_sold_date[0].split()[0]

      # check for sizes in product title
      if title.lower().find('xsmall') >= 0:
        size = 'Xsmall'
        sizes[0] = sizes[0] + 1
      elif title.lower().find('small') >= 0:
        size = 'Small'
        sizes[1] = sizes[1] + 1
      elif title.lower().find('medium') >= 0:
        size = 'Medium'
        sizes[2] = sizes[2] + 1
      elif title.lower().find('large') >= 0:
        size = 'Large'
        sizes[3] = sizes[3] + 1
      elif title.lower().find('xlarge') >= 0:
        size = 'XLarge'
        sizes[4] = sizes[4] + 1
      else:  
        size = 'Unknown'
        sizes[5] = sizes[5] + 1

      data = {
                  'url':raw_url[0],
                  'title':title,
                  'price':price, 
                  'sold':"Sold: "+sold_date,
                  'size':size
      }
      scraped_products.append(data)

    #print("    >>>> COUNT: ", count)
    max_page = -1
    if product_listings != None:
      if count < 200:
        print("  EBAY SOLD: REACHED LAST PAGE AT: ", page_num)
        max_page = page_num
    else:
      if (page_num == 0):
        print("  EBAY: No sold product listings on eBay")
      else:
        print("  EBAY SOLD: REACHED LAST PAGE AT: ", page_num)
        max_page = page_num
    #print("     >>>>>>>  totals: ", count, total_value )
    list = {'page': page_num, 'max_page': max_page, 'count': count, 'value': total_value, 'result_count': result_count, 'products' : scraped_products}
    return list

def ebay_sold_stats(brand):
  global ebay_sold_value
  global ebay_sold_count
  global ebay_sold_result_count
  global ebay_total_value

  if ebay_count == 0:
    print("  EBAY RESULTS ARE 0")
    return
  value = (ebay_total_value / ebay_count) * int(ebay_result_count)
  stats = "  SOLD STATS for Brand: %s   Items Scanned: %d   Total Items (Including sponsored): %d   Value (Without sponsored): $%0.2f "%(brand, 
          ebay_sold_count, int(ebay_sold_result_count), value) 
  ebay_sold_value = value  
  print(stats)

def ebay_process_sold_data(name_brand):
  global ebay_sold_count
  global ebay_total_value
  global ebay_result_count
  global ebay_sold_max_page

  print("name brand ", name_brand)
  ebay_pagenum_list = []
  for i in range(200):
    ebay_pagenum_list.append( [i+1, name_brand] )
  POOL_NUM = 8
  #print(">>> ", ebay_pagenum_list )
  with Pool(POOL_NUM) as p:
    data = p.map( ebay_parse_sold, ebay_pagenum_list )
    print( ">>> ", len(data) )
    for l in data:
      if l == None:
        continue
      #print( "    >>", l )
      page = l['page']
      temp = l["max_page"]
      if temp >= 0:
          if ebay_sold_max_page == -1:
            ebay_sold_max_page = temp
          if temp < ebay_sold_max_page:
            ebay_sold_max_page = temp
      products = l['products']
      count = l['count']
      ebay_count = ebay_count + count
      ebay_result_count = l['result_count']
      ebay_total_value = ebay_total_value + l['value']
      # Now copy each entry to master list
      start = (page - 1) * ebay_page_size
      j = 0
      # note that products may not appear in the order they do on the ebay web site search
      for i in range(start, start + count):
        products[j]['page'] = page
        ebay_scraped_products.append(products[j])
        j = j + 1
      #print( ebay_scraped_products)
    print(">>>> DONE with ebay thread processing")
  ebay_sold_stats(name_brand)
  return 


def save_scraped_data(website, sdata, brand):
  global final_global_value
  if sdata:
    if website == 'ebay':
      file_name = "eBay_" + str(brand) + ".csv"
    elif website == 'poshmark':
      file_name = "Poshmark_" + str(brand) + ".csv"
    elif website == 'thredup':
      file_name = "thredUP_" + str(brand) + ".csv"
    else:
      file_name = str(brand) + ".csv"

    f = open(file_name,"w+")
    f.write("\"title\", price, sold, size, url\r\n")

    size_display = "  Number of xsmall, small, medium, large, xlarge, unknown: " + str(sizes).strip('[]')
    total_value_stats = "  TOTAL VALUE OF AVAILABLE AND SOLD ITEMS: $" + str(ebay_available_value + sold_value)
    final_global_value = final_global_value + ebay_available_value + sold_value
    print(total_value_stats)
    f.write(stats) 
    f.write("\r\n")
    f.write(sold_stats)
    f.write("\r\n")
    f.write(size_display)
    f.write( "\r\n" )
    f.write(total_value_stats)
    f.write( "\r\n" )

    count = 0
    print("    Skipping all pages above ", ebay_max_page)
    for data in sdata:
      # print( "   ! ", count, data)
      if data['page'] > ebay_max_page:
        continue
      count = count + 1
      f.write("\"" + data['title'] + "\", ")
      new_price = data['price'].replace(',', "")
      f.write(new_price + ", ")
      f.write(data['sold'] + ", ")
      f.write(data['size'] + ", ")
      f.write(data['url'] + "\r\n")
    f.close() 
  else:
    print("No data scraped")
  return



# main code entry point
if __name__=="__main__":
  multiprocessing.freeze_support()
  argparser = argparse.ArgumentParser()
  argparser.add_argument('brand', help = 'Brand Name')
  args = argparser.parse_args()
  name_brand = args.brand

  # ebay
  #ebay_scraped_data = ebay_parse_available(brand)
  ebay_process_available_data(name_brand)
  ebay_process_sold_data(name_brand)
  save_scraped_data('ebay', ebay_scraped_products, name_brand)
  print("DONE WITH EBAY")

  # poshmark
  #poshmark_scraped_data = poshmark_parse_available(brand)
  #poshmark_scraped_data = poshmark_scraped_data + poshmark_parse_sold(brand)
  #save_scraped_data('poshmark', poshmark_scraped_data, brand)
  #print("DONE WITH POSHMARK")

  # thredup
  #thredup_scraped_data = thredup_parse_available(brand)
  #save_scraped_data('thredup', thredup_scraped_data, brand)
  #print("DONE WITH THREDUP")

  print("TOTAL VALUE OF ALL ITEMS ON EBAY, POSHMARK, THREDUP: " + str(final_global_value))
