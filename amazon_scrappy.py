import os
import re
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import lxml
import streamlit as st

def get_product_info(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    try:
        title = soup.find(id='productTitle').get_text(strip=True)
    except AttributeError:
        title = 'No se encontró el título'

    try:
        imagen_url = soup.find(id='landingImage')['src']
    except (AttributeError, TypeError):
        imagen_url = None

    try:
        price = soup.find('span', {'class': 'a-offscreen'}).get_text(strip=True)
    except (AttributeError, ValueError):
        price = 'No price found'
    
    return title, imagen_url, price


def save_image(image_url, product_name):
    folder = "imagenes"
    os.makedirs(folder, exist_ok=True)

    valid_filename = re.sub(r'[<>:"/\\|?*]', '', product_name)
    valid_filename = valid_filename[:10]
    filepath = os.path.join(folder, valid_filename + '.jpg')

    base, ext = os.path.splitext(filepath)
    counter = 1
    while os.path.exists(filepath):
        filepath = f"{base}_{counter}{ext}"
        counter += 1

    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return filepath
    return None


def save_to_excel(data):
    df = pd.DataFrame(data)
    file_name = f"busquedas.xlsx"

    if os.path.exists(file_name):
        existing_df = pd.read_excel(file_name)
        df = pd.concat([existing_df, df], ignore_index=True)

    df.to_excel(file_name, index=False)
    return file_name


def get_search_results(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
    }

    url = f"https://www.amazon.com/s?k={query}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    product_links = []

    for product in soup.select("div[data-asin] a.a-link-normal.s-no-outline[href]"):
        href = product["href"]
        if href.startswith("/"):
            href = "https://www.amazon.com" + href
        product_links.append(href)

    return product_links


#Streamlit App
st.title("Producto Scraper de Amazon")

search_query = st.text_input("Introduce tu búsqueda en Amazon:")

if search_query:
    st.write(f"Resultados para: {search_query}")
    product_urls = get_search_results(search_query)

    if product_urls:
        all_data = []
        for url in product_urls[:10]:
            title, image_url, price = get_product_info(url)

            if title != 'No se encontró el título':
                data = {
                    'Fecha': datetime.now().strftime('%Y-%m-%d'),
                    'Titulo': title,
                    'Precio': price,
                    'URL Imagen': image_url,
                    'URL Producto': url
                }
                all_data.append(data)

                if image_url:
                    save_image(image_url, title)

        if all_data:
            df = pd.DataFrame(all_data)
            st.write("### Información de los Productos")
            st.dataframe(df.style.set_properties(**{'text-align': 'left'}).set_table_styles(
                [{'selector': 'th', 'props': [('text-align', 'left')]}]
            ))

            file_name = save_to_excel(all_data)
            st.success(f"Datos guardados en {file_name}")
        else:
            st.error("No se encontraron los productos válidos.")

    else:
        st.error("No se encontraron resultados para tu búsqueda.")


