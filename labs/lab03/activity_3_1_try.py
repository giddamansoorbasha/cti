from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27015/")
db = client["university"]
courses = db["courses"]

# Add a "prerequisites" field (embedded array of course codes) to existing courses
courses.update_one({"code": "CS402"}, {"$set": {"prerequisites": ["CS401"]}})
courses.update_one({"code": "CS403"}, {"$set": {"prerequisites": ["CS401", "CS402"]}})
courses.update_one({"code": "CS401"}, {"$set": {"prerequisites": []}})

print("Prerequisites added to courses.\n")

print("All courses with their prerequisites:")
result = list(courses.find({}, {"_id": 0, "title": 1, "code": 1, "prerequisites": 1}))
for c in result:
    print(c)

with open("output.json", "w") as f:
    json.dump(result, f, indent=2)

print("\nSaved to output.json")

print("""
Design justification:
Prerequisites are embedded as an array of course codes inside each
course document, not stored in a separate collection.

Reasons:
1. Prerequisites are small, fixed-size lists (rarely more than 2-4 courses)
   that don't grow unbounded - ideal for embedding.
2. They are almost always read together with the course itself
   (e.g. showing a course page with its requirements) - embedding avoids
   an extra $lookup/join on every read.
3. They rarely change independently of the course - low write frequency.
4. Referencing would be better only if prerequisite courses needed to be
   queried/updated independently at scale, or if a course could have
   hundreds of prerequisites - not the case here.
""")