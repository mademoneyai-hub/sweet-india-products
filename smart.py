import pandas as pd
import requests
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import io
import os
import time
import re 

# ==========================================
# ⚙️ SETTINGS (Multi-Category Setup)
# ==========================================
GITHUB_USER = "mademoneyai-hub"
REPO_NAME = "sweet-india-products"
BRANCH = "main"

INPUT_FILE = "final_meesho_data.xlsx"
OUTPUT_FILE = "Amazon_Generic_Master_Upload.xlsx"

# ✅ BRAND SETTING: Generic
BRAND_NAME = "Generic" 
MANUFACTURER = "Sweet India Enterprises" # Yahan apni firm ka naam likhein

# 💰 PROFIT SETTING
FIXED_PROFIT = 200  

# ==========================================

# --- 1. INTELLIGENT CATEGORY DETECTOR ---
def detect_category_and_sizes(title, desc):
    text = (str(title) + " " + str(desc)).lower()
    
    # --- A. CLOTHING (Kurti, Top, Dress) ---
    if any(x in text for x in ['kurti', 'kurta', 'dress', 'top', 'tunic', 'shirt', 'gown']):
        return {
            'type': 'shirt',  # Amazon Feed Type
            'is_variation': True,
            'theme': 'size_name',
            'sizes': ['S', 'M', 'L', 'XL', '2XL'],
            'keywords': 'latest fashion for women, party wear, trendy design, comfort fit',
            'material_default': 'Cotton Blend'
        }
    
    # --- B. SHOES (Sandal, Shoe, Boot) ---
    elif any(x in text for x in ['shoe', 'sandal', 'boot', 'slipper', 'flat', 'heel']):
        return {
            'type': 'shoes',
            'is_variation': True,
            'theme': 'size_name',
            'sizes': ['6 UK', '7 UK', '8 UK', '9 UK'],
            'keywords': 'comfortable walking shoes, stylish footwear, durable sole, casual wear',
            'material_default': 'Synthetic Leather'
        }
    
    # --- C. SAREE (Clothing but NO Size Variation) ---
    elif 'saree' in text:
        return {
            'type': 'saree',
            'is_variation': False, # Saree ka size nahi hota
            'theme': '',
            'sizes': [],
            'keywords': 'designer saree, traditional wear, wedding saree, silk saree',
            'material_default': 'Art Silk'
        }

    # --- D. BAGS / WATCHES / OTHERS (Single Product) ---
    else:
        return {
            'type': 'luggage', # Default for bags
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
    elif "silk" in text: material = "Silk"
    elif "leather" in text: material = "Leather"
    elif "canvas" in text: material = "Canvas"
    elif "polyester" in text: material = "Polyester"
    
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

# --- 3. PRICE CALCULATOR ---
def calculate_price(raw_price):
    try:
        clean_str = str(raw_price).lower().replace('rs.', '').replace('rs', '').replace('₹', '').replace(',', '').replace(' ', '')
        cost = float(clean_str)
    except: return 0
    
    shipping = 74 
    return int(cost + shipping + FIXED_PROFIT)

# --- 4. IMAGE ENHANCER ---
def make_dslr_quality(img):
    if img.mode != "RGB": img = img.convert("RGB")
    img = ImageOps.exif_transpose(img)
    
    w, h = img.size
    target = 1000 # Amazon min requirement
    if w < target or h < target:
        ratio = target / min(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
    
    # Blur Bottom 10%
    blur_h = int(h * 0.10)
    box = (0, h - blur_h, w, h)
    blur = img.crop(box).filter(ImageFilter.GaussianBlur(radius=20))
    img.paste(blur, box)
    
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    return img

# ==========================================
# 🚀 MAIN PROCESSING ENGINE
# ==========================================
def process_multi_category():
    print("🚀 MULTI-CATEGORY SCRIPT STARTED...")
    print("   (Detecting: Clothes, Shoes, Sarees, Bags, etc.)")
    
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    try: df = pd.read_excel(INPUT_FILE)
    except: print("❌ Excel File nahi mili!"); return

    amazon_rows = []
    batch_time = int(time.time())

    for index, row in df.iterrows():
        # --- 1. DATA GATHERING ---
        raw_title = str(row.get('Title', 'Generic Product'))
        raw_desc = str(row.get('Description', ''))
        my_price = calculate_price(row.get('Price', 0))
        
        # --- 2. 🧠 AI DECISION (Category kya hai?) ---
        cat_info = detect_category_and_sizes(raw_title, raw_desc)
        
        # --- 3. DETAILS EXTRACTION ---
        final_mat, final_color = extract_material_and_color(raw_desc, cat_info['material_default'])
        
        # SEO Text Generation
        seo_title = f"{BRAND_NAME} {raw_title} | {final_mat} | {final_color} | {cat_info['keywords'].split(',')[0]}"
        final_bullets = [
            f"MATERIAL: High quality {final_mat}, designed for durability and comfort.",
            f"STYLE: Latest trendy design suitable for all occasions.",
            f"QUALITY: Premium finish from {BRAND_NAME}.",
            "CARE: Easy to clean and maintain.",
            "MADE IN INDIA: Proudly manufactured in India."
        ]

        # Base SKU
        base_sku = f"GEN-{cat_info['type'][:3].upper()}-{batch_time}-{index+1}"

        # --- 4. IMAGES ---
        image_links = []
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
        # 🟢 MODE 1: VARIATION PRODUCT (Clothes/Shoes)
        # ==========================================
        if cat_info['is_variation']:
            # A. PARENT ROW
            parent_row = {
                'item_sku': base_sku + "-PARENT",
                'item_name': seo_title,
                'brand_name': BRAND_NAME,
                'feed_product_type': cat_info['type'],
                'update_delete': 'Update',
                'parent_child': 'Parent',
                'variation_theme': cat_info['theme'],
                'department_name': 'Women' if 'women' in raw_title.lower() else 'Unisex',
                'product_description': raw_desc if len(raw_desc) > 10 else f"Shop this {raw_title}.",
                'bullet_point1': final_bullets[0], 'bullet_point2': final_bullets[1],
                'bullet_point3': final_bullets[2], 'bullet_point4': final_bullets[3],
                'bullet_point5': final_bullets[4],
                'generic_keywords': cat_info['keywords'],
                'main_image_url': main_img,
                'material_type': final_mat,
                'color_name': final_color,
                'manufacturer': MANUFACTURER,
            }
            amazon_rows.append(parent_row)

            # B. CHILD ROWS (Sizes)
            for size in cat_info['sizes']:
                child_row = parent_row.copy()
                child_row['item_sku'] = f"{base_sku}-{size.replace(' ', '')}"
                child_row['parent_child'] = 'Child'
                child_row['relationship_type'] = 'Variation'
                child_row['size_name'] = size
                child_row['standard_price'] = my_price
                child_row['quantity'] = 25
                child_row['other_image_url1'] = other_imgs[0] if len(other_imgs) > 0 else ''
                child_row['other_image_url2'] = other_imgs[1] if len(other_imgs) > 1 else ''
                amazon_rows.append(child_row)
            
            print(f"   👕 Variation Created: {raw_title[:15]}... ({len(cat_info['sizes'])} Sizes)")

        # ==========================================
        # 🔵 MODE 2: SINGLE PRODUCT (Bag/Watch/Saree)
        # ==========================================
        else:
            single_row = {
                'item_sku': base_sku,
                'item_name': seo_title,
                'brand_name': BRAND_NAME,
                'feed_product_type': cat_info['type'],
                'update_delete': 'Update',
                'standard_price': my_price,
                'quantity': 50,
                'product_description': raw_desc,
                'bullet_point1': final_bullets[0], 'bullet_point2': final_bullets[1],
                'bullet_point3': final_bullets[2],
                'generic_keywords': cat_info['keywords'],
                'main_image_url': main_img,
                'other_image_url1': other_imgs[0] if len(other_imgs) > 0 else '',
                'other_image_url2': other_imgs[1] if len(other_imgs) > 1 else '',
                'material_type': final_mat,
                'color_name': final_color,
                'manufacturer': MANUFACTURER,
                'department_name': 'Women'
            }
            amazon_rows.append(single_row)
            print(f"   👜 Single Item Created: {raw_title[:15]}...")

    # --- SAVE ---
    df_final = pd.DataFrame(amazon_rows)
    # Arrange columns properly
    cols = ['feed_product_type', 'item_sku', 'brand_name', 'item_name', 'parent_child', 'variation_theme', 'size_name', 'color_name', 'standard_price', 'quantity', 'main_image_url']
    other_cols = [c for c in df_final.columns if c not in cols]
    df_final = df_final[cols + other_cols]
    
    df_final.to_excel(OUTPUT_FILE, index=False)
    print(f"\n✅ MASTER SHEET READY: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_multi_category()
