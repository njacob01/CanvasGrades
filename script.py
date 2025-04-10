import re, os, csv
from dotenv import load_dotenv
from selenium import webdriver

# Web Drivers
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Error Handling
from selenium.common.exceptions import NoSuchElementException

# CONSTANTS
load_dotenv()
URL = "https://canvas.ubc.ca/courses"
AUTH = {"username": os.getenv("CANVAS_USERNAME"), "password": os.getenv("CANVAS_PASSWORD")}
HTML_NAMES = {"courses_list_class": "course-list-table-row",
              "grades_element_class": "student_assignment",
              "grade_description": "title",
              "grade_score": "grade"}
DRIVER = None

class Course:
    def __init__(self, name=None, code=None, subject=None, link=None, grade=None, all_grades=None):
        self.name = name
        self.code = code
        self.subject = subject
        self.link = link
        self.grade = grade
        self.all_grades = all_grades
    
    def __str__(self):
        return f"Name: {self.name}, All Grades: {self.all_grades}, Final Grade: {self.grade}"
    
    def __repr__(self):
        return f"Course({self.__str__()})"
    
    def asList(self):
        return [self.name, self.code, self.subject, self.link, self.grade, self.all_grades]

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
    
    def __repr__(self):
        return f"Grade({self.__str__()})"

def main():
    global DRIVER
    DRIVER = webdriver.Chrome()
    DRIVER.get(URL)

    authenticate()
    courses_list = getCourses()

    for course in courses_list:
        course.all_grades = getGrades(course)
    
    with open("test.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(course.asList() for course in courses_list)

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
            grade_description = element.find_element(By.CLASS_NAME, HTML_NAMES["grade_description"])
            grade.name = grade_description.find_element(By.TAG_NAME, "a").text
            grade.category = grade_description.find_element(By.TAG_NAME, "div").text

            grade_score = element.find_element(By.CLASS_NAME, HTML_NAMES["grade_score"])

            if grade_score.text and isNumber(grade_score.text):
                if '%' in grade_score.text:
                    grade.points_achieved = float(grade_score.text.strip()[:-1])
                    grade.points_total = float(100)
                else:
                    grade.points_achieved = float(grade_score.text.strip())
                    grade.points_total = float(element.find_element(By.XPATH, "following-sibling::*[1]").text.strip()[2:])

            grades.append(grade)
        except NoSuchElementException:
            pass

    DRIVER.get(current_url)
    return grades

def wait(max_time=10): # Wait for page to load
    WebDriverWait(DRIVER, max_time).until(lambda driver_instance: driver_instance.execute_script("return document.readyState") == "complete")

def isNumber(str):
    return re.match(r"\d+(\.\d+)?%?", str.strip())

if __name__ == "__main__":
    main()