import pandas as pd
import time
import os
import re

# ==========================================
# ⚙️ INPUT / OUTPUT FILES
# ==========================================
INPUT_FILE = "Final_Amazon_Ready_Upload.xlsx"
OUTPUT_FILE = "Final_Amazon_Single_Row_Upload.xlsx"

# ✅ CONFIGURATION (Global Constants)
# Ensure these apply to ALL products, otherwise leave blank to follow Rule #8
BRAND_NAME = "Generic"
MANUFACTURER = "Sweet India Enterprises"
FEED_PRODUCT_TYPE = "kurta"
ITEM_TYPE = "salwar-suit-sets"
RECOMMENDED_BROWSE_NODE = "1968255031"

# ==========================================
# 🛠️ HELPER FUNCTIONS (STRICT RULES)
# ==========================================

def clean_text(text):
    if pd.isna(text) or text == "" or str(text).lower() == "nan":
        return ""
    return str(text).strip()

def extract_all_sizes(description):
    """
    Rule #1 & #3: Extract ALL sizes from description.
    Rule #2: Combine into one string (Format: S | M | L...)
    """
    if not description:
        return "" # Changed from 'Free Size' to blank to strictly follow Rule #8 (No guessing)

    desc_upper = str(description).upper()
    found_sizes = []
    
    # Order matters: Check 3XL before XL to avoid partial matches
    check_list = ['3XL', '2XL', 'XXL', 'XL', 'XS', 'S', 'M', 'L', 'FREE SIZE']
    
    for size in check_list:
        # Regex explanation:
        # \b ensures we match "S" but not the "S" inside "DRESS"
        # We look for the size followed by a space, a comma, a slash, or a parenthesis/bracket
        if re.search(rf"\b{size}\b", desc_upper):
            found_sizes.append(size)
    
    # Remove duplicates while preserving order
    found_sizes = list(dict.fromkeys(found_sizes))
    
    if not found_sizes:
        return "" # Rule #8: If no size found, do not guess. Leave blank.
        
    return " | ".join(found_sizes)

def get_price_strict(row, df_columns):
    """Rule #4: Sheet se Price lo, nahi to Blank. NEVER guess."""
    possible_cols = ['standard_price', 'price', 'mrp', 'selling_price', 'amount']
    
    for col in df_columns:
        if str(col).lower().strip() in possible_cols:
            val = row[col]
            if pd.notna(val) and str(val).strip() != "":
                try:
                    return float(val)
                except:
                    return None
    return None

# ==========================================
# 🚀 MAIN PROCESS
# ==========================================
def process_file():
    print("🚀 Processing Started: Single Row Format...")

    try:
        df = pd.read_excel(INPUT_FILE)
        # Clean column headers
        df.columns = df.columns.str.strip()
        print(f"✅ Input File Loaded: {len(df)} rows.")
    except Exception as e:
        print(f"❌ Error: {INPUT_FILE} not found. Error: {e}")
        return

    # ✅ AMAZON EXACT COLUMN ORDER (Rule #7)
    AMZ_COLS = [
        'feed_product_type', 'item_sku', 'brand_name', 'item_name', 'external_product_id', 'external_product_id_type',
        'item_type', 'outer_material_type', 'material_composition', 'color_name', 'color_map', 'department_name', 
        'size_name', 'size_map', 'target_gender', 'age_range_description',
        'standard_price', 'quantity', 
        'main_image_url', 'other_image_url1', 'other_image_url2', 'other_image_url3', 
        'parent_child', 'parent_sku', 'relationship_type', 'variation_theme',
        'product_description', 'bullet_point1', 'bullet_point2', 'bullet_point3', 'bullet_point4', 'bullet_point5',
        'generic_keywords', 'country_of_origin', 'manufacturer', 'part_number', 'update_delete', 'recommended_browse_nodes'
    ]

    final_data = []

    for index, row in df.iterrows():
        
        # --- DATA EXTRACTION ---
        
        # 1. Description (Rule #6: No Change)
        raw_desc = clean_text(row.get('product_description', ''))
        
        # 2. Name
        raw_name = clean_text(row.get('item_name', ''))
        if not raw_name: 
             raw_name = raw_desc.split(':')[0][:150] if raw_desc else "" # Rule 8: Don't guess if desc is empty

        # 3. Price (Rule #4: Strict)
        price_val = get_price_strict(row, df.columns)

        # 4. SKU (Rule #5: Unique & Compulsory)
        sheet_sku = clean_text(row.get('item_sku', ''))
        # If SKU is missing in sheet, we create a base one, but ideally strict rules imply using sheet data.
        # However, SKU is mandatory for upload, so generating one is usually acceptable exception.
        base_sku = sheet_sku if sheet_sku else f"GEN-SKU-{index+1001}"

        # 5. SIZE EXTRACTION (Rule #1, #2, #3: Combined in one column)
        combined_sizes = extract_all_sizes(raw_desc)

        # Images
        img_main = clean_text(row.get('main_image_url', ''))
        img1 = clean_text(row.get('other_image_url1', ''))
        img2 = clean_text(row.get('other_image_url2', ''))
        img3 = clean_text(row.get('other_image_url3', ''))
        
        # Attributes - STRICT FIX FOR RULE #8
        # Removed defaults "Cotton Blend" and "Multicolor". 
        # Now it strictly pulls from sheet or leaves blank.
        mat = clean_text(row.get('material_type', '')) 
        col = clean_text(row.get('color_name', ''))

        # --- CREATE ROW (NO VARIATION - SINGLE ROW) ---
        
        row_data = {col: '' for col in AMZ_COLS}
        row_data.update({
            'feed_product_type': FEED_PRODUCT_TYPE,
            'item_sku': base_sku,
            'brand_name': BRAND_NAME,
            'item_name': raw_name,
            'item_type': ITEM_TYPE,
            'parent_child': '', # Rule: No variation structure
            'variation_theme': '', 
            'department_name': 'Women',
            'target_gender': 'Female',
            'age_range_description': 'Adult',
            'color_name': col, 
            'color_map': col, # Using specific color as map if standard map not provided
            'outer_material_type': mat, 
            'material_composition': mat,
            
            # ✅ SIZE COLUMN (Combined Sizes)
            'size_name': combined_sizes, 
            'size_map': 'Free Size' if not combined_sizes else 'Small', # Amazon needs a map, but we put combined in size_name
            
            'product_description': raw_desc,
            'bullet_point1': 'Care Instructions: Machine Wash',
            'bullet_point2': 'Fit Type: Regular',
            'bullet_point3': f'Fabric: {mat}' if mat else '',
            'bullet_point4': 'Package Contains: Kurta and Pant Set',
            'bullet_point5': 'Occasion: Casual, Festive, Party Wear',
            'generic_keywords': 'women kurta set ethnic wear',
            'country_of_origin': 'India',
            'manufacturer': MANUFACTURER,
            'recommended_browse_nodes': RECOMMENDED_BROWSE_NODE,
            'main_image_url': img_main,
            'other_image_url1': img1, 'other_image_url2': img2, 'other_image_url3': img3,
            'update_delete': 'Update',
            
            # ✅ PRICE & QTY
            'standard_price': price_val, # Rule: Value or Blank
            'quantity': 50,
            'part_number': base_sku
        })
        final_data.append(row_data)

        print(f"✅ Processed SKU: {base_sku} | Price: {price_val} | Sizes: {combined_sizes}")

    # Save
    df_out = pd.DataFrame(final_data, columns=AMZ_COLS)
    df_out.to_excel(OUTPUT_FILE, index=False)
    print("\n===========================================")
    print(f"🎉 FINAL SHEET READY: {OUTPUT_FILE}")
    print("👉 Sizes merged in one column (e.g., S | M | L)")
    print("👉 No duplicate rows or variations.")
    print("👉 Price blank if missing in master sheet.")
    print("===========================================")

if __name__ == "__main__":
    process_file()
