# Scrape Resale Sites
This program takes in a brand parameter and automatically scrapes the available and sold product listings for that brand off of eBay, Poshmark, and thredUP. The parameters of each listing scraped are the title, price, availablity, size, and url. These stats are combined into three CSV files (one for each site) displaying total stats per site including the total value of all products for the brand on that specific site.

Built using the Requests, argparse, lxml, and price_parser libraries.
