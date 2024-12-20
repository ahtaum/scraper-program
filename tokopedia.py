import os
import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def init_driver():
    options = Options()
    options.headless = True
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_tokopedia(base_url, start_page=1, end_page=3, location_filter=None):
    driver = init_driver()
    scraped_data = []

    for page in range(start_page, end_page + 1):
        url = f"{base_url}&page={page}"
        print(f"Scraping page {page}: {url}")
        driver.get(url)

        time.sleep(5)  # Waktu untuk menunggu halaman sepenuhnya dimuat

        # Scroll halaman agar semua produk terlihat
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Tunggu hingga halaman benar-benar di-scroll
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Ambil konten halaman
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Cek apakah halaman memiliki produk
        product_container = soup.select('div[data-testid="divSRPContentProducts"]')
        if not product_container:
            print(f"No products found on page {page}. Stopping.")
            break

        # Scrape data dari halaman
        judul = product_container[0].select('span[class="_0T8-iGxMpV6NEsYEhwkqEg=="]')
        toko = product_container[0].select('span[class="T0rpy-LEwYNQifsgB-3SQw== pC8DMVkBZGW7-egObcWMFQ== flip"]')
        lokasi = product_container[0].select('span[class="pC8DMVkBZGW7-egObcWMFQ== flip"]')
        links = product_container[0].find_all('a')

        for title, store, loc, link in zip(judul, toko, lokasi, links):
            product = {
                "title": title.get_text(strip=True),
                "store": store.get_text(strip=True),
                "lokasi": loc.get_text(strip=True),
                "link": link.get('href')
            }

            # Filter by location if location_filter is specified
            if location_filter:
                if location_filter.lower() in product["lokasi"].lower():
                    scraped_data.append(product)
            else:
                scraped_data.append(product)

    driver.quit()
    return scraped_data

def create_url(keyword):
    return f"https://www.tokopedia.com/search?st=product&q={keyword.replace(' ', '+')}"

def export_data(scraped_data, export_type="json"):
    # Membuat folder 'result' jika belum ada
    folder_name = "result"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Menentukan nama file output
    if export_type == "json":
        output_file = f"{folder_name}/scraped_products.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=4)
        print(f"JSON output saved as '{output_file}'")
    elif export_type == "csv":
        output_file = f"{folder_name}/scraped_products.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["title", "store", "lokasi", "link"])
            writer.writeheader()
            writer.writerows(scraped_data)
        print(f"CSV output saved as '{output_file}'")

def main():
    try:
        while True:
            keyword = input("Enter the product keyword you want to search for (or type 'quit' to exit): ")
            if keyword.lower() == 'quit':
                print("Exiting program.")
                return
            if keyword:
                break
            print("Keyword cannot be empty. Please enter a valid keyword.")
        
        location_filter = input("Enter a location to filter (leave blank for no filter, or type 'quit' to exit): ").strip()
        if location_filter.lower() == 'quit':
            print("Exiting program.")
            return

        # Halaman awal selalu default 1
        start_page = 1
        while True:
            try:
                end_page = int(input("Enter the ending page number (or type 'quit' to exit): "))
                if end_page < start_page:
                    print("Ending page must be greater than or equal to 1.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number.")

        export_choice = input("Do you want to export as JSON or CSV? (Enter 'json' or 'csv', or type 'quit' to exit): ").lower()
        if export_choice == 'quit':
            print("Exiting program.")
            return

        url = create_url(keyword)
        scraped_data = scrape_tokopedia(url, start_page=start_page, end_page=end_page, location_filter=location_filter)

        if scraped_data:
            export_data(scraped_data, export_choice)
        else:
            print("No data to export.")
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting.")
        return

if __name__ == "__main__":
    main()