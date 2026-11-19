from pymongo import MongoClient
import re
import json

client = MongoClient("mongodb://localhost:27015/")
db = client["inventory"]
products = db["products"]

def search_products(term):
    safe_term = re.escape(term)  # prevents OperationFailure on bad input like "(pack"
    return list(products.find(
        {"name": {"$regex": safe_term, "$options": "i"}},
        {"_id": 0}
    ))

# Case-insensitive search demo
print("Search 'wireless' (lowercase):")
for p in search_products("wireless"):
    print(p)

print("\nSearch 'COTTON' (uppercase, still matches 'Cotton'):")
for p in search_products("COTTON"):
    print(p)

# Demonstrate re.escape() protecting against invalid regex input
print("\nSearch with special character input '(pack' - handled safely:")
for p in search_products("(pack"):
    print(p)
print("(no crash - re.escape() treated '(' as a literal character)")

# Check index usage with explain()
products.create_index("name")
plan = products.find({"name": {"$regex": re.escape("wireless"), "$options": "i"}}).explain()
winning_stage = plan["queryPlanner"]["winningPlan"]
print("\nWinning plan stage:", winning_stage.get("stage"))
print("Index bounds used:", winning_stage.get("inputStage", {}).get("indexBounds"))

print("""
Note on index efficiency:
A case-insensitive regex like /wireless/i cannot use a tight index range -
its bounds are ["", {}), meaning it walks the entire index even though the
stage name still says IXSCAN. Anchoring (/^wireless/i) doesn't fix this
either. For real indexed case-insensitive search at scale, MongoDB text
indexes (or a collation with strength:2) should be used instead of regex.
""")

with open(r"lab04/output1.json", "a") as f:
    json.dump({
        "wireless_results": search_products("wireless"),
        "index_bounds": str(winning_stage.get("inputStage", {}).get("indexBounds"))
    }, f, indent=2)

print("Saved to output.json")