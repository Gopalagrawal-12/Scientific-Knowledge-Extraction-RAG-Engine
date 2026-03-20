import os
import json
from database import get_qdrant_client
from qdrant_client import models


def fix_my_qdrant():
    print("🚀 Connecting to Qdrant Cloud...")
    client = get_qdrant_client()
    collection_name = "research_buddy_docs"

    # 1. Create the Payload Index (The "Empty Return" Fix)
    print("🛠️ Creating Payload Index for 'metadata.user_id'...")
    client.create_payload_index(
        collection_name=collection_name,
        field_name="user_id",
        field_schema="keyword"
    )

    # 2. Debug: Peek at the data to see the REAL path
    print("🔍 Peeking at the latest data structure...")
    results, _ = client.scroll(
        collection_name=collection_name,
        limit=1,
        with_payload=True
    )

    if results:
        print("\n✅ FOUND DATA IN CLOUD:")
        print(json.dumps(results[0].payload, indent=2))

        # Check if our target field exists in the raw payload
        payload = results[0].payload
        if "metadata" in payload and "user_id" in payload["metadata"]:
            print(
                f"\n🎯 Confirmed: Your user_id is at 'metadata.user_id' and value is '{payload['metadata']['user_id']}'")
        else:
            print("\n⚠️ Warning: user_id NOT found at 'metadata.user_id'. Check the JSON above for the correct path.")
    else:
        print("\n❌ Collection is empty. Upload a paper first!")


if __name__ == "__main__":
    fix_my_qdrant()