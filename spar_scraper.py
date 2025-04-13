from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import os
import csv
from urllib.parse import urlparse


def open_vse_kategorije(driver, wait):
    driver.get("https://www.spar.si/online/")
    time.sleep(1)
    
    # Handle cookie and welcome popups again if needed
    try:
        welcome_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "onboarding-popup__close-button")))
        driver.execute_script("arguments[0].click();", welcome_button)
    except:
        pass
    
    try:
        vse_kategorije_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "main-navigation__toggle")))
        vse_kategorije_button.click()
        print("✅ Opened 'Vse kategorije'")
        time.sleep(2)
    except Exception as e:
        print("❌ Failed to open 'Vse kategorije':", e)


if __name__ == "__main__":
    # Setup
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.spar.si/online/")
    wait = WebDriverWait(driver, 5)

    # === Close Cookie Popup via Shadow DOM ===
    try:
        print("🌐 Accessing shadow DOM and finding ❌ close button...")
        success = driver.execute_script("""
            const host = document.querySelector("#cmpwrapper");
            if (!host || !host.shadowRoot) return false;

            const box = host.shadowRoot.querySelector("#cmpbox");
            if (!box) return false;

            const closeBtn = box.querySelector("div.cmpclose > a");
            if (!closeBtn) return false;

            closeBtn.click();
            return true;
        """)

        if success:
            print("✅ Cookie popup closed via Shadow DOM.")
        else:
            print("❌ Failed to locate and click close button via JS.")
    except Exception as e:
        print("❌ JavaScript error while trying to close cookie popup:", e)

    # === Close Welcome Modal (Onboarding) ===
    try:
        print("🔍 Looking for welcome modal close button...")
        welcome_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "onboarding-popup__close-button")))
        driver.execute_script("arguments[0].click();", welcome_button)
        print("✅ Welcome modal closed.")
    except Exception as e:
        print("❌ Failed to close welcome popup:", e)

    # ✅ Ready to Scrape
    print("🎉 All popups handled. Let's go scrape some groceries!")


    #########################################################################################################################
    # === Scraping Logic ===
    #########################################################################################################################

    data = []
    all_data = []

    # === Step 1: Get all top-level categories ===
    top_categories = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "a.flyout-categories__link[data-level='1']")))
    
    # ✅ Keep only first 10 relevant categories
    top_categories = top_categories[:10]

    print(f"🔍 Found {len(top_categories)} top-level categories.")
    # Loop over top-level categories
    for top_index in range(0, 1):  # Change this to 1 for testing
        # open_vse_kategorije(driver, wait)
        time.sleep(1)
        
        top_category = top_categories[top_index]
        top_category_name = top_category.find_element(By.CLASS_NAME, "ellipsisText").text.strip()
        if not top_category_name:
            top_category_name = "Unknown"

        driver.execute_script("arguments[0].click();", top_category)
        time.sleep(1)

        # ✅ Step 1: Collect subcategory URLs (NO scraping yet)
        subcat_elements = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a.flyout-categories__link[data-level='3'][data-has-parents='false']")))

        
        # ✅ Step 1: Collect subcategory URLs including mid-level info
        subcat_links = []
        mid_level_sections = driver.find_elements(By.CSS_SELECTOR, "li.flyout-categories__item[data-level='2']")

        print(f"🔍 Found {len(mid_level_sections)} mid-level categories.")

        for mid_section in mid_level_sections:
            try:
                mid_name = mid_section.find_element(By.CLASS_NAME, "ellipsisText").text.strip()

                third_level_links = mid_section.find_elements(By.CSS_SELECTOR, "ul > li.flyout-categories__item[data-level='3'] > a")

                for subcat in third_level_links:
                    try:
                        subcat_name = subcat.find_element(By.CLASS_NAME, "ellipsisText").text.strip()
                        subcat_url = subcat.get_attribute("href")

                        if subcat_url and not subcat_url.startswith("javascript"):
                            # Append subcat_links only if it's a real URL


                            parsed = urlparse(subcat_url)
                            path_parts = parsed.path.strip("/").split("/")  # removes leading/trailing slashes
                            # Example: ['online', 'sadje-in-zelenjava', 'sveza-zelenjava', 'solata-radic-spinaca', 'c', 'S1-1-3']

                            category_name = path_parts[1].replace("-", " ") if len(path_parts) > 1 else ""
                            mid_level_name = path_parts[2].replace("-", " ") if len(path_parts) > 2 else ""
                            subcategory_url_segment = path_parts[3].replace("-", " ") if len(path_parts) > 3 else ""

                            # Now append them all
                            subcat_links.append({
                                "category": category_name,
                                "mid_level": mid_level_name,
                                "subcategory": subcat_name,  # this still comes from visible link text!
                                "url": subcat_url
                            })

                    except Exception as e:
                        print(f"⚠️ Failed to parse subcategory inside {mid_name}: {e}")
                        continue
            except Exception as e:
                print("⚠️ Failed to parse mid-level category:", e)
                continue
  
        # ✅ Step 2: Loop over fresh links
        skipped_first_category = False
        previous_top_category_name = None
        top_categories_count = 0

        for link in subcat_links:

            current_top_category_name = link["category"]

            # ✅ If this is a new top category, save old data first
            if previous_top_category_name and current_top_category_name != previous_top_category_name:

                top_categories_count += 1

                if data:
                    safe_name = "".join(c for c in previous_top_category_name.lower().replace(" ", "_") if c.isalnum() or c in "_-")
                    filename = f"spar_{safe_name}.csv"
                    with open(filename, "w", newline='', encoding="utf-8") as f:
                        fieldnames = [
                            "store", "category", "mid_category",
                            "product_id", "name", "price", "discount", "url"
                        ]
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
                    print(f"💾 Saved {len(data)} products to {filename}")
                    data.clear()

            previous_top_category_name = current_top_category_name
            # stop after 10 categories for testing
            if top_categories_count >= 10:
                print("🛑 Reached 10 categories, stopping early for testing.")
                break

            try:
                subcat_url = link["url"]
                category_name = link["category"]
                mid_level_name = link["mid_level"]
                subcat_name = link["subcategory"]

                top_category_name = category_name # This is the top category name
                print(f"!!!! top_category_name : {top_category_name}")
    
                print(f"➡️  Going to {subcat_name}: {subcat_url}")
                driver.get(subcat_url)
                time.sleep(1)

                # Step 3: 
                product_links = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "a[data-id][href*='/p/']")))
                
                product_urls = []
                seen = set()
                url_count = 0

                for link in product_links:
                    # only get the first 5 product links
                    if url_count >= 5:
                        break
                    url = link.get_attribute("href")
                    if url and url not in seen:
                        product_urls.append(url)
                        seen.add(url)
                        url_count += 1

                print(f"🛍 Found {len(product_urls)} products on {subcat_name}.")

                # Step 4: Scrape product details
                for product_url in product_urls:
                    try:
                        print(f"🛒 Opening product: {product_url}")
                        driver.get(product_url)
                        time.sleep(0.5)

                        name = wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "label.productDetailsName"))).text.strip()
                        name = name.replace("\n", "; ").replace("\r", "").strip()

                        try:
                            price = driver.find_element(By.CSS_SELECTOR, "label.productDetailsPrice").text.strip()
                        except:
                            price = ""

                        try:
                            discount = driver.find_element(By.CSS_SELECTOR, "label.productDetailsOldPrice").text.strip()
                            if discount == "":
                                discount = None
                        except:
                            discount = None

                        try:
                            product_id_text = driver.find_element(By.CLASS_NAME, "productDetailsArticleNumber").text
                            product_id = product_id_text.split(":")[-1].strip()
                        except:
                            product_id = None

                        data.append({
                            "store": "Spar",
                            "category": category_name,
                            "mid_category": mid_level_name,
                            # "subcategory": subcat_name,
                            "product_id": product_id,
                            "name": name,
                            "price": price,
                            "discount": discount,
                            "url": product_url
                        })

                        all_data.append({
                            "store": "Spar",
                            "category": category_name,
                            "mid_category": mid_level_name,
                            # "subcategory": subcat_name,
                            "product_id": product_id,
                            "name": name,
                            "price": price,
                            "discount": discount,
                            "url": product_url
                        })

                        print(f"✅ Added product: {name}")           

                    except Exception as e:
                        print(f"❌ Failed to scrape product at {product_url}: {e}")
                        continue

            except Exception as e:
                print(f"⚠️ Failed to scrape subcategory '{link.get('subcategory', 'unknown')}':", e)

                continue
            

        # === Save to CSV ===
        print(f"🔢 Collected {len(all_data)} products for category: {top_category_name}")

        if all_data:
            filename = f"spar_{top_category_name.lower().replace(' ', '_')}.csv"
            with open(filename, "w", newline='', encoding="utf-8") as f:

                fieldnames = [
                    "store", "category", "mid_category",
                    "product_id", "name", "price", "discount", "url"
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)

            print(f"💾 Saved to {filename}")
        else:
            print("❌ No data collected.")


    driver.quit()