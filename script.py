import re, os
from selenium import webdriver

# Web Drivers
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Error Handling
from selenium.common.exceptions import NoSuchElementException

# Supress automatic console logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# CONSTANTS
URL = "https://canvas.ubc.ca/courses"
AUTH = {"username": "", "password": ""}
HTML_NAMES = {"courses_list_class": "course-list-table-row",
              "grades_element_class": "student_assignment",
              "grade_name": "title",
              "grade_mark": "tooltip"}
DRIVER = None

class Course:
    def __init__(self, name=None, link=None, grade=None, raw_grades=None):
        self.name = name
        self.link = link
        self.grade = grade
        self.raw_grades = raw_grades

class Grade:
    def __init__(self, name=None, category=None, points_achieved=None, points_total=None):
        self.name = name
        self.category = category
        self.points_achieved = points_achieved
        self.points_total = points_total

    @property
    def grade(self):
        if self.points_achieved is None or self.points_total is None:
            return None
        return round(self.points_achieved / self.points_total * 100, 2)
    
    def __str__(self):
        return f"Name: {self.name}, Grade: {self.grade}"

def main():
    AUTH["username"] = input("username: ")
    AUTH["password"] = input("password: ")

    global DRIVER
    DRIVER = webdriver.Chrome()
    DRIVER.get(URL)

    authenticate()
    courses_list = getCourses()

    for course in courses_list:
        course.raw_grades = getGrades(course)

    input("Press Enter to close...")

def authenticate():
    print(DRIVER)
    if DRIVER.current_url == URL:
        return
    DRIVER.find_element(By.ID, "username").send_keys(AUTH["username"])
    DRIVER.find_element(By.ID, "password").send_keys(AUTH["password"], Keys.RETURN)
    WebDriverWait(DRIVER, 10).until(EC.url_to_be(URL))
    wait()

def getCourses():
    courses_arr = DRIVER.find_elements(By.CLASS_NAME, HTML_NAMES["courses_list_class"])
    courses = []

    for item in courses_arr:
        course = Course()

        try:
            child = item.find_element(By.TAG_NAME, "a")
            course.name = child.get_attribute("title")
            course.link = child.get_attribute("href")

            if re.match(r".+ \d{3} .+", course.name):
                courses.append(course)
        except NoSuchElementException:
            pass
    
    return courses

def getGrades(course): # Return array of grades for given course
    current_url = DRIVER.current_url
    DRIVER.get(f'{course.link}/grades')

    grades = []

    elements = DRIVER.find_elements(By.CLASS_NAME, HTML_NAMES["grades_element_class"])

    for element in elements:
        grade = Grade()
        try:
            grade_description = element.find_element(By.CLASS_NAME, HTML_NAMES["grade_name"])
            grade.name = grade_description.find_element(By.TAG_NAME, "a").text
            grade.category = grade_description.find_element(By.TAG_NAME, "div").text

            grade_scores = element.find_element(By.CLASS_NAME, HTML_NAMES["grade_mark"]).find_elements(By.XPATH, "./span")

            print(f"{course}, {grade.name}")

            points_achieved_str = re.search(r"\d+(\.\d+)?", grade_scores[0].text)
            grade.points_achieved = float(points_achieved_str.group()) if points_achieved_str else None

            points_total_str = re.search(r"\d+(\.\d+)?", grade_scores[1].text)
            grade.points_total = float(points_total_str.group()) if points_total_str else None

            grades.append(grade)
        except NoSuchElementException:
            pass

    DRIVER.get(current_url)
    return grades

def wait(max_time=10): # Wait for page to load
    WebDriverWait(DRIVER, max_time).until(lambda driver_instance: driver_instance.execute_script("return document.readyState") == "complete")

if __name__ == "__main__":
    main()