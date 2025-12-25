import pandas as pd
import requests
from PIL import Image
# from rembg import remove  # <-- Agar rembg install hai aur use karna hai to '#' hata dein
import io
import os

# --- SETTINGS (Isse dhyan se bharein) ---
GITHUB_USER = "mademoneyai-hub"      # <--- YAHAN APNA GITHUB USERNAME LIKHEIN
REPO_NAME = "sweet-india-products"
BRANCH = "main"

INPUT_FILE = "final_meesho_data.xlsx"   # Aapki Meesho wali file
OUTPUT_FILE = "Final_Amazon_Upload.xlsx" # Jo Amazon pe jayegi
CROP_BOTTOM = 60 # Niche se kitna kaatna hai (Text hatane ke liye)
# ----------------------------------------

def process_and_organize():
    print("Excel file padh raha hu...")
    try:
        df = pd.read_excel(INPUT_FILE)
    except:
        print(f"Error: '{INPUT_FILE}' nahi mili! Naam check karein.")
        return

    amazon_data = []
    print(f"Total {len(df)} products hain. Processing shuru...")

    for index, row in df.iterrows():
        # Step A: Unique SKU Banana (Taaki mix na ho)
        sku = f"SWEET_{index+1001}" # Result: SWEET_1001, SWEET_1002...
        
        print(f"Working on: {sku}...")

        # Step B: Amazon Data Row Taiyaar Karna
        amz_row = {
            'item_sku': sku,
            'brand_name': 'Sweet India',
            'external_product_id': '', 
            'external_product_id_type': '',
            'item_name': f"Premium {str(row.get('Title', 'Fashion Product'))}",
            'feed_product_type': 'kurta', # Category
            'standard_price': row.get('Price', 999),
            'quantity': 50,
            'update_delete': 'Update',
            'product_description': str(row.get('Description', ''))
        }

        # Step C: Images Download -> Edit -> Rename -> Link
        # Hum 4 images check karenge (Image 1, Image 2, Image 3, Image 4)
        for i in range(1, 5):
            col_name = f"Image {i}"
            
            # Agar Excel mein link hai, tabhi process karein
            if col_name in row and pd.notna(row[col_name]):
                url = row[col_name]
                try:
                    # 1. Download
                    res = requests.get(url, timeout=10)
                    img = Image.open(io.BytesIO(res.content))
                    
                    # 2. Edit (Crop Bottom Text)
                    w, h = img.size
                    if h > 100:
                        img = img.crop((0, 0, w, h - CROP_BOTTOM))
                    
                    # 3. Rename & Save (SKU ke naam se save karein)
                    filename = f"{sku}_img{i}.jpg" # Example: SWEET_1001_img1.jpg
                    img.save(filename, quality=90) # Folder me save ho gayi
                    
                    # 4. GitHub Link Banana (Bilkul wahi naam jo save kiya)
                    gh_link = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{filename}"
                    
                    # 5. Excel mein Link dalna
                    if i == 1: amz_row['main_image_url'] = gh_link
                    else: amz_row[f'other_image_url{i-1}'] = gh_link
                    
                except Exception as e:
                    print(f"  ❌ Error image {i}: {e}")

        amazon_data.append(amz_row)

    # Step D: Final Excel Save Karna
    pd.DataFrame(amazon_data).to_excel(OUTPUT_FILE, index=False)
    print("\n------------------------------------------------")
    print("✅ PROCESS COMPLETE!")
    print(f"1. Saari edited photos folder mein aa gayi hain (Naam: {sku}...)")
    print(f"2. Nayi Excel '{OUTPUT_FILE}' ban gayi hai jisme GitHub links hain.")
    print("------------------------------------------------")

if __name__ == "__main__":
    process_and_organize()
