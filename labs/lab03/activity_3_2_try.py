from pymongo import MongoClient
import json
import sys

client = MongoClient("mongodb://localhost:27015/")
db = client["blogsystem"]

# Simulate a post with 10,000 embedded comments to show the size problem
big_comments = [{"author": f"User{i}", "text": "Sample comment text " * 5} for i in range(10000)]

sample_doc = {
    "title": "Popular Post",
    "author": "Mansoor",
    "content": "This post went viral...",
    "comments": big_comments
}

doc_size_bytes = sys.getsizeof(str(sample_doc))
print(f"Approximate document size with 10,000 embedded comments: {doc_size_bytes / (1024*1024):.2f} MB")
print("MongoDB's hard document size limit is 16 MB.\n")

explanation = """
Why embedding 10,000 comments is problematic:
1. Document size limit - MongoDB caps documents at 16MB. A post with
   10,000+ comments can easily exceed this as comments grow in length.
2. Write performance - every new comment requires rewriting/growing the
   entire parent document, causing expensive in-place update overhead
   and document relocation on disk.
3. Read overhead - fetching the post (e.g. just the title) always pulls
   all 10,000 comments too, wasting bandwidth and memory even when
   comments aren't needed.
4. No pagination - embedded arrays make "show 20 comments per page"
   awkward; you'd need $slice tricks instead of a simple query.

Alternative design - Referenced (hybrid) approach:
- Keep comments in a SEPARATE "comments" collection, referencing
  post_id (as already built in Activity 3.2's referenced design).
- Optionally embed only the latest 5-10 comments in the post document
  for fast preview, while the full list lives in the comments
  collection with pagination (skip/limit or cursor-based).
- Add an index on post_id in the comments collection for fast lookups.
- This is the "extended reference" / hybrid pattern - avoids the 16MB
  limit and keeps writes cheap regardless of comment volume.
"""
print(explanation)

with open("output.json", "w") as f:
    json.dump({
        "approx_size_mb": round(doc_size_bytes / (1024*1024), 2),
        "explanation": explanation.strip()
    }, f, indent=2)

print("Saved to output.json")