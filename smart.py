import pandas as pd
import random
import string

# --- Configuration (Yaha apni details dalein) ---
BRAND_NAME = "Sweet India"
MANUFACTURER = "Sweet India Pvt Ltd"
COUNTRY_OF_ORIGIN = "IN"

# --- Raw Data (Example Products - Isko aap Meesho scraping data se replace kar sakte hain) ---
# Example: Product Type, Color, Size, Material, Price
products_input = [
    {"type": "Cotton Kurti", "color": "Blue", "size": "M", "material": "Pure Cotton", "price": 499, "gender": "Women"},
    {"type": "Printed Leggings", "color": "Black", "size": "L", "material": "Lycra", "price": 299, "gender": "Women"},
    {"type": "Designer Sherwani", "color": "Gold", "size": "XL", "material": "Silk Blend", "price": 1499, "gender": "Men"},
    {"type": "Casual Shirt", "color": "White", "size": "40", "material": "Cotton Blend", "price": 699, "gender": "Men"},
]

# --- Helper Functions ---

def generate_sku(product):
    """Generates a unique professional SKU"""
    # Format: BRAND-TYPE-COLOR-SIZE-RANDOM
    short_type = product['type'].split()[0].upper()[:3]
    short_color = product['color'].upper()[:3]
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{BRAND_NAME[:3].upper()}-{short_type}-{short_color}-{product['size']}-{random_part}"

def generate_seo_title(product):
    """Creates a Keyword-Rich Title for Amazon SEO"""
    # Formula: Brand + Sub-Brand + Model + Specs + Keywords
    return f"{BRAND_NAME} {product['type']} for {product['gender']} | {product['material']} | {product['color']} | Stylish & Comfortable Daily Wear"

def generate_bullet_points(product):
    """Generates 5 High-Converting Bullet Points"""
    return [
        f"MATERIAL: Premium quality {product['material']} that is breathable and comfortable for all-day wear.",
        f"DESIGN: Stylish {product['type']} featuring a modern design suitable for casual and festive occasions.",
        f"FIT TYPE: Regular fit designed to provide a comfortable range of motion.",
        f"CARE INSTRUCTIONS: Machine wash or hand wash with mild detergent; dry in shade.",
        f"MADE IN INDIA: Proudly manufactured in India by {MANUFACTURER}."
    ]

def generate_keywords(product):
    """Generates Backend Search Terms (Hidden Keywords)"""
    base_keywords = [
        f"latest {product['type']}",
        f"{product['color']} {product['type']} for {product['gender']}",
        "party wear",
        "casual wear",
        "trending fashion",
        "under 500",
        "new arrival",
        "comfortable clothing"
    ]
    return ", ".join(base_keywords)

# --- Main Logic ---

amazon_data = []

for item in products_input:
    bullets = generate_bullet_points(item)
    
    row = {
        # Identity
        "feed_product_type": "clothing",
        "item_sku": generate_sku(item),
        "brand_name": BRAND_NAME,
        "external_product_id": "", # UPC/EAN yaha aayega agar hai toh
        "external_product_id_type": "GTIN", 
        
        # Core Content
        "item_name": generate_seo_title(item),
        "product_description": f"Upgrade your wardrobe with this stylish {item['type']} from {BRAND_NAME}. Made from {item['material']}, it ensures comfort and style. Perfect for daily use or special occasions.",
        
        # Bullet Points (Crucial for Conversion)
        "bullet_point1": bullets[0],
        "bullet_point2": bullets[1],
        "bullet_point3": bullets[2],
        "bullet_point4": bullets[3],
        "bullet_point5": bullets[4],
        
        # Discovery (SEO)
        "generic_keywords": generate_keywords(item),
        "color_name": item['color'],
        "size_name": item['size'],
        "material_type": item['material'],
        "department_name": item['gender'],
        
        # Offer & Price
        "standard_price": item['price'],
        "quantity": 100, # Default stock
        "merchant_shipping_group_name": "Default Amazon Template",
        
        # Compliance
        "country_of_origin": COUNTRY_OF_ORIGIN,
        "manufacturer": MANUFACTURER,
        "fulfillment_latency": 2, # Handling Time
    }
    
    amazon_data.append(row)

# --- Create DataFrame and Save ---
df = pd.DataFrame(amazon_data)

# Ensuring no empty columns for critical fields (filling generic text if needed)
df.fillna("Not Applicable", inplace=True)

# Export to CSV
output_filename = "amazon_bulk_upload_ready.csv"
df.to_csv(output_filename, index=False)

print(f"Success! '{output_filename}' generate ho gayi hai.")
print("Example generated SKU:", df.loc[0, 'item_sku'])
print("Example generated Title:", df.loc[0, 'item_name'])