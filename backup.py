from datetime import datetime



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
import os



# --- SETUP FIREFOX DRIVER ---
service = Service(executable_path="C:/Repos/Utils/geckodriver.exe")
options = Options()
# options.headless = False  # Set to True if you don't need the browser window
#hide firefox window
# os.environ['MOZ_HEADLESS'] = '1'

def add_increment_column(df):
    if df.empty:
        df["Increment"] = []
        return df

    # Clean and convert 'Current Price' to float
    df["Current Price"] = (
        df["Current Price"]
        .astype(str)
        .str.replace(r"[^\d.,]", "", regex=True)  # Remove currency symbols or other chars
        .str.replace(",", ".")                    # Handle decimal commas 
        .astype(float)
    )

    min_price = df["Current Price"].min()

    df["Increment"] = ((df["Current Price"] - min_price) / min_price * 100).round(2).astype(str) + " %"
    
    # Back to string + € / %
    # df["Increment"] = df["Increment"].astype(str) + " %"
    df["Current Price"] = df["Current Price"].round(2).astype(str) + " €"
    
    return df

def getBookResults(query, bookLimit):
    driver = webdriver.Firefox(service=service, options=options)
    url = "https://www.casadellibro.com"
    driver.get(url)

    time.sleep(2)  # Wait for dynamic content to load
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

    # Interact with right side panel ('Ordenar por)
    # Open right side panel 
    rightPanel = shadow_root1.find_element(By.CSS_SELECTOR, 'button[data-test="toggle-facets-button"]')
    rightPanel.click()
    time.sleep(0.2)
    # Sort 
    sortButton = shadow_root1.find_element(By.CSS_SELECTOR, 'div[data-test="sort"]')
    sortButton.click()
    time.sleep(0.2)
    for checkbox in sortButton.find_elements(By.CSS_SELECTOR, 'button[data-test="sort-picker-button"]'):
        if checkbox.text == 'Precio: De menor a mayor':
            checkbox.click()
    time.sleep(2)
    # Availability dropdown
    # availability = shadow_root1.find_element(By.CSS_SELECTOR, 'div[data-test="availability"]')
    try:
        availability = shadow_root1.find_element(By.CSS_SELECTOR, 'div[data-test="availability"]')
        
        availability.click()
        time.sleep(1.5)
        # Look for "available" checkbox and click it (the checkbox order changes with the query)
        for checkbox in availability.find_elements(By.CSS_SELECTOR, 'button[data-test="filter"]'):
            print(checkbox.text)
            if 'disponible' in checkbox.text:
                checkbox.click()
                print('click')
                break
        time.sleep(1.5)
    except NoSuchElementException:
        print('Filtro de disponibilidad no encontrado')
         
    # --- FIND ALL BOOK RESULT CARDS ---
    ###########################
    #     # --- EXPAND SHADOW DOM ROOT ---
    # def expand_shadow_element(element):
    #     shadow_root = driver.execute_script("return arguments[0].shadowRoot", element)
    #     return shadow_root

    # root1 = driver.find_element(By.XPATH, "//div[@class='x-root-container']")
    # shadow_root1 = expand_shadow_element(root1)
    # ##########################
    results = shadow_root1.find_elements(By.CSS_SELECTOR, "li.x-base-grid__item")
    books = []
    bookDf = pd.DataFrame()
    i=0
    for result in results:
        if i == bookLimit:
            break
        i+=1
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
                if not current_price:
                    print('Exception price empty 1')
                    continue
            except NoSuchElementException:
                print('Exception no price found 1')
                continue

            # Price (original)
            try:
                original_price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-previous-price"]')
                original_price = original_price_elem.text.strip()
            except NoSuchElementException:
                original_price = current_price

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
                "Link url": link,
                "Store": "Casa del libro"
            })
            print(len(books))
            bookDf = pd.DataFrame(books)
        except Exception as e:
            print(f"Error al obtener resultados de {url} : {e}")
    driver.close()
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 1 size: {bookDf.shape[0]}')
    return bookDf

def getBookResults2(query, bookLimit):
    books = []
    bookDf = pd.DataFrame()
    baseUrl = 'https://www.libreriacentral.com/'
    queryUrl = query.strip().replace(" ","+")
    url = f"{baseUrl}SearchResults.aspx?st={queryUrl}&cId=0&sm=qck"
    page = requests.get(url)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.find_all("div",class_="products-preview-list-item", limit=bookLimit)
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
                    #Book discarded if no price
                    continue
                print(current_price)
                # Image
                try:
                    img_url = baseUrl + result.find("img", class_='foto')['src']
                except e:
                    img_url = "N/A"
                print(img_url)
                #Link
                try:
                    link = result.find("a", attrs={"itemprop": "url"})["href"].strip()
                    link = baseUrl + link
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
                    "Link url": link,
                    "Store": "Librería central"
                })
                print(len(books))
                bookDf = pd.DataFrame(books)
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e}")
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 2 size: {bookDf.shape[0]}')
    return bookDf

# def getBookResults3(query, bookLimit):
#     books = []
#     baseUrl = 'https://www.iberlibro.com/'
#     queryUrl = query.strip().replace(" ","%20")
#     url = f"{baseUrl}servlet/SearchResults?cond=new&ds=20&fs=es&kn={queryUrl}&n=100046497&pt=book&rollup=on&sortby=2"
#     page = requests.get(url)
#     soup = BeautifulSoup(page.content,"html.parser")
#     results = soup.find_all("div",class_="products-preview-list-item")
#     i = 0
#     for result in results:
#         i+=1
#         print(i)
#         try:
#             #In stock? 
#             availability = result.find("span", class_='css-disponible')
#             if availability and result.find("span", class_='css-disponible').get_text().strip() == "Disponible":

#                 # Title
#                 name_element = result.find(attrs={"itemprop": "name"})
#                 title = name_element.get_text().strip()
#                 print(title)

#                 #Author
#                 author = result.find("meta", attrs={"itemprop": "author"})['content'].strip()
#                 print(author)
#                 detail = 'N/A'

#                 # Price 
#                 try:
#                     price_substrings = result.find("div", class_="precio").find_all("span")
#                     current_price = price_substrings[0].get_text().strip() +' '+price_substrings[1].get_text().strip()
#                     if len(price_substrings) > 2:
#                         original_price = price_substrings[2].get_text().strip() +' '+price_substrings[1].get_text().strip()
#                     else:
#                         original_price = current_price
#                 except e:
#                     #Book discarded if no price
#                     continue
#                 print(current_price)
#                 # Image
#                 try:
#                     img_url = baseUrl + result.find("img", class_='foto')['src']
#                 except e:
#                     img_url = "N/A"
#                 print(img_url)
#                 #Link
#                 try:
#                     link = result.find("a", attrs={"itemprop": "url"})["href"].strip()
#                     link = baseUrl + link
#                     print(link)
#                 except:
#                     link = "N/A"

#                 books.append({
#                     "Title": title,
#                     "Author": author,
#                     "Detail": detail,
#                     "Original Price": original_price,
#                     "Current Price": current_price,
#                     "Image url": img_url,
#                     "Link url": link
#                 })
#                 bookDf = pd.DataFrame(books).sort_values("Current Price", axis=0, ascending=False, inplace=True, na_position='last')
#         except Exception as e:
#             print(f"Error al obtener resultados: {e}")
#     return bookDf.truncate(after=bookLimit)


def drawDfTable(inputDf,dfkey):

    st.data_editor(
        inputDf,
        use_container_width=True,
        column_config={
            "Image url": st.column_config.ImageColumn(
                "Cubierta", 
                width="small",
                help="Doble click para ampliar"
            ),
            "Link url": st.column_config.LinkColumn(
                "Enlace", 
                display_text=r"https://www.(.*?)\.com"
            ),
            "Detail": st.column_config.TextColumn("Detalle"),
            "Original Price": st.column_config.TextColumn("Precio original"),
            "Current Price": st.column_config.TextColumn("Precio final"),
            "Author": st.column_config.TextColumn("Autor"),
            "Title": st.column_config.TextColumn("Título"),
            "Increment" : st.column_config.TextColumn("Incremento %"),
            
        },
        # column_order=['Título','Autor','Detalle','Precio original','Precio final','Increment','Cubierta','Enlace'],
        key=dfkey
        # hide_index=True
    )

def getSortedResults(fetch_func, query, bookLimit):
    df = fetch_func(query, bookLimit)
    if not df.empty and 'Current Price' in df.columns:
        return df.sort_values(by='Current Price', ignore_index=True)
    return df

def obtenerResultados(query, bookLimit):

    if query.strip():
        print('INICIO____________________________________________________________________')
        with st.spinner("Buscando libros..."):
            try:
                #Lista de funciones por cada tienda
                fetchFuncs = [getBookResults, getBookResults2]
                dfs = [getSortedResults(f, query, bookLimit) for f in fetchFuncs]
                if not dfs:
                    st.warning("No results found.")
                else:
                    # If 0 or 1 result per store, draw only one table
                    # Draw reduced table with first result from each store
                    # reducedBookDf = pd.concat([df.iloc[[0]] for df in dfs if not df.empty], ignore_index=True)
                    reducedBookDf = add_increment_column(pd.concat([df.iloc[[0]] for df in dfs if not df.empty], ignore_index=True))
                    st.markdown("#### 📘 Los resultados más baratos de cada tienda:")
                    drawDfTable(reducedBookDf, 'Reduced')
                    
                    # Show summary
                    
                    st.markdown("*Resumen de resultados por tienda:*")
                    for df in dfs:
                        
                        if not df.empty:
                            store_name = df['Store'].iloc[0]
                            st.write(f"  - {store_name}: {len(df)} resultados")

                    # if len(dfs) > 2 or any(df.shape[0] > 1 for df in dfs):
                    if any(df.shape[0] > 1 for df in dfs) and bookLimit > 1:
                        # Draw expanded table with the rest (up to bookLimit)
                        expandedDfs = [df.iloc[1:bookLimit] for df in dfs if df.shape[0] > 1]
                        if expandedDfs:
                            st.markdown("#### 📚 Resultados adicionales por tienda:")
                            # bookDf = pd.concat(expandedDfs, ignore_index=True).sort_values(by='Current Price', ignore_index=True)
                            bookDf = pd.concat(expandedDfs, ignore_index=True).sort_values(by='Current Price', ignore_index=True)
                            drawDfTable(bookDf, 'Expanded')
            except Exception as e:
                st.error(f"An error occurred: {e}")
        print('FIN____________________________________________________________________')
    else:
        st.warning("Please enter a book title or ISBN.")

col1, col2 = st.columns(2)
with col1:
    query = st.text_input("Introducir ISBN, título, genero, autor:", "")
    placeholderButton = st.empty()
    
with col2:
    bookLimit = st.number_input("Introducir máximo de libros por tienda (max 20)", min_value=1, max_value=20)

if placeholderButton.button("🔍 Buscar"):
    # Get the current time
    current_time = datetime.now().time()

    # Print the current time
    print("Current Time:", current_time)
    obtenerResultados(query, bookLimit)





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