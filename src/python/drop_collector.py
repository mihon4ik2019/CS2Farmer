import time
from typing import List
from .models import Account

class DropCollector:
    def __init__(self, db):
        self.db = db

    def collect_for_account(self, account: Account) -> int:
        time.sleep(2)
        return 1

    def collect_all(self, accounts: List[Account]) -> int:
        total = 0
        for acc in accounts:
            collected = self.collect_for_account(acc)
            total += collected
            acc.drop_today += collected
            acc.drop_week += collected
            acc.drop_month += collected
            acc.drop_total += collected
            self.db.update_account(acc)
        return total

    def get_stats(self) -> dict:
        accounts = self.db.get_accounts()
        today = sum(a.drop_today for a in accounts)
        week = sum(a.drop_week for a in accounts)
        month = sum(a.drop_month for a in accounts)
        total = sum(a.drop_total for a in accounts)
        return {
            "today": today,
            "week": week,
            "month": month,
            "total": total,
            "per_account": [{"username": a.username, "drop": a.drop_total} for a in accounts]
        }