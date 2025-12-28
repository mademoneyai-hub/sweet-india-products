import pandas as pd
import os

# --- STEP 1: FILE NAMES ---
source_file = 'Final_Amazon_Ready_Upload.xlsx'       # Aapki data wali file
output_file = 'Amazon_High_Ranking_Upload.xlsx'      # Amazon upload wali file

# --- STEP 2: SMART AI LOGIC (SEO & Category) ---
def get_smart_details(row):
    # Title aur Brand check karna
    title = str(row.get('item_name', '')).lower()
    if title == 'nan': title = str(row.get('Title', '')).lower()
    
    # LOGIC A: MITHAI / FOOD
    if any(x in title for x in ['sweet', 'mithai', 'kaju', 'laddu', 'barfi', 'ghee', 'snack', 'almond']):
        return {
            'type': 'food',
            'keywords': 'Indian Sweets, Traditional Mithai, Diwali Gift Pack, Fresh Snacks, Sweet India, Gourmet Foods, Family Pack',
            'desc_start': 'Authentic Indian Taste. Freshly packed with pure ingredients. Perfect for gifting.'
        }
    
    # LOGIC B: KAPDA / CLOTHING
    elif any(x in title for x in ['kurta', 'kurti', 'saree', 'shirt', 'top', 'dress', 'cotton']):
        return {
            'type': 'kurta' if 'kurta' in title else 'shirt',
            'keywords': 'Latest Fashion, Trendy Wear, Cotton Blend, Comfortable Fit, Party Wear, Casual Look, Ethnic Wear',
            'desc_start': 'Premium quality fabric ensuring comfort and style for every occasion.'
        }
    
    # LOGIC C: DEFAULT
    else:
        return {
            'type': 'product',
            'keywords': 'Best Seller, New Arrival, Premium Quality, High Rated',
            'desc_start': 'High quality product designed for your needs.'
        }

# --- STEP 3: DATA PROCESS ---
if not os.path.exists(source_file):
    print(f"Error: '{source_file}' nahi mili. Check karein file folder mein hai ya nahi.")
else:
    try:
        print("Processing... High Ranking SEO add kar raha hoon...")
        df_source = pd.read_excel(source_file)
        
        final_data = []

        for index, row in df_source.iterrows():
            # 1. Purana Data Copy (Flexible Matching)
            title = row.get('item_name') or row.get('Title') or row.get('Product Name')
            sku = row.get('item_sku') or row.get('SKU')
            price = row.get('standard_price') or row.get('Price') or 999
            qty = row.get('quantity') or row.get('Stock') or 100
            
            # 2. Smart AI Details
            smart_info = get_smart_details(row)
            
            # 3. Nayi Row Banana
            new_row = {
                'feed_product_type': smart_info['type'], 
                'item_sku': sku,
                'brand_name': 'Sweet India',
                'item_name': title,
                'external_product_id': row.get('external_product_id', ''),
                'external_product_id_type': 'EAN', 
                'standard_price': price,
                'quantity': qty,
                'generic_keywords': smart_info['keywords'], # SEO Keywords
                'main_image_url': row.get('main_image_url') or row.get('Image1'),
                'other_image_url1': row.get('other_image_url1') or row.get('Image2'),
                'other_image_url2': row.get('other_image_url2') or row.get('Image3'),
                'other_image_url3': row.get('other_image_url3') or row.get('Image4'),
                'item_description': row.get('item_description') or smart_info['desc_start'],
                'bullet_point1': row.get('bullet_point1') or 'Premium Quality Product',
                'bullet_point2': 'Satisfaction Guaranteed',
                'update_delete': 'Update'
            }
            final_data.append(new_row)

        # --- STEP 4: SAVE FILE ---
        df_final = pd.DataFrame(final_data)
        
        # Format set karna
        cols = ['feed_product_type', 'item_sku', 'brand_name', 'item_name', 
                'standard_price', 'quantity', 'generic_keywords', 'item_description', 
                'main_image_url', 'other_image_url1', 'update_delete']
        
        available_cols = [c for c in cols if c in df_final.columns]
        remaining = [c for c in df_final.columns if c not in available_cols]
        df_final = df_final[available_cols + remaining]

        df_final.to_excel(output_file, index=False)

        print("\n" + "="*50)
        print(f"✅ SUCCESS! '{output_file}' ban gayi hai.")
        print("👉 SEO aur Category fix ho gayi hai.")
        print("="*50)

    except Exception as e:
        print(f"\n❌ Error: {e}")
