from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time

def init_driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver

def scrape_tokopedia(base_url, start_page=1, end_page=3):
    driver = init_driver()
    
    for page in range(start_page, end_page + 1):
        url = f"{base_url}&page={page}"
        print(f"Scraping page {page}: {url}")
        driver.get(url)

        time.sleep(5)  # Tunggu halaman sepenuhnya dimuat

        # Klik tombol "Lihat selengkapnya" jika ada
        try:
            see_more_button = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="lnkSRPSeeAllLocFilter"]')
            ActionChains(driver).move_to_element(see_more_button).click().perform()
            print("Clicked 'Lihat selengkapnya'")
        except Exception as e:
            print(f"'Lihat selengkapnya' button not found or could not be clicked: {e}")

        # Scroll halaman agar semua produk terlihat
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Ambil konten halaman
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Cek apakah halaman memiliki produk
        products = soup.select('div[data-testid="divSRPContentProducts"] span')
        if not products:
            print(f"No products found on page {page}. Stopping.")
            break

        # Simpan hasil scraping ke file HTML untuk setiap halaman
        save_products(soup, f"page_{page}_products.html")

    driver.quit()

def save_products(soup, filename):
    # Ambil semua elemen span di dalam div[data-testid="divSRPContentProducts"]
    span_elements = soup.select('div[data-testid="divSRPContentProducts"] span')

    # Mendeklarasikan output_html sebagai string kosong
    output_html = "<html><head><title>Scraped Products</title></head><body>"
    output_html += f"<h1>Products from {filename}</h1>"

    # Menambahkan elemen span yang ditemukan ke dalam output_html
    for span in span_elements:
        output_html += f"{span.prettify()}"

    # Menambahkan penutup HTML
    output_html += "</body></html>"

    # Menyimpan HTML ke file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(output_html)

    print(f"HTML output saved as '{filename}'")

# URL pencarian Tokopedia tanpa parameter halaman
base_url = "https://www.tokopedia.com/search?q=elektronik"

# Eksekusi scraping untuk halaman 1 hingga 3
if __name__ == "__main__":
    scrape_tokopedia(base_url, start_page=1, end_page=2)