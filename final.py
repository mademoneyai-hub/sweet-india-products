import pandas as pd
import requests
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import io
import os
import time

# ==========================================
# ⚙️ SETTINGS (Yahan badlav karein)
# ==========================================
GITHUB_USER = "mademoneyai-hub"
REPO_NAME = "sweet-india-products"
BRANCH = "main"

INPUT_FILE = "final_meesho_data.xlsx"   
OUTPUT_FILE = "Final_Amazon_Upload.xlsx"

# --- Image Settings ---
BLUR_HEIGHT = 60       
HD_SIZE = 1200         

# --- 💰 Price & Profit Settings ---
# Ab har product par ₹200 ka seedha profit judega
FIXED_MARGIN = 200     
DEFAULT_WEIGHT = 450   # Grams
# ==========================================

def calculate_selling_price(making_cost, product_title):
    """
    Formula: Cost (Cleaned) + Shipping Charge + 200 (Profit)
    """
    # --- 1. SMART PRICE CLEANING (₹ aur Rs dono hatayega) ---
    try:
        # Pehle sab kuch text mein badlo aur chota (lowercase) karo
        clean_price = str(making_cost).lower()
        
        # Ab safai abhiyan:
        # 'rs.' ya 'rs' ya '₹' ya ',' sab hata do
        clean_price = clean_price.replace('rs.', '').replace('rs', '').replace('₹', '').replace(',', '').replace(' ', '')
        
        # Ab jo bacha wo shuddh number hai
        cost = float(clean_price)
    except:
        # Agar fir bhi na padh paye (matlab price hai hi nahi), to 0 maano
        print(f"⚠️ Price Error for: {product_title[:10]}... (Setting 0)")
        cost = 0 
    
    # --- 2. Weight Andaza ---
    weight = DEFAULT_WEIGHT
    title_lower = str(product_title).lower()
    
    # Agar bhari item ho to weight badha do
    if any(x in title_lower for x in ['coat', 'jacket', 'heavy', 'lehenga', 'gown', 'set of 2']):
        weight = 900
    elif any(x in title_lower for x in ['shoe', 'boot', 'sandal']):
        weight = 800
    
    # --- 3. Shipping Calculation (National) ---
    shipping_charge = 0
    if weight <= 500:
        shipping_charge = 74
    elif weight <= 1000:
        shipping_charge = 111
    else:
        shipping_charge = 153

    # --- 4. Final Price ---
    # Cost + Shipping + 200 (Profit)
    total_selling_price = cost + shipping_charge + FIXED_MARGIN
    
    return int(total_selling_price)

def make_dslr_quality(img):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = ImageOps.exif_transpose(img)

    w, h = img.size
    if w < HD_SIZE or h < HD_SIZE:
        ratio = HD_SIZE / min(w, h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Blur Bottom
    w, h = img.size
    blur_area_h = int(BLUR_HEIGHT * (h / 500)) if h > 500 else BLUR_HEIGHT
    bottom_box = (0, h - blur_area_h, w, h)
    bottom_strip = img.crop(bottom_box)
    blurred_strip = bottom_strip.filter(ImageFilter.GaussianBlur(radius=15))
    img.paste(blurred_strip, bottom_box)

    # Enhance
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.4)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)
    
    return img

def process_images():
    print("🚀 Script Started (Updated Profit: ₹200)...")
    
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    try:
        df = pd.read_excel(INPUT_FILE)
    except:
        print(f"❌ Error: '{INPUT_FILE}' nahi mili!")
        return

    amazon_data = []
    print(f"📦 Total {len(df)} products mile.")

    batch_time = int(time.time())

    for index, row in df.iterrows():
        sku = f"SWT-KUR-{batch_time}-{index+1}"
        
        title = str(row.get('Title', 'Designer Kurti'))
        cost_price = row.get('Price', 0)
        description = str(row.get('Description', ''))
        
        # Calculate Price
        final_price = calculate_selling_price(cost_price, title)

        print(f"   ⚙️ Processing: {title[:15]}... | Cost: {cost_price} -> SP: ₹{final_price}")

        amz_row = {
            'item_sku': sku,
            'brand_name': 'Sweet India',
            'item_name': f"Sweet India {title}",
            'external_product_id': '', 
            'external_product_id_type': '',
            'feed_product_type': 'kurta',
            'standard_price': final_price,
            'quantity': 50,
            'update_delete': 'Update',
            'product_description': description,
            'bullet_point1': "Care Instructions: Machine Wash",
            'bullet_point2': "Fit Type: Regular Fit",
            'bullet_point3': "Style: Modern & Trendy Design",
            'department_name': 'Women',
            'generic_keywords': 'kurti for women, latest design, cotton kurta, party wear'
        }

        # --- Image Processing ---
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
                    
                    gh_link = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{filename}"
                    
                    if i == 1: amz_row['main_image_url'] = gh_link
                    else: amz_row[f'other_image_url{i-1}'] = gh_link
                    
                except Exception as e:
                    pass 

        amazon_data.append(amz_row)

    pd.DataFrame(amazon_data).to_excel(OUTPUT_FILE, index=False)
    print("\n✅ PROCESS COMPLETE!")
    print(f"💰 Profit Margin Set: ₹{FIXED_MARGIN}")
    print(f"📂 Output File: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_images()
