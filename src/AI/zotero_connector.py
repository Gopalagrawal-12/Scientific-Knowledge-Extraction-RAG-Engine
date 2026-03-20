import os
from pyzotero import zotero
from dotenv import load_dotenv

load_dotenv()


class ZoteroSideSector:
    def __init__(self, library_id, api_key):
        # Library ID and API Key are passed per user to ensure segregation
        self.zot = zotero.Zotero(library_id, 'user', api_key)
    def get_organized_library(self)  :
        """Fetches items and organizes them by user-defined collections (folders)."""
        try:
            # 1. Get Collections to preserve user's organization
            collections = self.zot.collections()
            collection_map = {c['key']: c['data']['name'] for c in collections}

            # 2. Get Top Items (the actual papers/bookmarks)
            items = self.zot.top(limit=30)

            structured_sidebar = {}

            for item in items:
                data = item['data']
                # Extracting 'Inside Data' for the Side Sector
                entry = {
                    "title": data.get("title", "Untitled"),
                    "abstract": data.get("abstractNote", "No abstract available."),
                    "url": data.get("url"),
                    "tags": [t.get("tag") for t in data.get("tags", [])],
                    "date": data.get("date", "N/A"),
                    "key": item['key']
                }

                # Place in the correct folder or 'Uncategorized'
                col_keys = data.get("collections", [])
                col_name = collection_map.get(col_keys[0], "General") if col_keys else "General"

                if col_name not in structured_sidebar:
                    structured_sidebar[col_name] = []
                structured_sidebar[col_name].append(entry)

            return structured_sidebar
        except Exception as e:
            return {"error": str(e)}