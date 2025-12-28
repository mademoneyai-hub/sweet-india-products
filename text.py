import time
import pandas as pd
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. SETTINGS ---
AMAZON_EMAIL = "multitaskenterprises36@gmail.com" # <--- Yahan apna email dalein
AMAZON_PASS = "abhay@1234" # <--- Yahan apna password dalein

# Excel File Path
EXCEL_FILE = r"C:\Users\Sharma Family\Desktop\sweet-india-products\sweet-india-products\Final_Amazon_Ready_Upload.xlsx"

# --- 2. BROWSER SETUP ---
options = Options()
profile_path = r"C:\BotData"
options.add_argument(f"user-data-dir={profile_path}")
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20) # 20 second tak wait karega

# Temp Folder
TEMP_DIR = r"C:\Users\Sharma Family\Desktop\TempImages"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# --- 3. LOGIN & START ---
driver.get("https://sellercentral.amazon.in/product-search?ref=xx_catadd_dnav_xx")
time.sleep(3)

# Auto-Login Logic
if "Sign-In" in driver.title or "ap_email" in driver.page_source:
    try:
        driver.find_element(By.ID, "ap_email").clear()
        driver.find_element(By.ID, "ap_email").send_keys(AMAZON_EMAIL)
        try: driver.find_element(By.ID, "continue").click()
        except: pass
        time.sleep(1)
        driver.find_element(By.ID, "ap_password").send_keys(AMAZON_PASS)
        try: driver.find_element(By.NAME, "rememberMe").click()
        except: pass
        driver.find_element(By.ID, "signInSubmit").click()
    except:
        pass

print("\n" + "="*40)
print("🛑 WAIT: Login hone dein.")
print("Jab 'List Your Products' page dikh jaye, tab ENTER dabayein.")
print("="*40 + "\n")
input("Waiting for Enter...") 

# --- 4. MAIN PROCESS ---
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
else:
    print("❌ Excel File nahi mili.")
    exit()

for index, row in df.iterrows():
    try:
        # Sirf Main Image aur Description uthayenge
        img_link = str(row['main_image_url'])       
        description_text = str(row['product_description']) 
        
        # Row index print kar rahe hain (Product count)
        print(f"\n--- Processing Product {index+1} ---")

        # A. DOWNLOAD 1 IMAGE
        if "http" in img_link:
            current_img_name = f"product_{index}.jpg"
            full_img_path = os.path.join(TEMP_DIR, current_img_name)
            
            # Clean old file
            if os.path.exists(full_img_path): os.remove(full_img_path)

            try:
                response = requests.get(img_link)
                if response.status_code == 200:
                    with open(full_img_path, 'wb') as f:
                        f.write(response.content)
                    print("Image Downloaded (1 Image).")
                else:
                    print("❌ Link Dead.")
                    continue
            except:
                print("❌ Download Error.")
                continue
        else:
            print("❌ No Link.")
            continue

        # B. UPLOAD PROCESS
        driver.get("https://sellercentral.amazon.in/product-search?ref=xx_catadd_dnav_xx")
        time.sleep(4)
        
        try:
            # 1. 'Product image' Tab par Click karna (Zaroori step)
            try:
                # Hum dhoondhenge wo card jisme "Product image" likha hai
                # Ye XPath Amazon ke card structure ke liye hai
                tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'box')]//span[contains(text(), 'Product image')] | //*[contains(text(),'Product image')]")))
                tab.click()
                print("Clicked 'Product image' tab.")
                time.sleep(2)
            except:
                print("⚠️ Tab click nahi hua (shayad pehle se open hai).")

            # 2. Upload Button Dhoondna
            print("Looking for upload button...")
            # File input hidden hota hai, isliye 'presence' check karenge
            file_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
            
            file_input.send_keys(full_img_path)
            print("Image Uploading...")
            time.sleep(8) # Upload hone ka time dein
            
            # 3. Description Fill & Submit
            # Upload ke baad hi description box aata hai
            try:
                desc_box = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "textarea")))
                desc_box.clear()
                desc_box.send_keys(description_text)
                print("Description Filled.")
                
                # Submit Button
                submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                submit_btn.click()
                print("✅ Submitted.")
                
                # --- IMPORTANT: NEXT STEP ---
                print("Waiting for next page (Details)...")
                time.sleep(10) # Yahan code rukega taki aap dekh sakein agla page kya hai
                
            except Exception as e:
                print(f"❌ Description/Submit Error: {e}")
                # Screenshot lein taaki error dikh jaye
                driver.save_screenshot(f"error_row_{index}.png")

            # Clean up
            if os.path.exists(full_img_path):
                os.remove(full_img_path)
                
        except Exception as e:
            print(f"❌ Upload Step Error: {e}")
            driver.save_screenshot(f"upload_error_{index}.png")

    except Exception as e:
        print(f"Main Error: {e}")

print("Done.")
