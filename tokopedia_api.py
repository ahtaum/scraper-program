import os
import requests
import json
import csv
import time
import sys
import random
from math import ceil

# HEADER REQUEST
def get_request_headers():
    return {
        'sec-ch-ua-platform': 'Android',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'x-price-center': 'true',
        'accept': '*/*',
        'content-type': 'application/json',
        'X-Source': 'tokopedia-lite',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'
    }

# QUERY PAYLOAD
def get_graphql_data(search_term, page):
    start = (page - 1) * 60
    params = f"device=desktop&l_name=sre&ob=23&page={page}&q={search_term}&related=true&rf=true&rows=60&safe_search=false&scheme=https&shipping=&show_adult=false&source=search&st=product&start={start}&topads_bucket=true&unique_id=1f5798576edd6b8f5be3c8424ccfdce6&user_id=0&variants="
    return {
        "operationName": "SearchProductV5Query",
        "variables": {"params": params},
        "query": """
        query SearchProductV5Query($params: String!) {
          searchProductV5(params: $params) {
            header {
              totalData
            }
            data {
              products {
                id
                name
                url
                price {
                  text
                  number
                }
                mediaURL {
                  image
                }
                shop {
                  id
                  name
                  city
                }
              }
            }
          }
        }
        """
    }

# VALIDASI RESPONSE
def validate_response(response):
    try:
        return response['data']['searchProductV5']['data']['products']
    except KeyError:
        print("Struktur API telah berubah. Berikut respons mentah untuk analisis:")
        print(json.dumps(response, indent=4))
        sys.exit(1)

# GET TOTAL PAGES
def get_total_pages(search_term):
    response = requests.post(
        'https://gql.tokopedia.com/graphql/SearchProductV5Query',
        headers=get_request_headers(),
        json=get_graphql_data(search_term, page=1)
    )

    if response.status_code == 200:
        json_data = response.json()
        products = validate_response(json_data)
        total_data = json_data['data']['searchProductV5']['header']['totalData']
        return ceil(total_data / 60), total_data
    else:
        print(f"Permintaan gagal dengan status: {response.status_code}")
        sys.exit(1)

# SCRAPE DATA
def scrape_products(search_term, page):
    response = requests.post(
        'https://gql.tokopedia.com/graphql/SearchProductV5Query',
        headers=get_request_headers(),
        json=get_graphql_data(search_term, page)
    )

    if response.status_code == 200:
        json_data = response.json()
        return validate_response(json_data)
    else:
        print(f"Gagal mengambil data pada halaman {page}. Kode status: {response.status_code}")
        return []

# SCRAPE SEMUA HALAMAN
def scrape_pages(search_term, page_choice):
    total_pages, total_data = get_total_pages(search_term)
    all_products = []

    if page_choice.lower() == "all":
        print(f"Scraping semua {total_pages} halaman ({total_data} produk ditemukan)...")
        pages_to_scrape = range(1, total_pages + 1)
    else:
        try:
            page_choice = int(page_choice)
            if page_choice < 1 or page_choice > total_pages:
                print(f"Halaman {page_choice} tidak valid. Total halaman: {total_pages}")
                sys.exit(0)
            pages_to_scrape = range(1, page_choice + 1)
        except ValueError:
            print("Pilihan halaman tidak valid. Gunakan angka atau 'all'.")
            sys.exit(0)

    for page in pages_to_scrape:
        print(f"Scraping halaman {page}...")
        all_products.extend(scrape_products(search_term, page))
        time.sleep(1)  # Jeda untuk menghindari limitasi API

    return all_products

# FILTER DATA BERDASARKAN KOTA
def filter_by_city(products, city):
    if not city:
        return products
    return [product for product in products if city.lower() in product['shop']['city'].lower()]

# SIMPAN DATA
def save_to_file(products, search_term, city_filter, file_format):
    # Membuat folder 'result' jika belum ada
    folder_name = "result"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    random_number = random.randint(1000, 9999)
    filename = f"{folder_name}/scraped_{search_term.replace(' ', '_')}_{city_filter or 'all'}_{random_number}.{file_format}"

    if file_format == "json":
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(products, file, indent=4, ensure_ascii=False)
    elif file_format == "csv":
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["id", "name", "url", "price_text", "price_number", "image", "shop_id", "shop_name", "shop_city"])
            for product in products:
                writer.writerow([
                    product.get("id"),
                    product.get("name"),
                    product.get("url"),
                    product.get("price", {}).get("text"),
                    product.get("price", {}).get("number"),
                    product.get("mediaURL", {}).get("image"),
                    product.get("shop", {}).get("id"),
                    product.get("shop", {}).get("name"),
                    product.get("shop", {}).get("city"),
                ])
    else:
        print("Format file tidak valid. Program keluar.")
        sys.exit(0)

    print(f"Hasil scraping disimpan ke: {filename}")

# MAIN FUNCTION
def main():
    try:
        search_term = input("Masukkan kata kunci pencarian: ").strip()
        if not search_term:
            print("Kata kunci tidak boleh kosong. Program keluar.")
            sys.exit(0)

        page_choice = input("Masukkan halaman yang ingin diambil (angka atau 'all'): ").strip()
        city_filter = input("Masukkan kota untuk filter (kosongkan untuk semua): ").strip()
        file_format = input("Pilih format output (json/csv): ").strip().lower()

        if file_format not in ["json", "csv"]:
            print("Format file tidak valid. Gunakan 'json' atau 'csv'.")
            sys.exit(0)

        products = scrape_pages(search_term, page_choice)
        filtered_products = filter_by_city(products, city_filter)
        save_to_file(filtered_products, search_term, city_filter, file_format)
    except KeyboardInterrupt:
        print("\nOperasi dibatalkan pengguna.")
        sys.exit(0)

if __name__ == "__main__":
    main()