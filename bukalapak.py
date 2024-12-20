import json
import csv
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import random

def init_driver():
    options = Options()
    options.headless = True  # Agar kita bisa melihat proses scrolling
    options.add_argument('--disable-gpu')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_max_pages(driver, url):
    driver.get(url)
    time.sleep(1)  # Tunggu agar halaman selesai dimuat
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    pagination = soup.find('ul', class_='bl-pagination__list')
    if pagination:
        page_links = pagination.find_all('a', class_='bl-pagination__link')
        if page_links:
            last_page = page_links[-1].text.strip()
            if last_page.isdigit():
                return int(last_page)
    return 1  # Jika pagination tidak ditemukan, anggap hanya ada 1 halaman

def scrape_bukalapak(driver, url, location_filter=""):
    driver.get(url)
    time.sleep(1)
    products = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        product_cards = soup.find_all('div', class_='te-product-card bl-product-card-new')
        for card in product_cards:
            name_tag = card.find('p', class_='bl-text--ellipsis__2')
            name = name_tag.text.strip() if name_tag else None

            price_tag = card.find('p', class_='bl-product-card-new__price')
            price = price_tag.text.strip() if price_tag else None

            location_tag = card.find('p', class_='bl-product-card-new__store-location')
            location = location_tag.text.strip() if location_tag else None

            store_tag = card.find('p', class_='bl-product-card-new__store-name')
            store = store_tag.text.strip() if store_tag else None

            feedback_tag = card.find('span', class_='bl-text--caption-12')
            feedback = feedback_tag.text.strip() if feedback_tag else None

            link_tag = card.find('a', class_='bl-link', href=True)
            product_link = link_tag['href'] if link_tag else None

            # Jika ada filter lokasi, hanya produk dengan lokasi yang sesuai yang disertakan
            if location_filter and location_filter.lower() not in location.lower():
                continue

            products.append({
                'name': name,
                'price': price,
                'location': location,
                'store': store,
                'feedback': feedback,
                'link': product_link
            })

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Sudah sampai bawah halaman.")
            break
        last_height = new_height

    return products

def generate_filename(keyword, extension):
    current_date = datetime.now().strftime("%d-%m-%Y")
    unique_number = random.randint(1000, 9999)
    filename = f"{keyword}_{current_date}_{unique_number}_bukalapak.{extension}"
    return filename

def save_to_json(data, keyword):
    folder_path = os.path.join('result', "json")
    os.makedirs(folder_path, exist_ok=True)
    filename = generate_filename(keyword, "json")
    filepath = os.path.join(folder_path, filename)
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"Data telah disimpan dalam JSON di {filepath}")

def save_to_csv(data, keyword):
    folder_path = os.path.join('result', "csv")
    os.makedirs(folder_path, exist_ok=True)
    filename = generate_filename(keyword, "csv")
    filepath = os.path.join(folder_path, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Data telah disimpan dalam CSV di {filepath}")

# Urutan input:
# 1. Masukkan kata kunci pencarian
keyword = input("Masukkan kata kunci pencarian: ").strip()
if not keyword:
    print("Kata kunci tidak boleh kosong!")
else:
    keyword = keyword.replace(" ", "%20")

    # 2. Masukkan filter lokasi
    location_filter = input("Masukkan filter lokasi (kosongkan untuk semua lokasi): ").strip()

    # 3. Masukkan jumlah halaman yang ingin diambil
    try:
        page_count = int(input("Masukkan jumlah halaman yang ingin diambil: "))
        if page_count <= 0:
            print("Jumlah halaman harus lebih besar dari 0.")
        else:
            # 4. Pilih format penyimpanan
            print("Pilih format penyimpanan: (ketik 'json' atau 'csv')")
            choice = input("Masukkan pilihan: ").strip().lower()

            if choice not in ['json', 'csv']:
                print("Pilihan tidak valid. Program selesai.")
            else:
                driver = init_driver()
                url = f"https://www.bukalapak.com/products?search%5Bkeywords%5D={keyword}"
                max_pages = get_max_pages(driver, url)
                print(f"Jumlah halaman maksimum yang tersedia: {max_pages}")

                if page_count > max_pages:
                    print(f"Jumlah halaman terlalu besar. Maksimum adalah {max_pages}. Program akan keluar.")
                    driver.quit()
                else:
                    all_products = []
                    for page in range(1, page_count + 1):
                        print(f"Scraping halaman {page}...")
                        page_url = f"{url}&page={page}"
                        page_products = scrape_bukalapak(driver, page_url, location_filter)
                        all_products.extend(page_products)

                    driver.quit()

                    if all_products:
                        if choice == 'json':
                            save_to_json(all_products, keyword)
                        elif choice == 'csv':
                            save_to_csv(all_products, keyword)
                    else:
                        print(f"Tidak ada produk ditemukan untuk kata kunci '{keyword}' dengan lokasi '{location_filter}'.")
    except ValueError:
        print("Jumlah halaman harus berupa angka.")