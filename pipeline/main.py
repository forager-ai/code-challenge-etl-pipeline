"""
Pipeline entry point.

Replace this stub with your implementation. Goal: read all person and
organization records from $DATA_DIR, join them, and load the merged result
into a single Elasticsearch index named `persons`, within the resource
limits set in docker-compose.yml.

Input shape (NDJSON, one document per line, despite the `.json.gz` extension):

    { "id": ..., "date_updated": "...", "serialized_data": { /* rich record */ } }

Target document shape (defend variations in EVALUATION.md):

    {
        "forager_id": ...,
        "first_name": ..., "last_name": ..., ...,    # top-level fields from serialized_data
        "roles": [
            {
                "role_title": "...", "organization_id": ..., "organization_name": ...,
                "organization_domain": "...", "organization_industry": "...", ...
            }
        ],
        "organizations": [
            # populated by joining roles[].organization_id against orgs feed
            { "forager_id": ..., "name": ..., "linkedin_id": ..., ... }
        ]
    }

You may rewrite this in any language. If you do, update the Dockerfile,
docker-compose.yml command, and requirements accordingly.
"""

import os
import sys

from elasticsearch import Elasticsearch


def main() -> int:
    es_url = os.environ["ES_URL"]
    data_dir = os.environ["DATA_DIR"]

    es = Elasticsearch(es_url, request_timeout=30)
    if not es.ping():
        print(f"could not reach elasticsearch at {es_url}", file=sys.stderr)
        return 1

    print(f"connected to elasticsearch {es.info()['version']['number']}")
    print(f"data dir: {data_dir}")
    for sub in ("person", "organization"):
        path = os.path.join(data_dir, sub)
        if os.path.isdir(path):
            files = sorted(os.listdir(path))
            print(f"  {sub}/: {len(files)} files (e.g. {files[:2]})")
        else:
            print(f"  {sub}/: missing — unzip the data bundle into ./data/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
