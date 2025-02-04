import csv
import os
import time
import undetected_chromedriver as uc  # Prevents detection
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 🚀 Optimized Chrome Options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
chrome_options.add_argument("--disable-dev-shm-usage")  # Optimize memory use
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-background-networking")  # Speed boost
chrome_options.add_argument("--disable-sync")

# Initialize undetected ChromeDriver
driver = uc.Chrome(options=chrome_options)

# 📂 Setup CSV file
save_directory = r"C:/Users/PC4/OneDrive/Desktop/reg classproject"
os.makedirs(save_directory, exist_ok=True)
csv_filename = os.path.join(save_directory, f"all_courses_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv")

# 🎯 Subject List
option_values = ["AAS", "AMR", "AGC", "ARE", "AGE", "AED", "ASE", "AGR", "AMS", "ANB", "ABI", "ABG", 
    "ANG", "ANS", "ANT", "ABS", "ABT", "ARB", "AHI", "ART", "ASA", "AST", "ATM", "AVS", 
    "BCB", "BMB", "BIS", "BIO", "BPT", "BPH", "BST", "BIT", "DEB", "BAX", "CAN", "CDB", 
    "CEL", "CHE", "CHI", "CHN", "CTS", "CDM", "CLA", "CLH", "CGS", "LTS", "CLR", "CMN", 
    "CRD", "COM", "CNE", "CNS", "CRI", "CRO", "CSM", "CST", "DAN", "DSC", "DES", "DRA", 
    "EPS", "EAS", "ECL", "ECN", "EJS", "EDU", "EAP", "EDO", "EGG", "ENG", "EAE", "EAD", 
    "EAL", "EBS", "BIM", "ECH", "ECM", "ECI", "ECS", "EEC", "EMS", "EME", "MAE", "ENL", 
    "ENT", "ENH", "EVH", "ENP", "ENV", "ERS", "ESMC", "ESME", "ESM", "ESP", "EST", "ETX", 
    "EPI", "EVE", "EXB", "EXS", "FPS", "FMS", "LFA", "FAH", "FST", "FSM", "FOR", "FRE", 
    "FRS", "FSE", "GSW", "GGG", "GEO", "GEL", "GER", "GDB", "GLO", "GRD", "GRK", "MHI", "HEB",
      "HND", "HIN", "HIS", "HPS", "HNR", "HRT", "HDE", "HMR", "HUM", "HUN", "HYD", "IMM", "IPM",
        "IST", "IAD", "ICL", "IRE", "ITA", "JPN", "JST", "LED", "LDA", "LAT", "LAH", "LAW", "LIN", 
        "MGT", "MGV", "MGB", "MGP", "MPH", "MCN", "MPS", "MAT", "ANE", "BCM", "CHA", "CPS", "CMH", 
        "DER", "EPP", "FAP", "HPH", "IMD", "CAR", "NCM", "EMR", "ENM", "GAS", "GMD", "HON", "IDI", 
        "NEP", "PUL", "MMI", "PHA", "MDS", "NEU", "NSU", "OBG", "OEH", "OPT", "OSU", "OTO", "PMD", "PED", 
        "PMR", "PSU", "PSY", "SPH", "RON", "RDI", "RNU", "RAL", "SUR", "URO", "MDD", "MDI", "MST", "MIC", 
        "MMG", "MIB", "MSA", "MSC", "MCB", "MCP", "MUS", "NAS", "NAC", "NEM", "NPB", "NSC", "NRS", "NUT", "NGG",
          "NUB", "PFS", "PER", "PTX", "PHI", "PHE", "PAS", "PHY", "PGG", "PLB", "PBI", "PLP", "PPP", "PLS", "POL", 
          "POM", "PBG", "POR", "ACC", "PSC", "PUN", "RMT", "RST", "RUS", "VET", "STS", "SAS", "STP", "STH", "SOC", 
          "SSC", "SPA", "STA", "REL", "SAF", "SSB", "TCS", "TAE", "TXC", "TTP", "TRK", "UWP", "URD", "VCR", "DVM", "VMD", 
          "VEN", "APC", "VME", "VMB", "PMI", "PHR", "MPM", "VSR", "WFB", "WFC", "WMS", "WLD"]  # Use a subset for testing

# Function to scrape a subject
def scrape_subject(value):
    try:
        # Open website (only once)
        if driver.current_url != 'https://registrar-apps.ucdavis.edu/courses/search/index.cfm':
            driver.get('https://registrar-apps.ucdavis.edu/courses/search/index.cfm')

        # Select Term
        term_dropdown = driver.find_element(By.NAME, "termCode")
        Select(term_dropdown).select_by_value("202503")

        # Select Subject
        subject_dropdown = driver.find_element(By.NAME, "subject")
        Select(subject_dropdown).select_by_value(value)

        # Click Search Button
        search_button = driver.find_element(By.NAME, "search")
        driver.execute_script("arguments[0].click();", search_button)

        # Wait for results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table#mc_win tbody"))
        )

        # Extract Rows
        rows = driver.find_elements(By.CSS_SELECTOR, "tr[bgcolor]")
        results = []

        for row in rows:
            try:
                crn_td = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
                crn = crn_td.find_element(By.CSS_SELECTOR, "strong").text
                time_days = crn_td.find_element(By.CSS_SELECTOR, "em").text if crn_td.find_elements(By.CSS_SELECTOR, "em") else "N/A"

                course = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.split("\n")[0]
                section = row.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text.split("\n")[0]
                open_reserved_waitlist = row.find_element(By.CSS_SELECTOR, "td:nth-child(3) em").text if row.find_elements(By.CSS_SELECTOR, "td:nth-child(3) em") else "N/A"

                instructor_td = row.find_element(By.CSS_SELECTOR, "td:nth-child(5)")
                instructor = instructor_td.text.split("\n")[0] if instructor_td.text.strip() else "TBA"

                results.append([value, crn, time_days, course, section, open_reserved_waitlist, instructor])
            except:
                continue

        return results

    except Exception as e:
        print(f"Error processing subject {value}: {e}")
        return []

# Run subjects in parallel (adjust max_workers based on CPU)
with ThreadPoolExecutor(max_workers=5) as executor:
    all_results = executor.map(scrape_subject, option_values)

# Save to CSV
with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Subject", "CRN", "Time/Days", "Course", "Section", "Open/Reserved/Waitlist", "Instructor"])
    for result in all_results:
        writer.writerows(result)

print(f"✅ Data successfully saved to {csv_filename}")
driver.quit()
