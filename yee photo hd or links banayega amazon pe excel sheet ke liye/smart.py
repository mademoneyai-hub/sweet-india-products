import pandas as pd
import os

# ==========================================
# ⚙️ SETTINGS
# ==========================================
# 1. Wo file jisme GitHub Links aur data hai
SOURCE_FILE = "Final_Amazon_Upload_Ready.xlsx" 

# 2. Amazon ki khali Template (CSV/Excel)
TEMPLATE_FILE = "template.xlsx - Sheet1.csv"

# 3. Jo file Amazon par upload hogi
OUTPUT_FILE = "Amazon_SEO_Final_Upload.xlsx"

BRAND_NAME = "Sweet India"
# ==========================================

def get_high_ranking_seo(title):
    """Smart SEO Logic: Bullet Points aur Description generate karta hai"""
    clean_title = str(title).replace("Sweet India Premium ", "").replace("Sweet India ", "")
    
    # 🚀 High-Ranking Bullet Points
    bullets = [
        f"PREMIUM QUALITY FABRIC: This {clean_title} is crafted from high-quality, breathable fabric that ensures maximum comfort for all-day wear.",
        f"STYLISH & TRENDY: Featuring a contemporary design with elegant patterns, it's a perfect choice for ethnic, casual, and festive occasions.",
        "COMFORTABLE FIT: Carefully tailored to provide a flattering fit. Pairs effortlessly with leggings, palazzos, or jeans for a complete look.",
        f"VERSATILE WARDROBE ESSENTIAL: An ideal outfit for office wear, weddings, parties, or daily outings. A must-have for every fashion-forward woman.",
        "EASY CARE & DURABLE: Machine washable and resistant to shrinkage or color fading, maintaining its premium look even after many washes."
    ]
    
    # 🚀 SEO-Rich Description
    description = (
        f"Elevate your ethnic fashion game with the {BRAND_NAME} Premium {clean_title}. "
        f"Our {clean_title} is designed with the modern Indian woman in mind, blending traditional aesthetics with modern trends. "
        "Made from superior grade fabric, it offers a luxurious feel and exceptional durability. "
        "Whether you are attending a festive celebration or a casual get-together, this product promises a stunning and graceful appearance. "
        "Add this timeless piece to your collection and experience the perfect mix of style and comfort."
    )
    
    return bullets, description

def process_flat_sheet():
    print("🚀 SEO Optimization & Data Transfer Start...")

    # 1. Template Load Karo (Headers index 1 par hote hain)
    try:
        df_temp = pd.read_csv(TEMPLATE_FILE, header=1)
        template_cols = df_temp.columns.tolist()
    except Exception as e:
        print(f"❌ Template Error: {e}")
        return

    # 2. Data Source Load Karo (GitHub Link wali sheet)
    try:
        df_source = pd.read_excel(SOURCE_FILE)
    except:
        print(f"❌ '{SOURCE_FILE}' nahi mili! Naam check karein.")
        return

    final_data = []

    for index, row in df_source.iterrows():
        # Empty row based on template columns
        new_row = {col: '' for col in template_cols}
        
        # Details Fetch
        sku = row.get('item_sku', row.get('SKU', f"SWEET_{index+1001}"))
        title = row.get('item_name', row.get('Title', 'Product'))
        price = row.get('standard_price', row.get('Standard Price', 999))
        
        # SEO Content Generate Karo
        bullets, description = get_high_ranking_seo(title)

        print(f"   ⚙️ Processing {sku} with High SEO...")

        # Helper to fill columns safely
        def fill(col_name, val):
            if col_name in new_row:
                new_row[col_name] = val

        # --- MANDATORY IDENTITY ---
        fill('SKU', sku)
        fill('Listing Action', 'Update')
        fill('Product Type', 'kurta')
        fill('Item Name', title if BRAND_NAME in str(title) else f"{BRAND_NAME} Premium {title}")
        fill('Brand Name', BRAND_NAME)
        fill('Standard Price', price)
        fill('Quantity', 50)
        
        # --- SEO CONTENT ---
        fill('Product Description', description)
        fill('Bullet Point 1', bullets[0])
        fill('Bullet Point 2', bullets[1])
        fill('Bullet Point 3', bullets[2])
        fill('Bullet Point 4', bullets[3])
        fill('Bullet Point 5', bullets[4])
        
        # --- COMPLIANCE & HSN ---
        fill('HSN Code', '6304') # Standard Textile HSN
        fill('Country/Region of Origin', 'India')
        fill('Condition Type', 'New')
        fill('Manufacturer', BRAND_NAME)
        fill('Material Type', 'Cotton Blend')
        fill('Department', 'Women')
        fill('Color Map', 'Multicolor')
        fill('Merchant Shipping Group Name', 'Migrated Template')

        # --- IMAGE LINKS (GitHub URL Copy) ---
        # Main Image
        img1 = row.get('main_image_url', row.get('Main Image Location', ''))
        fill('Main Image Location', img1)

        # Other Images (Amazon column handles differently)
        other_img_indices = [i for i, x in enumerate(template_cols) if x == 'Other Image Location']
        
        # Hum check karenge ki source sheet me links kahan hain
        other_urls = []
        for col in ['other_image_url1', 'other_image_url2', 'other_image_url3', 'Other Image Location1', 'Other Image Location2']:
            if col in row and pd.notna(row[col]) and row[col] != '':
                other_urls.append(row[col])
        
        for i, url in enumerate(other_urls):
            if i < len(other_img_indices):
                new_row[template_cols[other_img_indices[i]]] = url

        final_data.append(new_row)

    # Save to Excel
    df_final = pd.DataFrame(final_data)
    df_final.to_excel(OUTPUT_FILE, index=False)
    
    print("\n✅ MISSION COMPLETE!")
    print(f"📂 SEO File Saved: {OUTPUT_FILE}")
    print("Ab aap ye file seedhe Amazon Seller Central par upload kar sakte hain.")

if __name__ == "__main__":
    process_flat_sheet()
 
