import pandas as pd
import requests
from PIL import Image, ImageOps, ImageFilter, ImageEnhance 
import io
import os

# ==========================================
# ⚙️ SETTINGS
# ==========================================
GITHUB_USER = "mademoneyai-hub"
REPO_NAME = "sweet-india-products"
BRANCH = "main"

INPUT_FILE = "final_meesho_data.xlsx"
OUTPUT_FILE = "Final_Amazon_Ready_Upload.xlsx"

# Pricing Settings
MY_PROFIT = 200
BUFFER_MARGIN = 30
DEFAULT_WEIGHT = 450

# --- AMAZON EXACT COLUMNS (Jo Sheet me hote hain) ---
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

def calculate_selling_price(making_cost, product_title):
    try: making_cost = float(making_cost)
    except: return 999
    
    weight = DEFAULT_WEIGHT
    title_lower = str(product_title).lower()
    
    # Weight Check Logic
    if any(x in title_lower for x in ['lehenga', 'jacket', 'coat', 'heavy']): weight = 900
    elif any(x in title_lower for x in ['gown', 'anarkali']): weight = 600
    
    # Courier Rate Logic
    if weight <= 500: shipping = 74
    elif weight <= 1000: shipping = 111
    else: shipping = 153

    return int(making_cost + shipping + BUFFER_MARGIN + MY_PROFIT)

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
    print("🚀 Script Start! Amazon Format generate ho raha hai...")
    
    try:
        df = pd.read_excel(INPUT_FILE)
    except:
        print(f"❌ '{INPUT_FILE}' nahi mili!")
        return

    amazon_data = []

    for index, row in df.iterrows():
        sku = f"SWEET_INDIA_{index+1001}"
        title = str(row.get('Title', 'Product'))
        desc = str(row.get('Description', 'Premium Quality Product from Sweet India'))
        price = calculate_selling_price(row.get('Price', 0), title)

        print(f"   ⚙️ Processing: {sku} | SP: {price}")

        # --- FILL AMAZON ROW ---
        # Hum wahi columns bharenge jo zaroori hain, baki blank rahenge
        amz_row = {col: '' for col in AMAZON_COLUMNS} # Pehle sab khali rakho

        amz_row['feed_product_type'] = 'kurta'  # Ya 'shirt', 'dress' etc.
        amz_row['item_sku'] = sku
        amz_row['brand_name'] = 'Sweet India'
        amz_row['item_name'] = f"Sweet India Premium {title}"
        
        # GTIN Exemption hai to ye dono khali chhodne hain
        amz_row['external_product_id'] = '' 
        amz_row['external_product_id_type'] = '' 

        amz_row['standard_price'] = price
        amz_row['quantity'] = 50
        amz_row['department_name'] = 'Women' # Ya 'Men'
        amz_row['color_name'] = 'Multicolor' # Default (Ya agar data me hai to wo lo)
        amz_row['size_name'] = 'Free Size'   # Default
        amz_row['material_type'] = 'Cotton Blend'
        amz_row['product_description'] = desc
        
        # Bullet Points
        amz_row['bullet_point1'] = "Premium Quality Fabric, Comfortable to wear."
        amz_row['bullet_point2'] = "Perfect for Casual, Party & Festive wear."
        amz_row['bullet_point3'] = "Care Instructions: Machine Wash / Hand Wash."
        
        # Mandatory Compliance
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
                    
                    filename = f"{sku}_img{i}.jpg"
                    final_img.save(filename, quality=95)
                    
                    # Github Link
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
    print("Is file me Amazon ke standard columns (feed_product_type, brand, price etc.) hain.")

if __name__ == "__main__":
    process_images()
