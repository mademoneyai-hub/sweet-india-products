import pandas as pd
import requests
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import io
import os
import time  # Added for unique SKU generation

# ==========================================
# ⚙️ SETTINGS
# ==========================================
GITHUB_USER = "mademoneyai-hub"
REPO_NAME = "sweet-india-products"
BRANCH = "main"

INPUT_FILE = "final_meesho_data.xlsx"
OUTPUT_FILE = "Final_Amazon_Ready_Upload.xlsx"

# Pricing Settings
# Ab Shipping alag se nahi judega. 
# Formula: Product Price + FIXED_ADDITION (190)
FIXED_ADDITION = 190 

# --- AMAZON EXACT COLUMNS ---
AMAZON_COLUMNS = [
    'feed_product_type', 'item_sku', 'brand_name', 'external_product_id', 
    'external_product_id_type', 'item_name', 'standard_price', 'quantity', 
    'main_image_url', 'other_image_url1', 'other_image_url2', 'other_image_url3', 
    'department_name', 'color_name', 'size_name', 'material_type', 
    'fit_type', 'neck_style', 'pattern_type', 'product_description', 
    'bullet_point1', 'bullet_point2', 'bullet_point3', 'generic_keywords',
    'country_of_origin', 'batteries_required', 'are_batteries_included', 
    'supplier_declared_dg_hz_regulation'
]

# ==========================================

def calculate_selling_price(making_cost):
    """
    New Formula: Base Price + 190 (Profit & Shipping included)
    """
    try: 
        # Clean the price string (remove '₹', comma, space)
        clean_price = str(making_cost).lower().replace('rs.', '').replace('rs', '').replace('₹', '').replace(',', '').replace(' ', '')
        cost = float(clean_price)
    except: 
        return 999
    
    # Cost + 190
    return int(cost + FIXED_ADDITION)

def make_dslr_quality(img):
    if img.mode != "RGB": img = img.convert("RGB")
    img = ImageOps.exif_transpose(img)
    
    # Resize to HD (1200px)
    w, h = img.size
    if w < 1200 or h < 1200:
        ratio = 1200 / min(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
    
    # Blur Bottom
    w, h = img.size
    blur_h = 60
    box = (0, h - blur_h, w, h)
    blur = img.crop(box).filter(ImageFilter.GaussianBlur(radius=15))
    img.paste(blur, box)
    
    # Enhance
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Color(img).enhance(1.1)
    return img

def process_images():
    print("🚀 Script Start! Generating Unique SKUs & Price + 190...")
    
    try:
        df = pd.read_excel(INPUT_FILE)
    except:
        print(f"❌ '{INPUT_FILE}' nahi mili!")
        return

    amazon_data = []
    
    # Unique Batch ID based on current time
    batch_id = int(time.time())

    for index, row in df.iterrows():
        # --- 1. UNIQUE SKU LOGIC ---
        # Format: SWEET-BatchID-RowIndex (Example: SWEET-173546-1001)
        sku = f"SWEET-{batch_id}-{index+1001}"
        
        title = str(row.get('Title', 'Product'))
        desc = str(row.get('Description', 'Premium Quality Product from Sweet India'))
        
        # --- 2. PRICE LOGIC (Cost + 190) ---
        price = calculate_selling_price(row.get('Price', 0))

        print(f"   ⚙️ {sku} | SP: {price}")

        # --- FILL AMAZON ROW ---
        amz_row = {col: '' for col in AMAZON_COLUMNS}

        amz_row['feed_product_type'] = 'kurta' 
        amz_row['item_sku'] = sku
        amz_row['brand_name'] = 'Sweet India'
        amz_row['item_name'] = f"Sweet India Premium {title}"
        
        amz_row['external_product_id'] = '' 
        amz_row['external_product_id_type'] = '' 

        amz_row['standard_price'] = price
        amz_row['quantity'] = 50
        amz_row['department_name'] = 'Women'
        amz_row['color_name'] = 'Multicolor'
        amz_row['size_name'] = 'Free Size'
        amz_row['material_type'] = 'Cotton Blend'
        amz_row['product_description'] = desc
        
        amz_row['bullet_point1'] = "Premium Quality Fabric, Comfortable to wear."
        amz_row['bullet_point2'] = "Perfect for Casual, Party & Festive wear."
        amz_row['bullet_point3'] = "Care Instructions: Machine Wash / Hand Wash."
        
        amz_row['country_of_origin'] = 'India'
        amz_row['batteries_required'] = 'False'
        amz_row['are_batteries_included'] = 'False'
        amz_row['supplier_declared_dg_hz_regulation'] = 'Not Applicable'

        # --- IMAGES ---
        for i in range(1, 5):
            col_name = f"Image {i}"
            if col_name in row and pd.notna(row[col_name]):
                url = row[col_name]
                try:
                    res = requests.get(url, timeout=10)
                    img = Image.open(io.BytesIO(res.content))
                    final_img = make_dslr_quality(img)
                    
                    # Filename me bhi SKU use hoga uniqueness ke liye
                    filename = f"{sku}_img{i}.jpg"
                    final_img.save(filename, quality=95)
                    
                    gh_link = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{filename}"
                    
                    if i == 1: amz_row['main_image_url'] = gh_link
                    elif i == 2: amz_row['other_image_url1'] = gh_link
                    elif i == 3: amz_row['other_image_url2'] = gh_link
                    elif i == 4: amz_row['other_image_url3'] = gh_link
                    
                except: pass

        amazon_data.append(amz_row)

    # Save Excel with exact columns
    final_df = pd.DataFrame(amazon_data, columns=AMAZON_COLUMNS)
    final_df.to_excel(OUTPUT_FILE, index=False)
    
    print("\n✅ MISSION COMPLETE!")
    print(f"📂 File Saved: {OUTPUT_FILE}")
    print(f"👉 New SKUs generated like: SWEET-{batch_id}-XXXX")

if __name__ == "__main__":
    process_images()
