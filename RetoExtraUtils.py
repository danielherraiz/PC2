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
from datetime import datetime

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
options.add_argument("-private")
driver = webdriver.Firefox(service=service, options=options)
# options.headless = False  # Set to True if you don't need the browser window
#hide firefox window
# os.environ['MOZ_HEADLESS'] = '1'

## FUNCTIONS TO OBTAIN CONTENT FROM BOOK STORES ##

def getBooksCasaLibro(query, bookLimit, ebook, itemCondition):
    # driver = webdriver.Firefox(service=service, options=options)
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
            if re.search(r"disponible", checkbox.text, re.IGNORECASE):
                checkbox.click()
                break
        # time.sleep(1.5)
    except (NoSuchElementException , TimeoutException) as e:
        print(e.args)
    
    time.sleep(0.5)
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", root1)
    results = shadow_root.find_elements(By.CSS_SELECTOR, "li.x-base-grid__item")
    time.sleep(0.5)
    books = []
    bookDf = pd.DataFrame()
    i=0
    driver.implicitly_wait(0.5)
    for result in results:
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

            # Image
            try:
                img_elem = article.find_element(By.CSS_SELECTOR, 'img[data-test="result-picture-image"]')
                img_url = img_elem.get_attribute("src")
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                img_url = "N/A"

            #Previous version
            #Link
            try:
                link_el = article.find_element(By.CSS_SELECTOR, 'a[data-test="result-link"]')
                link = link_el.get_attribute("href")
                print(link)
            except:
                link = "N/A"
                
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

            # # Price (original)
            try:
                original_price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-previous-price"]')
                original_price = original_price_elem.text.strip()
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                original_price = current_price

            books.append({
                "Título": title,
                "Autor": author,
                "Comentarios": detail,
                "Precio base": original_price,
                "Precio final": current_price,
                "Cubierta": img_url,
                "Enlace": link,
                "Tienda": "Casa del libro"
            })
            print(len(books))
            
        except Exception as e:
            print(f"Error al obtener resultados de {url} : {e}")
        if len(books) == bookLimit:
            break
    bookDf = pd.DataFrame(books)
    # driver.close()
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 1 size: {bookDf.shape[0]}')
    return bookDf

def getBooksLibCentral(query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    baseUrl = 'https://www.libreriacentral.com/'
    queryUrl = query.strip().replace(" ","+")
    url = f"{baseUrl}SearchResults.aspx?st={queryUrl}&cId=0&sm=qck&sort=MEMA"
    page = requests.get(url)
    time.sleep(1)
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
                    "Comentarios": detail,
                    "Precio base": original_price,
                    "Precio final": current_price,
                    "Cubierta": img_url,
                    "Enlace": link,
                    "Tienda": "Librería central"
                })
                print(len(books))
                bookDf = pd.DataFrame(books)
            if len(books) == bookLimit:
                break
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e}")
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 2 size: {bookDf.shape[0]}')
    return bookDf

def getBooksIberLibro(query, bookLimit, ebook, itemCondition):
    bookDf = pd.DataFrame()
    books = []
    baseUrl = 'https://www.iberlibro.com/'
    queryUrl = query.strip().replace(" ","%20")
    # url = f"{baseUrl}servlet/SearchResults?cond=new&ds=20&fs=es&kn={queryUrl}&n=100046497&pt=book&rollup=on&sortby=2"
    url = f"{baseUrl}servlet/SearchResults?ch_sort=t&cm_sp=sort-_-SRP-_-Results&cond=new&ds=20&fs=es&kn={queryUrl}&n=100046497&pt=book&rollup=on&sortby=2"
    page = requests.get(url)
    time.sleep(0.5)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.find_all("li",class_="cf result-item",limit = bookLimit)
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
                "Comentarios": detail,
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
        if len(books) == bookLimit:
            break
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 3 size: {bookDf.shape[0]}')
    return bookDf

def getBooksAmazon(query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    
    url = "https://www.amazon.es/"
    driver.get(url)
    time.sleep(0.5)

    # time.sleep(2)  # Wait for dynamic content to load
    # acceptCookies = driver.find_element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')
    # acceptCookies.click()
    # time.sleep(1) 
    #cookies
    try:
        driver.find_element(By.ID, "sp-cc-accept").click()
    except:
        print("no cookies")

    driver.implicitly_wait(2)
    #Category button
    try:
        driver.find_element(By.ID, "searchDropdownBox").click()
        #Select books category
        driver.find_element(By.XPATH, "//option[@value='search-alias=stripbooks']").click()
        #Find search input and send query
        search = driver.find_element(By.XPATH, "//input[@id='twotabsearchtextbox']")
        search.send_keys(query)
        #Confirm search
        driver.find_element(By.XPATH, "//input[@id='nav-search-submit-button']").click()
    except:
        #Sometimes the category is not shown until a first search (page load is different)
        search0 = driver.find_element(By.ID, "nav-bb-search").click()
        search0.send_keys(query)
        driver.find_element(By.ID, "nav-bb-button").click()
        driver.find_element(By.ID, "searchDropdownBox").click()
        driver.find_element(By.XPATH, "//option[@value='search-alias=stripbooks']").click()
        
    if(itemCondition):
        for itemCondButton in driver.find_elements(By.ID, "p_n_condition-type/15144009031"):
            itemCondButton.click()
    
    #Check if there are any results. There might me results for other departments and 
    #give false positive, need to check the text message
    for resultMessage in driver.find_elements(By.XPATH, "//div[contains(@data-cel-widget,'search_result')]"):
        if 'No hay resultados para' in resultMessage.text:
            print('no hay resultados')
            driver.close()
            return bookDf
    # #Sort price ascending
    # driver.find_element(By.CSS_SELECTOR, "span[class='a-dropdown-prompt']").click()
    # time.sleep(0.3)
    try:
        driver.find_element(By.CSS_SELECTOR, "span[class='a-dropdown-container']").click()
    except:
        driver.close()
        return bookDf
    
    # time.sleep(0.3)
    driver.find_element(By.CSS_SELECTOR, "a[id='s-result-sort-select_1']").click()
    time.sleep(1)
    results = driver.find_elements(By.CSS_SELECTOR, "div[data-csa-c-type='item']")
    print(datetime.now().time())
    print(len(results))
    baseUrl = "https://www.amazon.es/"
    
    driver.implicitly_wait(0)
    i=0
    for result in results:
        i+=1
        try:
            title = result.find_element(By.CSS_SELECTOR, "h2[class='a-size-medium a-spacing-none a-color-base a-text-normal']").text
            #Authors might come with different class 
            try:
                author = result.find_element(By.CSS_SELECTOR, "a[class='a-size-base a-link-normal s-underline-text s-underline-link-text s-link-style']").text
            except Exception as e:
                try:
                    author = result.find_elements(By.CSS_SELECTOR, "span[class='a-size-base']")[1].text
                except:
                    continue
            try:
                img_url = result.find_element(By.CSS_SELECTOR, "img[class='s-image']").get_attribute("src")
                print(img_url)
            except:
                print('no image')
            #Different prices for different formats. Will be saved as different book results
            # i=0
            # All detail links
            detail_link_List = result.find_elements(By.XPATH, './/a[contains(@class,"a-text-bold")]')
            # All prices
            price_List = result.find_elements(By.XPATH, './/a[@aria-describedby="price-link"]')
            
            for i in range(len(price_List)):
                try:
                    detail = detail_link_List[i].text
                    if ("Kindle" in detail or "Audiolibro" in detail or "Pódcast" in detail) and ebook:
                        continue
                    link = detail_link_List[i].get_attribute("href")
                except:
                    detail = "N/A"
                    link = "N/A" 
                    print('no detail')     
                price_text = price_List[i].text.replace("\n", ".").replace(",", ".")
                match = re.match(r"(\d+[.]?\d*)", price_text)
                if match:
                    
                    current_price = float(match.group(1))
                    print(f"price match: {current_price}")
                try:
                    original_text = price_List[i].find_element(By.XPATH, './/span[@class="a-price a-text-price"]').text
                    match = re.match(r"(\d+[.]?\d*)", original_text.replace(",", "."))
                    if match:
                        original_price = str(match.group(1))
                        print(original_price)
                    else:
                        original_price = current_price
                except:
                    print(f"origin price exception: {current_price}")
                    original_price = current_price
                books.append({
                    "Título": title,
                    "Autor": author,
                    "Comentarios": detail,
                    "Cubierta": img_url,
                    "Enlace": link,
                    "Tienda": "Amazon",
                    "Precio base": original_price,
                    "Precio final": current_price
                })
                if len(books) == bookLimit:
                    break
        except Exception as e:
            print(f"Error procesando un resultado: {e}")
        if len(books) == bookLimit:
            break
            
    bookDf = pd.DataFrame(books)
    driver.close()
    print(f'tienda 3 size: {bookDf.shape[0]}')
    return bookDf
    
def getBooksEbay(query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    baseUrl = 'https://www.ebay.es/'
    queryUrl = query.strip().replace(" ","+")
    itemConditionParam = ''
    if(itemCondition):
        itemConditionParam = "&LH_ItemCondition=1000"
    url = f"{baseUrl}sch/i.html?_nkw={query}&_sacat=267&_from=R40&_sop=15&rt=nc{itemConditionParam}"

    page = requests.get(url)
    time.sleep(1)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.css.select('li[data-marko-key^="0 s0-55-0-9-8-4-4-0-3-0-4"]', limit=bookLimit)
    i = 0
    for result in results:
        i+=1
        print(i)
        try:
            # Title
            name_element = result.find("div", class_="s-item__title")
            title = name_element.get_text().strip()
            print(title)

            #Author
            author = 'N/A'
            print(author)
            detail_element = result.find("div", class_="s-item__subtitle")
            
            
            detail = detail_element.get_text().strip()
            if "|" in detail:
                detail = detail.split("|")[0]

            ##Commented because looking for shipping costs in all stores is way above scope (varies with the total order, location, etc)
            # shipping_element = result.find("span", class_="s-item__shipping s-item__logisticsCost").get_text()
            # print(shipping_element)
            # if "EUR" in shipping_element:
            #     # shipping_element_formatted = shipping_element.replace(",",".").replace(r"[^\d.,]", "", regex=True)
            #     shipping_element_formatted = re.sub(r"[^\d.]", "", shipping_element.replace(",", "."))
            #     detail = detail +'. '+ shipping_element_formatted + '€ envío'
            #     print(detail)
            # Price 
            try:
                price_element = result.find("span", class_="s-item__price")
                current_price = price_element.get_text().strip()
                original_price = current_price
            except:
                #Book discarded if no price
                continue
            print(current_price)
            # Image
            try:
                img_element = result.find("div", class_="s-item__image-wrapper image-treatment")
                img_url = img_element.find('img')["src"]
            except e:
                img_url = "N/A"
            print(img_url)
            #Link
            try:
                link = result.find("a", class_="s-item__link")["href"]
                print(link)
            except:
                link = "N/A"

            books.append({
                "Título": title,
                "Autor": author,
                "Comentarios": detail,
                "Precio base": original_price,
                "Precio final": current_price,
                "Cubierta": img_url,
                "Enlace": link,
                "Tienda": "eBay"
            })
            print(len(books))
            bookDf = pd.DataFrame(books)
            if len(books) == bookLimit:
                break
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e}")
            print(f"Error al obtener resultados de {baseUrl} : {e.args}")
    # return bookDf.truncate(after=bookLimit)
    print(f'tienda 5 size: {bookDf.shape[0]}')
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
        print('sorted')
        return df.sort_values(by='Precio final', ignore_index=True)
    else:
        print('no sorted')
        return df

def getResults(fetch_func, query, bookLimit, ebook, itemCondition):
    df = fetch_func(query, bookLimit, ebook, itemCondition)
    return sortResults(df)