from pymongo import MongoClient
from pymongo.errors import OperationFailure

admin = MongoClient("mongodb://admin:admin123@localhost:27200/?authSource=admin", serverSelectionTimeoutMS=5000)
d = admin["cti_auth"]

for cmd, n in [
    ("dropUser", "app_user_read"), ("dropUser", "app_user_write"), ("dropUser", "hr_user"),
    ("dropRole", "reader_role"), ("dropRole", "writer_role"), ("dropRole", "hr_role"),
]:
    try:
        d.command(cmd, n)
    except OperationFailure:
        pass

for c in ("staff_public", "staff", "threats"):
    d.drop_collection(c)

d.threats.insert_one({"title": "demo threat"})
d.staff.insert_many([{"name": "Asha", "salary": 90000}, {"name": "Ravi", "salary": 80000}])
d.command("create", "staff_public", viewOn="staff", pipeline=[{"$project": {"salary": 0}}])


def res(coll, *actions):
    return {"resource": {"db": "cti_auth", "collection": coll}, "actions": list(actions)}


d.command("createRole", "reader_role", privileges=[res("threats", "find"), res("staff_public", "find")], roles=[])
d.command("createRole", "writer_role", privileges=[res("threats", "find", "insert", "update", "remove")], roles=[])
d.command("createRole", "hr_role", privileges=[res("staff", "find")], roles=[])
d.command("createUser", "app_user_read", pwd="read123", roles=["reader_role"])
d.command("createUser", "app_user_write", pwd="write123", roles=["writer_role"])
d.command("createUser", "hr_user", pwd="hr123", roles=["hr_role"])


def as_user(u, p):
    return MongoClient(f"mongodb://{u}:{p}@localhost:27200/?authSource=cti_auth", serverSelectionTimeoutMS=5000)["cti_auth"]


def attempt(label, fn):
    try:
        out = fn()
        extra = f" | {out}" if out is not None else ""
        print(f"  ALLOWED | {label}{extra}")
    except OperationFailure:
        print(f"  DENIED  | {label}")


r = as_user("app_user_read", "read123")
w = as_user("app_user_write", "write123")
h = as_user("hr_user", "hr123")

print("[1] app_user_read (reader_role)")
attempt("find threats", lambda: len(list(r.threats.find())))
attempt("find staff_public (redacted)", lambda: list(r.staff_public.find({}, {"_id": 0})))
attempt("find staff (with salary)", lambda: list(r.staff.find()))
attempt("insert threats", lambda: r.threats.insert_one({"x": 1}))

print("\n[2] app_user_write (writer_role)")
attempt("insert threats", lambda: bool(w.threats.insert_one({"x": 1}).inserted_id))
attempt("find staff", lambda: list(w.staff.find()))

print("\n[3] hr_user (hr_role)")
attempt("find staff (with salary)", lambda: list(h.staff.find({}, {"_id": 0})))