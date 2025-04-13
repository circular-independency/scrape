from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from collections import defaultdict
import os
import re


def close_cookie_popup(driver, wait):
    try:
        print("🍪 Looking for cookie popup...")
        allow_all_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.iCDacceptallbtn.lib-cc-accept-all"))
        )
        allow_all_btn.click()
        print("✅ Cookie popup closed.")
    except Exception as e:
        print("❌ Failed to close cookie popup:", e)

def close_welcome_popup(driver, wait):
    try:
        print("🙋 Looking for welcome/onboarding popup...")
        close_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.close.lib-popup-button-close"))
        )
        close_btn.click()
        print("✅ Welcome popup closed.")
    except Exception as e:
        print("❌ Failed to close welcome popup:", e)


def close_email_popup(driver, wait):
    try:
        print("📧 Looking for email signup popup...")
        close_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.lib-popup-content a.lib-popup-button-close, div.lib-popup-content button[aria-label='Zapri']"))
        )
        close_btn.click()
        print("✅ Email signup popup closed.")
    except Exception as e:
        print("⚠️ Email signup popup not found or already closed.")



def extract_categories(driver):
    print("📦 Extracting categories from 'Vsi Izdelki' page...")
    categories_data = []

    try:
        root_ul = driver.find_element(By.CSS_SELECTOR, "ul.lib-categories:not(.lib-categories-template)")
        li_elements = root_ul.find_elements(By.XPATH, ".//li")

        for li in li_elements:
            try:
                link = li.find_element(By.CSS_SELECTOR, "a.lib-filters-category-change")
                label_full = link.get_attribute("data-analytics-label-expanded")  # e.g., "A;B;C"
                label_parts = label_full.split(";") if label_full else []

                category = label_parts[0] if len(label_parts) > 0 else None
                mid_category = label_parts[1] if len(label_parts) > 1 else None
                subcategory = label_parts[2] if len(label_parts) > 2 else None

                categories_data.append({
                    "category": category,
                    "mid_category": mid_category,
                    "subcategory": subcategory,
                    "category_id": link.get_attribute("data-category-id"),
                    "num_products": link.get_attribute("data-num-all-products")
                })
            except Exception as e:
                print("⚠️ Failed to extract a category:", e)
                continue

    except Exception as e:
        print("❌ Could not locate root category list:", e)

    return categories_data


def extract_products_from_category(driver, wait):
    products = []
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#grid .product")))
        product_elements = driver.find_elements(By.CSS_SELECTOR, "#grid .product")

        for product in product_elements:
            try:
                name = product.find_element(By.CSS_SELECTOR, ".lib-product-name").text
                url = product.find_element(By.CSS_SELECTOR, ".lib-product-url").get_attribute("href")
                item_id = product.get_attribute("data-item-id")
                data_analytics = product.get_attribute("data-analytics-object")

                # Price
                price_elem = product.find_element(By.CSS_SELECTOR, ".lib-product-price")
                price = price_elem.text.strip().replace(",", ".") if price_elem else None

                products.append({
                    "item_id": item_id,
                    "name": name,
                    "url": url,
                    "price": price,
                    "analytics": data_analytics
                })
            except Exception as e:
                print("⚠️ Failed to extract a product:", e)
                continue

    except Exception as e:
        print("❌ Failed to load product grid:", e)

    return products




if __name__ == "__main__":
    # Setup
    service = Service(ChromeDriverManager().install())

    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2  # Block notifications
    })

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 5)

    # Open Mercator website
    print("🌐 Opening Mercator website...")
    driver.get("https://mercatoronline.si/")
    time.sleep(2)

    # Step 1: Close cookie popup
    close_cookie_popup(driver, wait)

    time.sleep(1)

    close_welcome_popup(driver, wait)

    # Placeholder for upcoming scraping logic
    print("🎯 Ready for next step...")

    ## Step 2: Navigate to a specific page (e.g., "Brskaj")
    driver.get("https://mercatoronline.si/brskaj")

    time.sleep(1)

    # Step 4: Extract category structure
    categories = extract_categories(driver)
    print(f"✅ Extracted {len(categories)} category entries.")



    # Create folder to store category files
    os.makedirs("mercator_data", exist_ok=True)

    # Group products by top category
    grouped_by_top_category = defaultdict(list)

    # Track which top categories have already been saved
    saved_top_categories = set()

    for cat in categories:

       
        cat_id = cat['category_id']
        top_category = cat['category']
        print(f"🔍 Scraping: {top_category} > {cat['mid_category']} > {cat['subcategory']}")

        if cat["mid_category"] is None or cat["subcategory"] is None:
            print(f"⏭️ Skipping incomplete category: {cat}")
            continue

        # Open brskaj page again to get a fresh sidebar for clicking
        driver.get("https://mercatoronline.si/brskaj")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.lib-categories")))

        # Click the category based on its ID
        try:
            category_link = driver.find_element(By.CSS_SELECTOR, f"a.lib-filters-category-change[data-category-id='{cat_id}']")
            driver.execute_script("arguments[0].scrollIntoView(true);", category_link)
            driver.execute_script("arguments[0].click();", category_link)

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#grid .product")))
            time.sleep(1)
            close_email_popup(driver, wait)

        except Exception as e:
            print(f"❌ Failed to click category {cat_id}: {e}")
            continue


        # Limit to first 5 products
        products = extract_products_from_category(driver, wait)[:5]

        for p in products:
            p["category"] = top_category
            p["mid_category"] = cat["mid_category"]
            p["subcategory"] = cat["subcategory"]

        grouped_by_top_category[top_category].extend(products)

        # Check if this is the last occurrence of this top_category
        next_cats = categories[categories.index(cat)+1:]
        is_last_of_top_category = all(c['category'] != top_category for c in next_cats)

        if is_last_of_top_category and top_category not in saved_top_categories:
            # Sanitize filename
            filename = re.sub(r"[^\w\-]+", "_", top_category.strip())
            filepath = os.path.join("mercator_data", f"mercator_{filename}.json")

            # Save data
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(grouped_by_top_category[top_category], f, ensure_ascii=False, indent=2)

            print(f"💾 Saved {len(grouped_by_top_category[top_category])} items to {filepath}")
            saved_top_categories.add(top_category)



    # Clean exit for now
    driver.quit()
