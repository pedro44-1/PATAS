"""Reconcile issued FT invoices with the billing provider until they are paid.

Usage: python scripts/reconcile_invoices.py [--loop] [--interval SECONDS]
"""
import argparse
import logging
import time
from uuid import uuid4

import redis

from src.core.config import settings
from src.core.database import SessionLocal
from src.services.billing_reconciliation import reconcile_pending_invoices

LOCK_KEY = "patas:billing-reconcile:lock"
logger = logging.getLogger("patas.billing_reconcile")


def run_once() -> dict[str, int] | None:
    token = str(uuid4())
    client = redis.Redis.from_url(settings.REDIS_URL)
    lock_ttl = max(60, settings.BILLING_RECONCILE_INTERVAL_SECONDS)
    if not client.set(LOCK_KEY, token, nx=True, ex=lock_ttl):
        logger.info("reconciliation already running elsewhere; skipping")
        return None
    db = SessionLocal()
    try:
        result = reconcile_pending_invoices(db)
        logger.info("billing reconciliation %s", result)
        return result
    finally:
        db.close()
        if client.get(LOCK_KEY) == token.encode():
            client.delete(LOCK_KEY)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=settings.BILLING_RECONCILE_INTERVAL_SECONDS)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if not settings.BILLING_RECONCILE_ENABLED:
        logger.info("BILLING_RECONCILE_ENABLED is false; nothing to do")
        while args.loop:
            time.sleep(3600)
        return
    while True:
        run_once()
        if not args.loop:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
