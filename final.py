import pandas as pd
import requests
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import io
import os
import time

# ==========================================
# ⚙️ SETTINGS
# ==========================================
GITHUB_USER = "mademoneyai-hub"
REPO_NAME = "sweet-india-products"
BRANCH = "main"

INPUT_FILE = "final_meesho_data.xlsx"   
OUTPUT_FILE = "Final_Amazon_Upload.xlsx"

# --- Image Settings ---
HD_SIZE = 1200         

# --- 💰 Price & Profit Settings ---
FIXED_MARGIN = 200     
DEFAULT_WEIGHT = 450   # Grams
# ==========================================

def calculate_selling_price(making_cost, product_title):
    try:
        clean_price = str(making_cost).lower()
        clean_price = clean_price.replace('rs.', '').replace('rs', '').replace('₹', '').replace(',', '').replace(' ', '')
        cost = float(clean_price)
    except:
        cost = 0 
    
    weight = DEFAULT_WEIGHT
    title_lower = str(product_title).lower()
    if any(x in title_lower for x in ['coat', 'jacket', 'heavy', 'lehenga', 'gown', 'set of 2']):
        weight = 900
    elif any(x in title_lower for x in ['shoe', 'boot', 'sandal']):
        weight = 800
    
    shipping_charge = 0
    if weight <= 500: shipping_charge = 74
    elif weight <= 1000: shipping_charge = 111
    else: shipping_charge = 153

    return int(cost + shipping_charge + FIXED_MARGIN)


def remove_watermark_opencv(pil_img):
    """
    OpenCV Telea Inpainting Logic (No Blur, Only Clean Removal)
    """
    # 1. Convert PIL image to OpenCV format (NumPy Array)
    open_cv_image = np.array(pil_img)
    
    # 2. Convert RGB to BGR (OpenCV uses BGR)
    if open_cv_image.shape[2] == 3:
        img = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
    elif open_cv_image.shape[2] == 4:
        img = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
    else:
        img = open_cv_image

    h, w = img.shape[:2]

    # 3. Sirf Bottom 15% Area Scan karo
    scan_height = int(h * 0.15)
    if scan_height < 10: scan_height = 10
    
    roi = img[h - scan_height:h, 0:w]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 4. Bright White Pixels Detect (Threshold > 210)
    _, bright_mask = cv2.threshold(gray_roi, 210, 255, cv2.THRESH_BINARY)

    # 5. Edge Detection (Sirf edges/text pakadne ke liye)
    edges = cv2.Canny(gray_roi, 100, 200)
    kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=1)

    # 6. Combine Masks & Find Box
    combined_mask = cv2.bitwise_and(bright_mask, edges_dilated)
    x, y, box_w, box_h = cv2.boundingRect(combined_mask)

    # Ignore cases: No text, or text box is too wide (border of dress)
    if box_w == 0 or box_h == 0 or box_w > (w * 0.80):
        return pil_img # Return original PIL image safely

    # 7. Inpainting Mask
    inpaint_mask_roi = np.zeros_like(gray_roi)
    inpaint_mask_roi[y:y+box_h, x:x+box_w] = bright_mask[y:y+box_h, x:x+box_w]
    inpaint_mask_roi = cv2.dilate(inpaint_mask_roi, kernel, iterations=1)

    full_mask = np.zeros((h, w), dtype=np.uint8)
    full_mask[h - scan_height:h, 0:w] = inpaint_mask_roi

    # 8. Apply Inpainting (Clean Removal)
    result = cv2.inpaint(img, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # 9. Convert back to PIL Image
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)


def make_dslr_quality(img):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = ImageOps.exif_transpose(img)

    # 1. OpenCV Watermark Removal (Telea Inpainting)
    img = remove_watermark_opencv(img)

    # 2. Resize to HD
    w, h = img.size
    if w < HD_SIZE or h < HD_SIZE:
        ratio = HD_SIZE / min(w, h)
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # 3. Enhance Quality
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.3)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    
    return img


def process_images():
    print("🚀 Script Started (OpenCV Watermark Removal + GitHub Links)...")
    
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

        # --- Image Downloading & Processing ---
        for i in range(1, 5):
            col_name = f"Image {i}"
            if col_name in row and pd.notna(row[col_name]):
                url = row[col_name]
                try:
                    res = requests.get(url, timeout=10)
                    img = Image.open(io.BytesIO(res.content))
                    
                    # Core Processing
                    final_img = make_dslr_quality(img)

                    # Save File locally
                    filename = f"{sku}_img{i}.jpg" 
                    final_img.save(filename, quality=95)
                    
                    # Generate GitHub Link
                    gh_link = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{filename}"
                    
                    # Assign link to Excel columns
                    if i == 1: amz_row['main_image_url'] = gh_link
                    else: amz_row[f'other_image_url{i-1}'] = gh_link
                    
                except Exception as e:
                    pass 

        amazon_data.append(amz_row)

    pd.DataFrame(amazon_data).to_excel(OUTPUT_FILE, index=False)
    print("\n✅ PROCESS COMPLETE!")
    print(f"💰 Profit Margin Set: ₹{FIXED_MARGIN}")
    print(f"📂 Output File Ready: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_images()
