from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27015/")
db = client["blogsystem"]

db.drop_collection("posts")
db.drop_collection("comments")
db.drop_collection("posts_embedded")

posts = db["posts"]
comments = db["comments"]

# Step 1: Insert 5 posts (referenced design)
post_ids = posts.insert_many([
    {"title": "Intro to MongoDB", "author": "Mansoor", "content": "MongoDB basics..."},
    {"title": "Embedding vs Referencing", "author": "Mansoor", "content": "Design patterns..."},
    {"title": "Aggregation Pipelines", "author": "Mansoor", "content": "Using $lookup..."},
    {"title": "Schema Validation", "author": "Mansoor", "content": "jsonSchema rules..."},
    {"title": "Indexes in MongoDB", "author": "Mansoor", "content": "Speeding up queries..."},
]).inserted_ids

print("5 posts inserted.")

# Step 1: Insert 10 comments referencing post_ids
comment_docs = []
for i in range(10):
    comment_docs.append({
        "post_id": post_ids[i % 5],
        "author": f"User{i+1}",
        "text": f"This is comment number {i+1}"
    })
comments.insert_many(comment_docs)
print("10 comments inserted.\n")

# Step 2: $lookup query - get a post with its comments in ONE query
print("Post with comments (using $lookup):")
pipeline = [
    {"$match": {"_id": post_ids[0]}},
    {"$lookup": {
        "from": "comments",
        "localField": "_id",
        "foreignField": "post_id",
        "as": "comments"
    }}
]
lookup_result = list(posts.aggregate(pipeline))
print(lookup_result)

# Step 3: Migrate to embedded design using aggregation pipeline
migrate_pipeline = [
    {"$lookup": {
        "from": "comments",
        "localField": "_id",
        "foreignField": "post_id",
        "as": "comments"
    }},
    {"$out": "posts_embedded"}
]
posts.aggregate(migrate_pipeline)
print("\nMigration complete. New collection: posts_embedded")

print("\nSample embedded document:")
embedded_sample = db["posts_embedded"].find_one({"_id": post_ids[0]})
print(embedded_sample)

# Step 4: Compare number of queries needed
print("""
Query count comparison to display a post with its comments:
- Referenced design : 2 queries (1 for post + 1 for comments)
                       OR 1 query if using $lookup aggregation
- Embedded design    : 1 query (single find() - comments already inside)

Embedded design always needs exactly 1 query regardless of $lookup use,
while referenced design needs 2 separate queries without aggregation.
""")

with open("output.json", "w") as f:
    json.dump({
        "lookup_result": lookup_result,
        "embedded_sample": embedded_sample
    }, f, default=str, indent=2)

print("Saved to output.json")