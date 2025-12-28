import pandas as pd
import requests
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import io
import os
import time
import re

# ==========================================
# ⚙️ SETTINGS
# ==========================================
GITHUB_USER = "mademoneyai-hub"
REPO_NAME = "sweet-india-products"
BRANCH = "main"

INPUT_FILE = "final_meesho_data.xlsx"
OUTPUT_FILE = "Amazon_Complete_Master_Upload.xlsx"

# ✅ BRAND & INFO
BRAND_NAME = "Generic"  # Generic rakha hai taki error na aaye
MANUFACTURER = "Sweet India Enterprises"

# 💰 PRICING SETTINGS (Merged from your code)
FIXED_PROFIT = 200   # Apka Munafa
BUFFER_MARGIN = 30   # Extra Safety Margin
DEFAULT_WEIGHT = 450 # Grams

# ==========================================

# --- 1. INTELLIGENT CATEGORY DETECTOR ---
def detect_category_and_sizes(title, desc):
    text = (str(title) + " " + str(desc)).lower()
    
    # A. CLOTHING (Kurti, Top, Dress) -> Needs S-2XL
    if any(x in text for x in ['kurti', 'kurta', 'dress', 'top', 'tunic', 'shirt', 'gown', 'lehenga']):
        return {
            'type': 'shirt',  
            'is_variation': True,
            'theme': 'size_name',
            'sizes': ['S', 'M', 'L', 'XL', '2XL'],
            'keywords': 'latest fashion for women, party wear, trendy design, comfort fit, ethnic wear',
            'material_default': 'Cotton Blend'
        }
    
    # B. SHOES (Sandal, Shoe, Boot) -> Needs UK Sizes
    elif any(x in text for x in ['shoe', 'sandal', 'boot', 'slipper', 'flat', 'heel', 'jutti']):
        return {
            'type': 'shoes',
            'is_variation': True,
            'theme': 'size_name',
            'sizes': ['6 UK', '7 UK', '8 UK', '9 UK'],
            'keywords': 'comfortable walking shoes, stylish footwear, durable sole, casual wear',
            'material_default': 'Synthetic Leather'
        }
    
    # C. SAREE (No Size)
    elif 'saree' in text:
        return {
            'type': 'saree',
            'is_variation': False,
            'theme': '',
            'sizes': [],
            'keywords': 'designer saree, traditional wear, wedding saree, silk saree',
            'material_default': 'Art Silk'
        }

    # D. OTHERS (Single Item)
    else:
        return {
            'type': 'luggage', 
            'is_variation': False,
            'theme': '',
            'sizes': [],
            'keywords': 'premium quality, durable material, latest style, gift item',
            'material_default': 'High Quality Material'
        }

# --- 2. SMART DETAILS EXTRACTOR ---
def extract_material_and_color(text, default_mat):
    text = str(text).lower()
    
    # Material Scan
    material = default_mat
    if "rayon" in text: material = "Rayon"
    elif "cotton" in text: material = "Cotton"
    elif "silk" in text: material = "Art Silk"
    elif "georgette" in text: material = "Georgette"
    elif "crepe" in text: material = "Crepe"
    elif "leather" in text: material = "Leather"
    
    # Color Scan
    color = "Multicolor"
    if "red" in text: color = "Red"
    elif "blue" in text: color = "Blue"
    elif "black" in text: color = "Black"
    elif "white" in text: color = "White"
    elif "pink" in text: color = "Pink"
    elif "yellow" in text: color = "Yellow"
    elif "green" in text: color = "Green"

    return material, color

# --- 3. PRICE CALCULATOR (Updated with Buffer & Weight Logic) ---
def calculate_price(raw_price, title):
    try:
        # Clean Price
        clean_str = str(raw_price).lower().replace('rs.', '').replace('rs', '').replace('₹', '').replace(',', '').replace(' ', '')
        cost = float(clean_str)
    except: return 0 
    
    # Weight Logic (From your code)
    weight = DEFAULT_WEIGHT
    title_lower = str(title).lower()
    if any(x in title_lower for x in ['lehenga', 'jacket', 'coat', 'heavy']): weight = 900
    elif any(x in title_lower for x in ['gown', 'anarkali', 'set of 2']): weight = 600
    elif any(x in title_lower for x in ['shoe', 'boot']): weight = 800

    # Shipping Logic
    shipping = 74
    if weight > 500 and weight <= 1000: shipping = 111
    elif weight > 1000: shipping = 153
    
    # Formula: Cost + Shipping + Buffer(30) + Profit(200)
    return int(cost + shipping + BUFFER_MARGIN + FIXED_PROFIT)

# --- 4. IMAGE ENHANCER ---
def make_dslr_quality(img):
    if img.mode != "RGB": img = img.convert("RGB")
    img = ImageOps.exif_transpose(img)
    
    # HD Resize
    w, h = img.size
    target = 1000 
    if w < target or h < target:
        ratio = target / min(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
    
    # Blur Bottom
    blur_h = 60
    box = (0, h - blur_h, w, h)
    blur = img.crop(box).filter(ImageFilter.GaussianBlur(radius=15))
    img.paste(blur, box)
    
    # Quality Boost
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    return img

# ==========================================
# 🚀 MAIN PROCESSING ENGINE
# ==========================================
def process_amazon_complete():
    print("🚀 ULTIMATE SCRIPT STARTED...")
    
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    try: df = pd.read_excel(INPUT_FILE)
    except: print("❌ Excel File nahi mili!"); return

    amazon_rows = []
    batch_time = int(time.time())

    # --- DEFINING EXACT AMAZON COLUMNS ---
    AMZ_COLS = [
        'feed_product_type', 'item_sku', 'brand_name', 'item_name', 
        'parent_child', 'parent_sku', 'relationship_type', 'variation_theme', 
        'standard_price', 'quantity', 'main_image_url', 
        'other_image_url1', 'other_image_url2', 'other_image_url3', 
        'department_name', 'color_name', 'size_name', 'material_type', 
        'product_description', 'bullet_point1', 'bullet_point2', 'bullet_point3', 
        'bullet_point4', 'bullet_point5', 'generic_keywords', 
        'country_of_origin', 'manufacturer', 'update_delete',
        'external_product_id', 'external_product_id_type',
        'batteries_required', 'are_batteries_included', 'supplier_declared_dg_hz_regulation'
    ]

    for index, row in df.iterrows():
        # 1. Basic Data
        raw_title = str(row.get('Title', 'Generic Product'))
        raw_desc = str(row.get('Description', ''))
        
        # Price Calculation with your Formula
        my_price = calculate_price(row.get('Price', 0), raw_title)
        
        # 2. Detect Logic
        cat_info = detect_category_and_sizes(raw_title, raw_desc)
        final_mat, final_color = extract_material_and_color(raw_desc, cat_info['material_default'])
        
        # 3. SEO Content
        seo_title = f"{BRAND_NAME} {raw_title} | {final_mat} | {final_color} | {cat_info['keywords'].split(',')[0]}"
        bullets = [
            f"MATERIAL: High quality {final_mat}, designed for durability and comfort.",
            f"STYLE: Latest trendy design suitable for all occasions.",
            f"QUALITY: Premium finish from {MANUFACTURER}.",
            "CARE: Easy to clean and maintain.",
            "MADE IN INDIA: Proudly manufactured in India."
        ]

        # 4. Images Processing
        image_links = []
        base_sku = f"SWT-GEN-{batch_time}-{index+1}" # Unique SKU
        
        for i in range(1, 5):
            col_name = f"Image {i}"
            if col_name in row and pd.notna(row[col_name]):
                try:
                    res = requests.get(row[col_name], timeout=10)
                    img = Image.open(io.BytesIO(res.content))
                    final_img = make_dslr_quality(img)
                    filename = f"{base_sku}_img{i}.jpg"
                    final_img.save(filename, quality=95)
                    gh_link = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{filename}"
                    image_links.append(gh_link)
                except: pass
        
        main_img = image_links[0] if len(image_links) > 0 else ""
        other_imgs = image_links[1:] + [""] * (3 - len(image_links[1:]))

        # ==========================================
        # 🟢 LOGIC: VARIATION (Clothes/Shoes)
        # ==========================================
        if cat_info['is_variation']:
            # A. PARENT ROW (Header)
            parent_sku = base_sku + "-PARENT"
            parent_row = {col: '' for col in AMZ_COLS} # Initialize Blank
            
            parent_row.update({
                'feed_product_type': cat_info['type'],
                'item_sku': parent_sku,
                'brand_name': BRAND_NAME,
                'item_name': seo_title,
                'parent_child': 'Parent',
                'variation_theme': cat_info['theme'],
                'department_name': 'Women',
                'product_description': raw_desc,
                'bullet_point1': bullets[0], 'bullet_point2': bullets[1], 'bullet_point3': bullets[2],
                'bullet_point4': bullets[3], 'bullet_point5': bullets[4],
                'generic_keywords': cat_info['keywords'],
                'main_image_url': main_img,
                'material_type': final_mat,
                'color_name': final_color,
                'manufacturer': MANUFACTURER,
                'country_of_origin': 'India',
                'update_delete': 'Update',
                'batteries_required': 'False',
                'are_batteries_included': 'False',
                'supplier_declared_dg_hz_regulation': 'Not Applicable'
            })
            amazon_rows.append(parent_row)

            # B. CHILD ROWS (Actual Sizes)
            for size in cat_info['sizes']:
                child_row = parent_row.copy() # Copy Parent Data
                child_row.update({
                    'item_sku': f"{base_sku}-{size.replace(' ', '')}",
                    'parent_child': 'Child',
                    'parent_sku': parent_sku,  # Linked to Parent
                    'relationship_type': 'Variation',
                    'size_name': size,
                    'standard_price': my_price, # Price added here
                    'quantity': 30,             # Quantity added here
                    'other_image_url1': other_imgs[0] if len(other_imgs) > 0 else '',
                    'other_image_url2': other_imgs[1] if len(other_imgs) > 1 else ''
                })
                amazon_rows.append(child_row)
            
            print(f"   👕 Processed: {raw_title[:15]}... | SP: {my_price}")

        # ==========================================
        # 🔵 LOGIC: SINGLE PRODUCT (Bags/Watches)
        # ==========================================
        else:
            single_row = {col: '' for col in AMZ_COLS}
            single_row.update({
                'feed_product_type': cat_info['type'],
                'item_sku': base_sku,
                'brand_name': BRAND_NAME,
                'item_name': seo_title,
                'standard_price': my_price,
                'quantity': 50,
                'product_description': raw_desc,
                'bullet_point1': bullets[0], 'bullet_point2': bullets[1], 'bullet_point3': bullets[2],
                'generic_keywords': cat_info['keywords'],
                'main_image_url': main_img,
                'other_image_url1': other_imgs[0] if len(other_imgs) > 0 else '',
                'other_image_url2': other_imgs[1] if len(other_imgs) > 1 else '',
                'material_type': final_mat,
                'color_name': final_color,
                'manufacturer': MANUFACTURER,
                'country_of_origin': 'India',
                'department_name': 'Women',
                'update_delete': 'Update',
                'batteries_required': 'False',
                'are_batteries_included': 'False',
                'supplier_declared_dg_hz_regulation': 'Not Applicable'
            })
            amazon_rows.append(single_row)
            print(f"   👜 Processed: {raw_title[:15]}... | SP: {my_price}")

    # --- SAVE FINAL EXCEL ---
    df_final = pd.DataFrame(amazon_rows, columns=AMZ_COLS)
    df_final.to_excel(OUTPUT_FILE, index=False)
    
    print("\n✅ MISSION COMPLETE! Amazon Sheet Ready.")
    print(f"📂 Output File: {OUTPUT_FILE}")
    print(f"👉 Price Logic: Cost + Shipping + Buffer({BUFFER_MARGIN}) + Profit({FIXED_PROFIT})")

if __name__ == "__main__":
    process_amazon_complete()
