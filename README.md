
# 🛒 Slovenian Grocery Store Scrapers

This repository contains two robust Selenium-based web scrapers for Slovenian online grocery stores: **Spar** and **Mercator**. The scrapers are designed to navigate each store’s structure, handle dynamic popups, and extract structured product data for analysis or comparison.

---

## 📦 Features

- ✅ Automatically handles cookie and onboarding popups
- ✅ Navigates category and subcategory structures
- ✅ Extracts product details including:
  - Product name
  - Category
  - Price
  - Product URL
  - Discount and product ID
- ✅ Saves data in structured **CSV** and **JSON** formats
- ✅ Separate files per top-level category

---

## 🛍 Supported Stores

| Store     | Method Used | Notes                                                                 |
|-----------|-------------|-----------------------------------------------------------------------|
| **Spar**  | Full URL-based navigation and direct product scraping | Extracts detailed info from individual product pages |
| **Mercator** | Click simulation to trigger JavaScript loaders | Extracts lightweight info from subcategory listing pages |

---

## 🧰 Requirements

- Python 3.8+
- Google Chrome
- ChromeDriver (automatically managed)

Install dependencies:
```bash
pip install -r requirements.txt
```

If `requirements.txt` isn't provided, install manually:
```bash
pip install selenium webdriver-manager
```

---

## 🚀 Usage

### 🔹 SPAR Scraper
```bash
python spar_scraper.py
```
Saves a CSV with product data from selected categories.

### 🔹 Mercator Scraper
```bash
python mercator_scraper.py
```
Saves individual JSON files (per top-level category) and can convert to CSV using `json_to_csv.py`.

---

## 📁 Output Files

- `spar_sample_products.csv` — CSV file with scraped SPAR product data
- `mercator_data/` — Folder with one JSON file per Mercator top-level category
- `mercator_<category>.csv` — Optional converted CSV files

---


