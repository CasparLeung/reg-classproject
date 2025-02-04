from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import logging
from prereq_alg import break_down_prereq_text, flatten_breakdown, save_breakdown_to_csv
import os

# Configure logging with force=True to avoid conflicts
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)

def scrape_course_prerequisites(driver, course_code):
    """
    Scrapes the prerequisite text from the UC Davis course catalog for a given course code.
    """
    try:
        # Open the UC Davis course catalog search page
        driver.get("https://catalog.ucdavis.edu/course-search/")

        # Locate the search box, input the course code, and submit the search
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "crit-keyword"))
        )
        search_box.clear()
        search_box.send_keys(course_code)
        
        # Click the search button
        search_button = driver.find_element(By.ID, "search-button")
        search_button.click()

        # Wait for the search results to load and click the first result link
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "result__link"))
        )
        first_result.click()

        # Check if the prerequisite element exists and extract its content
        try:
            prerequisite_text_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.text.courseblockdetail.detail-prerequisite"))
            )
            prerequisite_text_content = re.sub(r'^Prerequisite\(s\):\s*', '', prerequisite_text_element.text)
            print(f"Prerequisites for {course_code}: {prerequisite_text_content}")
            return prerequisite_text_content

        except TimeoutException:
            print(f"No prerequisites found for {course_code}")
            return None

    except Exception as e:
        logging.error(f"Error occurred while processing {course_code}: {e}")
        return None

if __name__ == "__main__":
    # Set Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enables headless mode
    chrome_options.add_argument("--disable-gpu")  # Disables GPU hardware acceleration
    chrome_options.add_argument("--window-size=1920x1080")  # Set window size for headless mode
    chrome_options.add_argument("--no-sandbox")  # Required for some environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents limited resource issues

    # Initialize the Chrome WebDriver with headless mode
    driver = webdriver.Chrome(options=chrome_options)

    # List of courses to scrape
    
    course_codes = [ "ARE 100A","ECS 017","ECS 032A","ECS 032B","MAT 021A","MAT 021B","MAT 021C","MAT 022A",
        "STA 035A","STA 035B","STA 035C","ECS 116","ECS 117","ECS 119","STA 108",
       "STA 141A","STA 131A","MAT 170","MAT 168","MAT 167","STS 101"
        
    ]
    #
    
    # CSV file for saving results
    output_file = r"C:\\Users\\PC4\\OneDrive\\Desktop\\reg classproject\\prereq.csv"

    # Clear the CSV file before writing new data (optional)
    if os.path.exists(output_file):
        os.remove(output_file)

    # Loop through each course, scrape prerequisites, and save them to CSV
    for course_code in course_codes:
        prereq_text = scrape_course_prerequisites(driver, course_code)
        if prereq_text:
            breakdown = break_down_prereq_text(prereq_text)
            save_breakdown_to_csv(breakdown, csv_filename=output_file, prereq=course_code)
            print(f"Prerequisites for {course_code} have been saved successfully.")
        else:
            prereq_text = ""
            breakdown = break_down_prereq_text(prereq_text)
            save_breakdown_to_csv(breakdown, csv_filename=output_file, prereq=course_code)

    # Close the browser after all courses have been processed
    driver.quit()
    print(f"All course prerequisites have been saved to {output_file}.")
