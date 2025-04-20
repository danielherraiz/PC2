

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
# import selenium
# import re
import time
# import scipy
# import os
# import json


# from RetoExtraSites.CasaDelLibro import getPrice_casaDelLibro

st.set_page_config(
    page_title="Price Comparer",
    page_icon=":book:",
    layout="wide"
    #layout="wide",
)

st.title("PC2 Reto Extra")
st.header("Daniel Herraiz")

# st.subheader("Casa Del Libro")
# st.write(getPrice_casaDelLibro())


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options

import time

# --- SETUP FIREFOX DRIVER ---
service = Service(executable_path="C:/Repos/Utils/geckodriver.exe")
options = Options()
# options.headless = False  # Set to True if you don't need the browser window

def getBookResults(query):
    driver = webdriver.Firefox(service=service, options=options)
    driver.get("https://www.casadellibro.com")

    time.sleep(3)  # Wait for dynamic content to load
    acceptCookies = driver.find_element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')
    acceptCookies.click()

    time.sleep(1) 

    search = driver.find_element(By.XPATH, "//input[@id='empathy-search']")
    search.send_keys(query)

    time.sleep(1) 

    # --- EXPAND SHADOW DOM ROOT ---
    def expand_shadow_element(element):
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", element)
        return shadow_root

    root1 = driver.find_element(By.XPATH, "//div[@class='x-root-container']")
    shadow_root1 = expand_shadow_element(root1)

    # --- FIND ALL BOOK RESULT CARDS ---
    results = shadow_root1.find_elements(By.CSS_SELECTOR, "li.x-base-grid__item")

    books = []

    for result in results:
        try:
            article = result.find_element(By.CSS_SELECTOR, "article")
            
            # Title
            titles = article.find_elements(By.CSS_SELECTOR, 'h2[data-test="result-title"]')
            title = titles[0].text if titles else "N/A"

            #Author
            author = titles[1].text if len(titles) > 1 else "N/A"

            #Detail
            try:
                detail_el = article.find_elements(By.CSS_SELECTOR, 'span.x-text1.x-text1-sm.x-font-bold.x-text-lead-50')
                detail = detail_el[0].text.strip() if detail_el else "N/A"
            except NoSuchElementException:
                detail = "N/A"

            # Price (Current)
            try:
                price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-current-price"]')
                current_price = price_elem.text.strip()
            except NoSuchElementException:
                current_price = "N/A"

            # Price (original)
            try:
                original_price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-previous-price"]')
                original_price = original_price_elem.text.strip()
            except NoSuchElementException:
                original_price = current_price  # fallback

            # Image
            try:
                img_elem = article.find_element(By.CSS_SELECTOR, 'img[data-test="result-picture-image"]')
                img_url = img_elem.get_attribute("src")
            except NoSuchElementException:
                img_url = "N/A"

            #Link
            try:
                link_el = article.find_element(By.CSS_SELECTOR, 'a[data-test="result-link"]')
                link = link_el.get_attribute("href")
                print(link)
            except:
                link = "N/A"

            books.append({
                "Title": title,
                "Author": author,
                "Detail": detail,
                "Original Price": original_price,
                "Current Price": current_price,
                "Image url": img_url,
                "Link url": link
            })

        except Exception as e:
            print(f"Error parsing book: {e}")

    # --- PRINT RESULTS ---
    driver.close()
    return books
    # df1['Image'] = df1['Image URL'].apply(lambda x: f'<img src="{x}" width="60">')  # Adjust image size as needed
    # df1['Link'] = df1['Book URL'].apply(lambda x: f'<a href="{x}" target="_blank">View Book</a>')

    # df1['Image'] = df1['Image'].apply(lambda x: f'<img src="{x}" width="60">' if x else "")
    # df1['Link'] = df1['Link'].apply(lambda x: f'<a href="{x}" target="_blank">View Book</a>' if x else "")
    # df1 = df1[['Title', 'Author', 'Original Price', 'Current Price', 'Image', 'Link']]

    # st.write(df1.to_html(escape=False, index=False), unsafe_allow_html=True)
    # st.dataframe(df1)



    # from bs4 import BeautifulSoup
def getBookResults2(query):
    books = []
    queryUrl = query.strip().replace(" ","+")
    url = f"https://www.libreriacentral.com/SearchResults.aspx?st={queryUrl}&cId=0&sm=qck"
    page = requests.get(url)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.find_all("div",class_="products-preview-list-item")
    i = 0
    for result in results:
        i+=1
        print(i)
        try:
            #In stock? 
            availability = result.find("span", class_='css-disponible')
            if availability and result.find("span", class_='css-disponible').get_text().strip() == "Disponible":

                # Title
                name_element = result.find(attrs={"itemprop": "name"})
                title = name_element.get_text().strip()
                print(title)

                #Author
                author = result.find("meta", attrs={"itemprop": "author"})['content'].strip()
                print(author)
                detail = 'N/A'

                # Price 
                try:
                    price_substrings = result.find("div", class_="precio").find_all("span")
                    current_price = price_substrings[0].get_text().strip() +' '+price_substrings[1].get_text().strip()
                    if len(price_substrings) > 2:
                        original_price = price_substrings[2].get_text().strip() +' '+price_substrings[1].get_text().strip()
                    else:
                        original_price = current_price
                except e:
                    current_price = "N/A"
                    original_price = "N/A"
                print(current_price)
                # Image
                try:
                    img_url = result.find("img", class_='foto')['src']
                except e:
                    img_url = "N/A"

                #Link
                try:
                    link = result.find("a", attrs={"itemprop": "url"})["href"].strip()
                    print(link)
                except:
                    link = "N/A"

                books.append({
                    "Title": title,
                    "Author": author,
                    "Detail": detail,
                    "Original Price": original_price,
                    "Current Price": current_price,
                    "Image url": img_url,
                    "Link url": link
                })
        except Exception as e:
            print(f"Error al obtener resultados: {e}")
    return books


# from urllib.parse import urljoin

# # def getLibreriaCentralResults():
#     isbn2 = '9788478884452'
#     url = f"https://www.casadellibro.com/?query={isbn}"
#     print(url)
#     page = requests.get(url)
#     soup = BeautifulSoup(html, 'html.parser')
#     results = []

#     # Each book is within a Product schema tag
#     products = soup.find_all('div', itemtype="http://schema.org/Product")

#     for product in products:
#         title = product.find(itemprop="name")
#         author_meta = product.find('meta', itemprop="author")
#         price = product.find('span', itemprop="price")
#         currency = product.find('span', itemprop="priceCurrency")
#         image = product.find('img', itemprop="image")
#         isbn = product.find('meta', itemprop="isbn")
#         url = product.find('a', itemprop="url")
#         availability = product.find('link', itemprop="availability")

#         data = {
#             'title': title.get_text(strip=True) if title else None,
#             'author': author_meta['content'].strip() if author_meta else None,
#             'price': price.get_text(strip=True) if price else None,
#             'currency': currency['content'].strip() if currency else None,
#             'image_url': urljoin(base_url, image['src']) if image else None,
#             'isbn': isbn['content'].strip() if isbn else None,
#             'product_url': urljoin(base_url, url['href']) if url else None,
#             'availability': availability['href'].split('/')[-1] if availability else None
#         }

#         results.append(data)

#     return results
#     st.data_editor(
#         df1,
#         use_container_width=True,
#         column_config={
#             "Image url": st.column_config.ImageColumn(
#                 "Cubierta", 
#                 width="small"
#             ),
#             "Link url": st.column_config.LinkColumn(
#                 "Enlace", 
#                 display_text=r"https://www.(.*?)\.com"
#             ),
#             "Detail": st.column_config.TextColumn("Detalle"),
#             "Original Price": st.column_config.TextColumn("Precio original"),
#             "Current Price": st.column_config.TextColumn("Precio final"),
#             "Author": st.column_config.TextColumn("Autor"),
#             "Title": st.column_config.TextColumn("Título")
#         }
#     )
#     driver.close()

query = st.text_input("Introducir ISBN, título, genero, autor:", "")
if st.button("🔍 Buscar"):
    if query.strip():
        with st.spinner("Buscando libros..."):
            try:
                bookFinalList = []
                booklist1=getBookResults(query)
                booklist2=getBookResults2(query)
                bookFinalList.extend(booklist1)
                bookFinalList.extend(booklist2)
                
                st.data_editor(
                    pd.DataFrame(bookFinalList),
                    use_container_width=True,
                    column_config={
                        "Image url": st.column_config.ImageColumn(
                            "Cubierta", 
                            width="small"
                        ),
                        "Link url": st.column_config.LinkColumn(
                            "Enlace", 
                            display_text=r"https://www.(.*?)\.com"
                        ),
                        "Detail": st.column_config.TextColumn("Detalle"),
                        "Original Price": st.column_config.TextColumn("Precio original"),
                        "Current Price": st.column_config.TextColumn("Precio final"),
                        "Author": st.column_config.TextColumn("Autor"),
                        "Title": st.column_config.TextColumn("Título")
                    }
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a book title or ISBN.")









# isbn = '9788478884452'
# url = f"https://www.casadellibro.com/?query={isbn}"
# driver = webdriver.Firefox(service=service, options=options)
# driver.get(url)

# def expand_shadow_element(element):
#     shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
#     return shadow_root

# root1 = driver.find_element(By.XPATH, "//div[@class='x-root-container']")
# print(root1)
# shadow_root1 = expand_shadow_element(root1)

# try:
#     bookPrice2 = shadow_root1.find_element(By.CSS_SELECTOR, 'div[data-test="result-current-price"]')
#     print("Element found:", bookPrice2.text)
# except NoSuchElementException:
#     print("Element not found.")

# print(bookPrice1[0].text)