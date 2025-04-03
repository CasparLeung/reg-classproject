#reg-classproject
Academic Plan Builder:
  A tool to help students plan their academic schedule based on course prerequisites and seat availability.



Here's a GitHub README.md tailored for your Academic Plan project:

Academic Plan Builder
A tool to help students plan their academic schedule based on course prerequisites and seat availability.

Introduction
The Academic Plan Builder helps students create an optimized course schedule by:
1.  Tracking seat availability for classes.
2.  Extracting prerequisite information for each course.
3.  Storing and structuring prerequisite data.
4.  Ordering classes in a way that satisfies prerequisites.

This project web scrapes data from:
UC Davis Course Search (https://registrar-apps.ucdavis.edu/courses/overUse.html)(for seat availability)
UC Davis Course Catalog (https://catalog.ucdavis.edu/course-search/)(for prerequisites)

Project Structure

├──  Web Scraping Form Submit(1).py → Tracks remaining seats via web scraping
├──  find_class_prereq.py → Extracts course prerequisites from catalog
├──  prereq_alg.py → Formats prerequisites into a structured CSV
└──  class_algorithmn.py → Arranges class order based on prerequisites
