#!/usr/bin/env python3
"""
Correctness tests for the take-home pipeline.

Run AFTER `docker compose up` completes the ingest:

    python3 bench/correctness.py

The script reads expected values from bench/expected.json and runs three
queries against Elasticsearch:

  1. Total person document count
  2. Persons who have held a specific role title
     (term query on roles.role_title.keyword)
  3. Persons who have worked at a specific organization
     (term query on organizations.name.keyword)

Exits 0 if all pass, non-zero on any failure. No pip-install required;
uses only the Python standard library.

Configuration via environment variables:
  ES_URL      Elasticsearch base URL          (default: http://localhost:9200)
  INDEX_NAME  Override the index name to test (default: from expected.json)
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ES_URL = os.environ.get("ES_URL", "http://localhost:9200").rstrip("/")
EXPECTED_PATH = Path(__file__).parent / "expected.json"


def es_count(index: str, query: dict) -> int:
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        f"{ES_URL}/{index}/_count",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["count"]


def check(name: str, actual: int, expected: int) -> bool:
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: got {actual:,}, expected {expected:,}")
    return ok


def main() -> int:
    if not EXPECTED_PATH.exists():
        print(f"missing {EXPECTED_PATH}", file=sys.stderr)
        return 2

    expected = json.loads(EXPECTED_PATH.read_text())
    index = os.environ.get("INDEX_NAME", expected["index_name"])

    print(f"running correctness tests against {ES_URL}/{index}\n")

    failures = 0
    try:
        # 1. total person count
        actual = es_count(index, {"match_all": {}})
        if not check("total person count", actual, expected["total_persons"]):
            failures += 1

        # 2. persons with a specific role title
        t2 = expected["persons_with_role_title"]
        actual = es_count(index, {"term": {"roles.role_title.keyword": t2["role_title"]}})
        if not check(
            f'persons who have held role title "{t2["role_title"]}"',
            actual,
            t2["count"],
        ):
            failures += 1

        # 3. persons who worked at a specific organization (by name)
        t3 = expected["persons_at_organization"]
        actual = es_count(index, {"term": {"organizations.name.keyword": t3["name"]}})
        if not check(
            f'persons who worked at "{t3["name"]}"',
            actual,
            t3["count"],
        ):
            failures += 1
    except urllib.error.URLError as e:
        print(f"\nelasticsearch request failed: {e}", file=sys.stderr)
        return 2

    print()
    if failures == 0:
        print("all tests passed.")
        return 0
    print(f"{failures} test(s) failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
