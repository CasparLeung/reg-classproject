from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import re
import json
from prereq_alg import parse_prereq_json  # your custom parser function

# --- Chrome driver setup ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# --- Define course codes to scrape ---
course_codes = [
     "STA 035B", "STA 035C"
]

# --- Scraping Function ---
def scrape_course_prerequisites(driver, course_code):
    try:
        driver.get("https://catalog.ucdavis.edu/course-search/")

        # Find search box
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "crit-keyword"))
        )
        search_box.clear()
        search_box.send_keys(course_code)
        driver.find_element(By.ID, "search-button").click()

        # Click first result
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "result__link"))
        )
        first_result.click()

        # Find prerequisites
        try:
            prereq_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "p.text.courseblockdetail.detail-prerequisite")
                )
            )
            prereq_text = prereq_element.text.strip()
            prereq_text = re.sub(r'^Prerequisite\(s\):\s*', '', prereq_text)
            print(f"Prerequisites for {course_code}: {prereq_text}")
            return prereq_text
        except TimeoutException:
            print(f"No prerequisites found for {course_code}")
            return ""

    except Exception as e:
        logging.error(f"Error while processing {course_code}: {e}")
        return ""

# --- Scrape prerequisites for each course ---
prereq_texts = []
for code in course_codes:
    prereq = scrape_course_prerequisites(driver, code)
    prereq_texts.append(prereq)

# --- Parse using prereq_alg ---
output = {}

for code, text in zip(course_codes, prereq_texts):
    print(f"Processing {code} with text: '{text}'")

    if not text.strip():
        print(f"Skipping {code} because no prereq text found.")
        output[code] = {}
        continue

    try:
        parsed_json = parse_prereq_json([code], [text])
        output.update(parsed_json)
    except Exception as e:
        logging.error(f"Failed to parse {code}: {e}")
        output[code] = {}

# --- Save to JSON ---
output_file = r"C:\\Users\\PC4\\OneDrive\\Desktop\\reg classproject\\parsed_prereqs.json"
with open(output_file, "w") as f:
    json.dump(output, f, indent=2)

print(f"\u2705 Prerequisite structure saved to {output_file}")

# --- Cleanup ---
driver.quit()