import os
import csv
from multiprocessing import freeze_support
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import date

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


# ───────────────────────── Chrome Setup ─────────────────────────

def make_chrome_options():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--disable-sync")
    return opts


def create_driver(driver_path: str):
    return uc.Chrome(
        driver_executable_path=driver_path,
        options=make_chrome_options(),
        use_subprocess=False
    )


# ───────────────────────── Scraping Logic ─────────────────────────

def scrape_subject(subject_code: str, driver_path: str):
    driver = create_driver(driver_path)
    data = []

    try:
        driver.get("https://registrar-apps.ucdavis.edu/courses/search/index.cfm")

        Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "termCode"))
        )).select_by_value("202603")

        Select(driver.find_element(By.NAME, "subject")) \
            .select_by_value(subject_code)

        driver.execute_script(
            "arguments[0].click();",
            driver.find_element(By.NAME, "search")
        )

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table#mc_win tbody"))
        )

        rows = driver.find_elements(By.CSS_SELECTOR, "tr[bgcolor]")

        for row in rows:
            try:
                crn = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) strong").text.strip()
                if not crn.isdigit():
                    continue

                time_days = (
                    row.find_elements(By.CSS_SELECTOR, "td:nth-child(1) em") and
                    row.find_element(By.CSS_SELECTOR, "td:nth-child(1) em").text
                    or "N/A"
                )

                course = row.find_element(By.CSS_SELECTOR, "td:nth-child(2)") \
                    .text.split("\n")[0]

                section = row.find_element(By.CSS_SELECTOR, "td:nth-child(3)") \
                    .text.split("\n")[0]

                open_wait = (
                    row.find_elements(By.CSS_SELECTOR, "td:nth-child(3) em") and
                    row.find_element(By.CSS_SELECTOR, "td:nth-child(3) em").text
                    or "N/A"
                )

                instructor = (
                    row.find_element(By.CSS_SELECTOR, "td:nth-child(5)")
                       .text.split("\n")[0]
                       or "TBA"
                )

                data.append([
                    subject_code,
                    crn,
                    time_days,
                    course,
                    section,
                    open_wait,
                    instructor
                ])

            except Exception:
                continue

        return data

    finally:
        driver.quit()


# ───────────────────────── Helpers ─────────────────────────

def extract_open_count(text: str) -> int:
    try:
        for part in text.split("/"):
            if "Open" in part:
                return int(part.split(":")[1].strip())
    except Exception:
        pass
    return 0


def deduplicate_rows(rows):
    seen = set()
    deduped = []

    for row in rows:
        key = (row[1], row[3])  # (CRN, Course)
        if key not in seen:
            seen.add(key)
            deduped.append(row)

    return deduped


def aggregate_open_by_course(rows):
    course_open = defaultdict(int)
    for row in rows:
        course_open[row[3]] += extract_open_count(row[5])
    return course_open


def update_course_open_tracker(course_open, tracker_file):
    today = date.today().isoformat()
    existing = {}

    if os.path.exists(tracker_file):
        with open(tracker_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                existing[r["Course"]] = r

    updated = {}

    for course, total_open in course_open.items():
        if course not in existing:
            updated[course] = {
                "Course": course,
                "First Seen": today,
                "Total Open": total_open,
                "Days to Zero": 0 if total_open == 0 else ""
            }
        else:
            record = existing[course]
            record["Total Open"] = total_open

            if record["Days to Zero"] == "" and total_open == 0:
                first_seen = date.fromisoformat(record["First Seen"])
                record["Days to Zero"] = (date.today() - first_seen).days

            updated[course] = record

    with open(tracker_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Course", "First Seen", "Total Open", "Days to Zero"]
        )
        writer.writeheader()
        writer.writerows(updated.values())


# ───────────────────────── Main ─────────────────────────

def main():
    freeze_support()

    # unpack chromedriver once
    tmp = uc.Chrome(options=make_chrome_options(), use_subprocess=False)
    tmp.quit()

    driver_path = os.path.join(
        os.getenv("APPDATA"),
        "undetected_chromedriver",
        "undetected_chromedriver.exe"
    )

    save_dir = r"C:/Users/PC4/OneDrive/Desktop/reg classproject"
    os.makedirs(save_dir, exist_ok=True)

    courses_csv = os.path.join(save_dir, "all_courses.csv")
    tracker_csv = os.path.join(save_dir, "course_open_tracker.csv")

    subjects = ["ECL"]  # extend as needed

    with ThreadPoolExecutor(max_workers=5) as pool:
        batches = pool.map(
            lambda s: scrape_subject(s, driver_path),
            subjects
        )

    all_rows = []
    for batch in batches:
        if batch:
            all_rows.extend(batch)

    all_rows = deduplicate_rows(all_rows)

    # overwrite snapshot CSV
    with open(courses_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Subject",
            "CRN",
            "Time/Days",
            "Course",
            "Section",
            "Open/Reserved/Waitlist",
            "Instructor"
        ])
        writer.writerows(all_rows)

    course_open = aggregate_open_by_course(all_rows)
    update_course_open_tracker(course_open, tracker_csv)

    print(f"✅ Snapshot saved to {courses_csv}")
    print(f"📊 Course OPEN tracker updated: {tracker_csv}")


if __name__ == "__main__":
    main()
