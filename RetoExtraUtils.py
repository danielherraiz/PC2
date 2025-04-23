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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.firefox.options import Options

import time
import os

import traceback
import re


# --- SETUP FIREFOX DRIVER ---
service = Service(executable_path="C:/Repos/Utils/geckodriver.exe")
options = Options()
# options.headless = False  # Set to True if you don't need the browser window
#hide firefox window
# os.environ['MOZ_HEADLESS'] = '1'

## FUNCTIONS TO OBTAIN CONTENT FROM BOOK STORES ##

def getBooksCasaLibro(query, bookLimit):
    driver = webdriver.Firefox(service=service, options=options)
    url = "https://www.casadellibro.com"
    driver.get(url)
    driver.implicitly_wait(5)

    # time.sleep(2)  # Wait for dynamic content to load
    acceptCookies = driver.find_element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')
    acceptCookies.click()
    # time.sleep(1) 

    search = driver.find_element(By.XPATH, "//input[@id='empathy-search']")
    search.send_keys(query)

    # --- EXPAND SHADOW DOM ROOT ---
    # def expand_shadow_element(element):
    #     
    #     return shadow_root

    root1 = driver.find_element(By.XPATH, "//div[@class='x-root-container']")
    # shadow_root1 = expand_shadow_element(root1)
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", root1)
    # time.sleep(0.5)
    # Interact with right side panel ('Ordenar por)
    # Open right side panel 
    rightPanel = shadow_root.find_element(By.CSS_SELECTOR, 'button[data-test="toggle-facets-button"]')
    rightPanel.click()
    # time.sleep(0.2)
    # Sort 
    sortButton = shadow_root.find_element(By.CSS_SELECTOR, 'div[data-test="sort"]')
    sortButton.click()
    # time.sleep(0.2)
    for checkbox in sortButton.find_elements(By.CSS_SELECTOR, 'button[data-test="sort-picker-button"]'):
        if checkbox.text == 'Precio: De menor a mayor':
            checkbox.click()
    # time.sleep(2)
    # Availability dropdown
    try:
        availability = shadow_root.find_element(By.CSS_SELECTOR, 'div[data-test="availability"]')
        
        availability.click()
        # time.sleep(1.5)
        # Look for "available" checkbox and click it (the checkbox order changes with the query)
        for checkbox in availability.find_elements(By.CSS_SELECTOR, 'button[data-test="filter"]'):
            print(checkbox.text)
            if 'disponible' in checkbox.text:
                checkbox.click()
                print('click')
                break
        # time.sleep(1.5)
    except (NoSuchElementException , TimeoutException) as e:
        print(e.args)
    
    time.sleep(1.5)
    results = shadow_root.find_elements(By.CSS_SELECTOR, "li.x-base-grid__item")
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
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                detail = "N/A"

            # Price (Current)
            try:
                price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-current-price"]')
                current_price = price_elem.text.strip()
                if not current_price:
                    print('Exception price empty 1')
                    continue
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                print('Exception no price found 1')
                
                continue

            # Price (original)
            try:
                original_price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-previous-price"]')
                original_price = original_price_elem.text.strip()
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                original_price = current_price

            # Image
            try:
                img_elem = article.find_element(By.CSS_SELECTOR, 'img[data-test="result-picture-image"]')
                img_url = img_elem.get_attribute("src")
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                img_url = "N/A"

            #Link
            try:
                link_el = article.find_element(By.CSS_SELECTOR, 'a[data-test="result-link"]')
                link = link_el.get_attribute("href")
                print(link)
            except:
                link = "N/A"

            books.append({
                "Título": title,
                "Autor": author,
                "Detalle": detail,
                "Precio base": original_price,
                "Precio final": current_price,
                "Cubierta": img_url,
                "Enlace": link,
                "Tienda": "Casa del libro"
            })
            print(len(books))
            bookDf = pd.DataFrame(books)
        except Exception as e:
            print(f"Error al obtener resultados de {url} : {e}")
    driver.close()
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 1 size: {bookDf.shape[0]}')
    return bookDf

def getBooksLibCentral(query, bookLimit):
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
                    "Título": title,
                    "Autor": author,
                    "Detalle": detail,
                    "Precio base": original_price,
                    "Precio final": current_price,
                    "Cubierta": img_url,
                    "Enlace": link,
                    "Tienda": "Librería central"
                })
                print(len(books))
                bookDf = pd.DataFrame(books)
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e}")
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 2 size: {bookDf.shape[0]}')
    return bookDf

def getBooksIberLibro(query, bookLimit):
    bookDf = pd.DataFrame()
    books = []
    baseUrl = 'https://www.iberlibro.com/'
    queryUrl = query.strip().replace(" ","%20")
    # url = f"{baseUrl}servlet/SearchResults?cond=new&ds=20&fs=es&kn={queryUrl}&n=100046497&pt=book&rollup=on&sortby=2"
    url = f"{baseUrl}servlet/SearchResults?ch_sort=t&cm_sp=sort-_-SRP-_-Results&cond=new&ds=20&fs=es&kn={queryUrl}&n=100046497&pt=book&rollup=on&sortby=2"
    page = requests.get(url)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.find_all("li",class_="cf result-item")
    i = 0
    for result in results:
        i+=1
        print(i)
        try:
            # Title
            title = result.find(attrs={"itemprop": "name"})['content'].strip()
            # title = name_element.get_text().strip()
            print(title)

            #Author
            author = result.find("meta", attrs={"itemprop": "author"})['content'].strip()
            print(author)
            detail = result.find("meta", attrs={"itemprop": "about"})['content']
            detail = re.split(r'Condic.*', detail)[0].strip()
            print(author)
            # Price 
            try:
                current_price = result.find("p", class_="item-price").text
                
                original_price = current_price
            except Exception as e:
                #Book discarded if no price
                continue
            print(current_price)
            # Image
            try:
                img_url = result.find("img", class_='srp-item-image')['src'].strip()
                # img_url = result.find("img", class_="srp-item-image")['src'].strip()
            except Exception as e:
                img_url = "N/A"
            print(img_url)
            #Link
            try:
                link = result.find("a", attrs={"itemprop": "url"})["href"].strip()
                link = baseUrl + link
                print(link)
            except Exception as e:
                link = "N/A"

            books.append({
                "Título": title,
                "Autor": author,
                "Detalle": detail,
                "Precio base": original_price,
                "Precio final": current_price,
                "Cubierta": img_url,
                "Enlace": link,
                "Tienda": "Iber Libro"
            })
            print(len(books))
            bookDf = pd.DataFrame(books)
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e}")
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 3 size: {bookDf.shape[0]}')
    return bookDf


## FUNCTIONS FOR DATA MANIPULATION ##

def add_increment_column(df, min_price):
    try:
        if df.empty:
            df["Incremento %"] = []
            return df
        if(min_price==-1):
            min_price = df["Precio final"].min()
        
        df["Incremento %"] = ((df["Precio final"] - min_price) / min_price * 100).round(2).astype(str) + " %"
        df["Precio base"] = df["Precio base"].str.replace(",", ".").replace(r"[^\d.,]", "", regex=True) + " €"
        df["Precio final"] = df["Precio final"].round(2).astype(str) + " €"
    except Exception as e:
        traceback.print_exc()
    return df, min_price

def sortResults(df):
    #Apply float format so the sorting works properly
    if not df.empty and 'Precio final' in df.columns:
        df["Precio final"] = (
        df["Precio final"]
        .astype(str)
        .str.replace(r"[^\d.,]", "", regex=True)  # Remove currency symbols or other chars
        .str.replace(",", ".")                    # Handle decimal commas 
        .astype(float)
    )
    return df.sort_values(by='Precio final', ignore_index=True)

def getResults(fetch_func, query, bookLimit):
    df = fetch_func(query, bookLimit)
    return sortResults(df)