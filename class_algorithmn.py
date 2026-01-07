import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

def load_data(csv_path):
    data = pd.read_csv(csv_path)
    data.fillna("N/A", inplace=True)  # Normalize N/A values
    return data

def build_prerequisite_mappings(data):
    prereq_dict = defaultdict(lambda: {"groups": defaultdict(set), "related_groups": {}})
    dependent_courses = defaultdict(set)
    course_dependencies = defaultdict(set)
    
    for index, row in data.iterrows():
        course = row['course']
        prereq = row['prereq']
        group = row['group']
        condition = row['condition']
        related_group = row['related_group']
        
        if group == "N/A" and course == prereq:
            prereq_dict[course]["no_prereq"] = True
            continue
        
        prereq_dict[prereq]["groups"][group].add(course)
        
        if related_group != "N/A":
            prereq_dict[prereq]["related_groups"][group] = related_group
        
        dependent_courses[course].add(prereq)
        course_dependencies[prereq].add(course)
    
    return prereq_dict, dependent_courses, course_dependencies

def resolve_related_groups(prereq_dict):
    for prereq, data in prereq_dict.items():
        related_groups = data["related_groups"]
        for group, rel_group in related_groups.items():
            if rel_group in data["groups"]:
                data["groups"][group] |= data["groups"].get(rel_group, set())

def generate_schedule(prereq_dict, dependent_courses, course_dependencies):
    resolve_related_groups(prereq_dict)
    all_courses = set(prereq_dict.keys())
    available_courses = {course for course in all_courses if "no_prereq" in prereq_dict[course]}
    
    print("Identified Courses with No Prerequisites:", available_courses)
    
    schedule = []
    scheduled_courses = set()
    remaining_courses = set(prereq_dict.keys()) - available_courses
    course_term_mapping = {}
    
    while available_courses or remaining_courses:
        current_term_courses = sorted(available_courses)
        if not current_term_courses and remaining_courses:
            print("Warning: Some courses have unresolved prerequisites:", remaining_courses)
            schedule.append(sorted(remaining_courses))  # Append remaining courses to subsequent terms
            remaining_courses.clear()
            break  # Prevent infinite loop
        
        term_index = len(schedule)
        schedule.append(current_term_courses)
        for course in current_term_courses:
            course_term_mapping[course] = term_index
        
        scheduled_courses.update(current_term_courses)
        available_courses.clear()
        
        newly_available_courses = set()
        for course in current_term_courses:
            if course in course_dependencies:
                for dependent in course_dependencies[course]:
                    if dependent in prereq_dict:
                        for group in list(prereq_dict[dependent]["groups"]):
                            prereq_dict[dependent]["groups"][group].discard(course)
                        
                        prereq_dict[dependent]["groups"] = {
                            g: c for g, c in prereq_dict[dependent]["groups"].items() if c
                        }
                        
                        if not prereq_dict[dependent]["groups"] and dependent not in scheduled_courses:
                            # Ensure prerequisite courses are scheduled first
                            max_prereq_term = max(
                                (course_term_mapping.get(prereq, -1) for prereq in dependent_courses[dependent]),
                                default=-1
                            )
                            
                            if max_prereq_term + 1 >= len(schedule):
                                schedule.append([])
                            schedule[max_prereq_term + 1].append(dependent)
                            course_term_mapping[dependent] = max_prereq_term + 1
                            newly_available_courses.add(dependent)
                            remaining_courses.discard(dependent)
        
        available_courses.update(newly_available_courses)
    
    return schedule

def visualize_schedule(schedule):
    if schedule:
        plt.figure(figsize=(12, 8))
        all_courses = []
        term_labels = []
        
        for term, courses in enumerate(schedule, start=1):
            for course in courses:
                all_courses.append(course)
                term_labels.append(term)
        
        if all_courses:
            y_positions = range(len(all_courses))
            plt.barh(y_positions, term_labels, tick_label=all_courses)
            
            plt.xlabel("Term")
            plt.ylabel("Courses")
            plt.title("Course Schedule Visualization")
            plt.gca().invert_yaxis()
            plt.show()
        else:
            print("No courses available to visualize.")
    else:
        print("No courses scheduled. Check prerequisite structure.")

if __name__ == "__main__":
    csv_path = 'C:/Users/PC4/OneDrive/Desktop/reg classproject/prereq.csv'
    data = load_data(csv_path)
    prereq_dict, dependent_courses, course_dependencies = build_prerequisite_mappings(data)
    schedule = generate_schedule(prereq_dict, dependent_courses, course_dependencies)
    
    print("\nSchedule of courses to take each term:")
    if schedule:
        for term, courses in enumerate(schedule, start=1):
            print(f"Term {term}: {', '.join(courses)}")
        visualize_schedule(schedule)
    else:
        print("No valid schedule could be generated. Check prerequisites for cycles or errors.")
