import time
from pymongo.errors import PyMongoError
from helpers import client, db

accounts, history = db.accounts, db.transfer_history


def reset():
    accounts.drop()
    history.drop()
    accounts.insert_many([
        {"account_id": "A", "balance": 500, "version": 0},
        {"account_id": "B", "balance": 200, "version": 0},
    ])


def show(label):
    bal = {a["account_id"]: a["balance"] for a in accounts.find()}
    print(f"  {label:<34} | {bal}")


def transfer(src, dst, amount):
    for attempt in range(5):
        try:
            with client.start_session() as s:
                with s.start_transaction():
                    r = accounts.update_one(
                        {"account_id": src, "balance": {"$gte": amount}},
                        {"$inc": {"balance": -amount, "version": 1}},
                        session=s,
                    )
                    if r.modified_count == 0:
                        raise ValueError("insufficient funds")
                    accounts.update_one(
                        {"account_id": dst},
                        {"$inc": {"balance": amount, "version": 1}},
                        session=s,
                    )
                    history.insert_one({"from": src, "to": dst, "amount": amount}, session=s)
            return
        except PyMongoError as e:
            if e.has_error_label("TransientTransactionError"):
                time.sleep(0.1 * 2 ** attempt)
                continue
            raise


reset()
show("start")
transfer("A", "B", 100)
show("after A->B 100")

try:
    transfer("A", "B", 1000)
except ValueError as e:
    print(f"  rejected                           | {e}")

show("after failed transfer (rollback)")
print(f"  history_rows={history.count_documents({})} (expected=1)")