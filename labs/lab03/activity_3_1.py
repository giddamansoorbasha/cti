from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27015/")
db = client["university"]

# Drop collection if it exists (clean slate for repeated runs)
db.drop_collection("courses")

# Step 2: Add schema validation before inserting data
db.create_collection("courses", validator={
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["title", "code", "instructor", "schedule"],
        "properties": {
            "title": {"bsonType": "string"},
            "code": {"bsonType": "string", "pattern": "^[A-Z]{2,4}[0-9]{3}$"},
            "instructor": {"bsonType": "string"},
            "schedule": {
                "bsonType": "object",
                "required": ["days", "times", "room"],
                "properties": {
                    "days": {"bsonType": "array"},
                    "times": {"bsonType": "string"},
                    "room": {"bsonType": "string"}
                }
            }
        }
    }
})

courses = db["courses"]

# Step 1: Insert 3 course documents with embedded roster + schedule
courses.insert_many([
    {
        "title": "Database Systems",
        "code": "CS401",
        "instructor": "Dr. Sharma",
        "schedule": {"days": ["Monday", "Wednesday"], "times": "10:00-11:30", "room": "Room 101"},
        "roster": [
            {"name": "Ravi Kumar", "student_id": "S001", "grade": "A"},
            {"name": "Anjali Rao", "student_id": "S002", "grade": "B+"}
        ]
    },
    {
        "title": "Operating Systems",
        "code": "CS402",
        "instructor": "Dr. Sharma",
        "schedule": {"days": ["Tuesday", "Thursday"], "times": "09:00-10:30", "room": "Room 102"},
        "roster": [
            {"name": "Kiran Patel", "student_id": "S003", "grade": "A-"},
            {"name": "Ravi Kumar", "student_id": "S001", "grade": "B"}
        ]
    },
    {
        "title": "Computer Networks",
        "code": "CS403",
        "instructor": "Dr. Mehta",
        "schedule": {"days": ["Monday", "Friday"], "times": "13:00-14:30", "room": "Room 103"},
        "roster": [
            {"name": "Anjali Rao", "student_id": "S002", "grade": "A"},
            {"name": "Sneha Reddy", "student_id": "S004", "grade": "B"}
        ]
    }
])

print("3 course documents inserted.\n")

# Step 1: Query all courses that meet on Monday
print("Courses meeting on Monday:")
monday_courses = list(courses.find({"schedule.days": "Monday"}, {"_id": 0}))
for c in monday_courses:
    print(c)

# Step 3: Find all students enrolled in courses taught by a specific instructor
print("\nStudents enrolled in courses taught by Dr. Sharma:")
sharma_courses = courses.find({"instructor": "Dr. Sharma"}, {"_id": 0, "title": 1, "roster": 1})
students = []
for course in sharma_courses:
    for student in course["roster"]:
        print(f"{student['name']} (ID: {student['student_id']}) - Course: {course['title']}")
        students.append({**student, "course": course["title"]})

# Save output for submission
with open("output.json", "w") as f:
    json.dump({
        "monday_courses": monday_courses,
        "sharma_students": students
    }, f, indent=2)

print("\nSaved to output.json")