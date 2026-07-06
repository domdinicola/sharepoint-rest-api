import hashlib
import json
import logging
import time
from urllib.parse import quote

import requests
from msal import ConfidentialClientApplication

from sharepoint_rest_api import config
from sharepoint_rest_api.builders.rest_builder import (
    GRAPH_SEARCH_URL,
    GRAPH_URL,
    RestBuilder,
)

logger = logging.getLogger(__name__)

_scan_cache = {}


def _get_scan_cache(key):
    entry = _scan_cache.get(key)
    if entry is not None and time.time() < entry["expires"]:
        return entry["value"]
    if entry is not None:
        del _scan_cache[key]
    return None


def _set_scan_cache(key, value, ttl=300):
    _scan_cache[key] = {"value": value, "expires": time.time() + ttl}
    if len(_scan_cache) > 500:
        now = time.time()
        stale = [k for k, v in _scan_cache.items() if now >= v["expires"]]
        for k in stale:
            del _scan_cache[k]


class GraphClientError(Exception):
    """Exception when using the Graph client."""


class GraphClient:
    """Client to access SharePoint content via Microsoft Graph API.

    Manages authentication via MSAL, provides GET/POST methods for HTTP
    communication, and delegates JSON query body construction to a
    RestBuilder instance.
    """

    def __init__(self, client_id=None, client_secret=None, tenant=None, **kwargs):
        self._client_id = client_id or config.GRAPH_CLIENT_ID
        self._client_secret = client_secret or config.GRAPH_CLIENT_SECRET
        self._tenant = tenant or config.GRAPH_TENANT
        self._app = None
        self._token = None
        self._site_id = None
        self._rest_builder = RestBuilder()
        self.folder = kwargs.get("folder", "Documents")

    # ---- Auth -----------------------------------------------------------------

    @property
    def _msal_app(self):
        if self._app is None:
            self._app = ConfidentialClientApplication(
                client_id=self._client_id,
                client_credential=self._client_secret,
                authority=f"https://login.microsoftonline.com/{self._tenant}",
            )
        return self._app

    @property
    def token(self):
        if self._token is None:
            result = self._msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            if "access_token" not in result:
                raise GraphClientError(
                    f"Could not acquire token: {result.get('error_description', result.get('error', 'Unknown error'))}"
                )
            self._token = result["access_token"]
        return self._token

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    # ---- HTTP -----------------------------------------------------------------

    def get(self, url, timeout=120):
        retries = config.GRAPH_API_RETRY_COUNT
        for attempt in range(retries + 1):
            try:
                response = requests.get(url, headers=self.headers, timeout=timeout)
                if response.status_code == 504 and attempt < retries:
                    logger.warning("Graph GET returned 504, retrying (%d/%d)", attempt + 1, retries)
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                raise GraphClientError(f"Graph GET request failed: {e}")
        raise GraphClientError("Graph GET request failed after all retries")

    def post(self, url, json=None, timeout=60):
        retries = config.GRAPH_API_RETRY_COUNT
        for attempt in range(retries + 1):
            try:
                response = requests.post(url, headers=self.headers, json=json, timeout=timeout)
                if response.status_code == 504 and attempt < retries:
                    logger.warning("Graph POST returned 504, retrying (%d/%d)", attempt + 1, retries)
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                raise GraphClientError(f"Graph POST request failed: {e}")
        raise GraphClientError("Graph POST request failed after all retries")

    # ---- Site ID --------------------------------------------------------------

    def _get_site_id(self):
        site = config.SHAREPOINT_SITE
        tenant = config.SHAREPOINT_TENANT.strip("/")
        site_type = config.SHAREPOINT_SITE_TYPE
        hostname = tenant.replace("https://", "").split("/")[0]
        url = f"{GRAPH_URL}/sites/{hostname}:/{site_type}/{site}"
        response = self.get(url)
        return response.json()["id"]

    @property
    def site_id(self):
        if self._site_id is None:
            self._site_id = self._get_site_id()
        return self._site_id

    # ---- Query / Response processing ------------------------------------------

    @staticmethod
    def _merge_batch_fields(container, responses):
        for br in responses:
            try:
                idx = int(br.get("id", 0))
            except ValueError, TypeError:
                continue
            if idx >= len(container):
                continue
            item, site_id, list_id, item_id = container[idx]
            if br.get("status", 0) != 200:
                continue
            body = br.get("body")
            if not isinstance(body, dict):
                continue
            fields = body.get("fields")
            if not isinstance(fields, dict):
                continue
            for k, v in fields.items():
                if k not in item:
                    item[k] = v

    def _fetch_item_fields(self, items_with_refs):
        """Fetch full listItem fields for search results via the list items API.

        Uses the Microsoft Graph batch endpoint to efficiently retrieve
        list item fields for items found by the search API.  The Graph API
        limits a single batch to 20 requests, so larger sets are chunked.
        """
        if not items_with_refs:
            return

        batch_requests = []
        for idx, (_item, site_id, list_id, item_id) in enumerate(items_with_refs):
            if not all([site_id, list_id, item_id]):
                continue
            try:
                encoded_site_id = quote(site_id, safe="")
            except TypeError:
                logger.warning("Failed to encode site_id: %s", site_id)
                continue
            batch_requests.append(
                {
                    "id": str(idx),
                    "method": "GET",
                    "url": f"/sites/{encoded_site_id}/lists/{list_id}/items/{item_id}?expand=fields",
                }
            )

        if not batch_requests:
            return

        batch_limit = 20  # Graph API $batch hard limit
        for chunk_start in range(0, len(batch_requests), batch_limit):
            chunk = batch_requests[chunk_start : chunk_start + batch_limit]
            for i, req in enumerate(chunk):
                req["id"] = str(i)
            batch_body = RestBuilder.build_batch_body(chunk)

            try:
                resp = self.post(f"{GRAPH_URL}/$batch", json=batch_body, timeout=120)
            except GraphClientError as e:
                logger.warning(
                    "Batch field fetch failed (items %d-%d): %s",
                    chunk_start,
                    chunk_start + len(chunk) - 1,
                    e,
                )
                continue

            chunk_container = items_with_refs[chunk_start : chunk_start + len(chunk)]
            self._merge_batch_fields(chunk_container, resp.json().get("responses", []))

    @staticmethod
    def _check_filter_op(operator_key, item_str, item_parts, expected_values):
        if operator_key == "eq":
            if not any(ev in item_parts or ev == item_str for ev in expected_values):
                return False
        elif operator_key == "not":
            if any(ev in item_parts or ev == item_str for ev in expected_values):
                return False
        elif operator_key == "contains":
            if not any(ev in item_str or any(ev in p for p in item_parts) for ev in expected_values):
                return False
        elif operator_key == "not_in" and any(ev in item_parts or ev == item_str for ev in expected_values):
            return False
        return True

    @staticmethod
    def _matches_post_filters(item, post_filters, reverse_map=None):
        """Check if an enriched item matches all post-filters.

        Comma-separated filter values are treated as OR (same as KQL).
        Semicolons in item values are treated as multi-value field separators.

        Args:
            item: Enriched item dict (already has listItem fields merged).
            post_filters: Dict of managed-property-name -> value to match.
            reverse_map: Optional dict of managed name -> serializer name
                         (e.g. {'DonorCode': 'DRPDonorCode'}).

        """
        for qs_filter_name, filter_value in post_filters.items():
            parts = qs_filter_name.split("__")
            raw_name = parts[0]
            operator_key = parts[-1] if len(parts) > 1 else "eq"
            is_exclusion = raw_name.startswith("-")
            clean_name = raw_name.lstrip("-")
            alt_name = (reverse_map or {}).get(clean_name, clean_name)

            item_val = item.get(clean_name)
            if item_val is None:
                item_val = item.get(alt_name)
            if item_val is None:
                if operator_key == "not":
                    continue
                return is_exclusion

            item_str = str(item_val).strip()
            expected_str = filter_value.strip()
            expected_values = [v.strip() for v in expected_str.split(",")]
            item_parts = [p.strip() for p in item_str.split(";")] if ";" in item_str else [item_str]

            if is_exclusion:
                if any(ev in item_parts or ev == item_str for ev in expected_values):
                    return False
                continue

            if not GraphClient._check_filter_op(operator_key, item_str, item_parts, expected_values):
                return False

        return True

    @staticmethod
    def _merge_list_item_fields(item, list_item):
        li_fields = list_item.get("fields", {})
        if not isinstance(li_fields, dict):
            return
        item["OriginalPath"] = li_fields.get("path", "")
        if li_fields.get("title"):
            item["Title"] = li_fields["title"]
        for k, v in li_fields.items():
            if k not in item:
                item[k] = v

    @staticmethod
    def _build_item_from_hit(hit):
        resource = hit.get("resource", {})
        web_url = resource.get("webUrl") or ""
        name = resource.get("name") or ""

        if not name and web_url:
            name = web_url.rstrip("/").rsplit("/", 1)[-1]

        item = {
            "Title": name,
            "Path": web_url,
            "DocId": resource.get("id", ""),
            "WorkId": hit.get("hitId", ""),
            "Rank": hit.get("rank", 0),
            "Size": resource.get("size", 0),
            "Write": resource.get("lastModifiedDateTime", ""),
            "LastModifiedTime": resource.get("lastModifiedDateTime", ""),
        }

        file_info = resource.get("file")
        if isinstance(file_info, dict):
            mime = file_info.get("mimeType", "")
            item["FileType"] = mime.split("/")[-1] if "/" in mime else mime

        created_by = resource.get("createdBy")
        if isinstance(created_by, dict):
            user = created_by.get("user", {})
            if isinstance(user, dict) and user.get("displayName"):
                item["Author"] = user["displayName"]

        list_item = resource.get("listItem")
        if isinstance(list_item, dict):
            GraphClient._merge_list_item_fields(item, list_item)

        if hit.get("summary"):
            item["HitHighlightedSummary"] = hit["summary"]

        return item

    @staticmethod
    def _extract_item_refs(resource):
        parent_ref = resource.get("parentReference")
        site_id = parent_ref.get("siteId") if isinstance(parent_ref, dict) else None
        sp_ids = parent_ref.get("sharepointIds") if isinstance(parent_ref, dict) else None
        list_id = sp_ids.get("listId") if isinstance(sp_ids, dict) else None
        list_item_id = sp_ids.get("listItemId") if isinstance(sp_ids, dict) else None
        if site_id and list_id and list_item_id:
            return site_id, list_id, list_item_id
        return None

    def _execute_search_page(self, kql, start_row, page_size, reverse_map=None):
        """Execute a single search API page and return (items, total_rows) from raw results.

        Args:
            kql: KQL query string.
            start_row: Zero-based row offset.
            page_size: Number of results to fetch.
            reverse_map: Optional dict of managed name -> serializer field name.

        """
        body = RestBuilder.build_search_request_body(kql, start_row, page_size)
        try:
            response = self.post(GRAPH_SEARCH_URL, json=body, timeout=60)
        except GraphClientError as e:
            raise GraphClientError(f"Graph Search API request failed: {e}")

        data = response.json()
        hits_container = data["value"][0]["hitsContainers"][0]
        total_rows = hits_container.get("total", 0)
        results = hits_container.get("hits", [])

        items = []
        items_with_refs = []

        for hit in results:
            item = GraphClient._build_item_from_hit(hit)
            items.append(item)

            refs = GraphClient._extract_item_refs(hit.get("resource", {}))
            if refs:
                items_with_refs.append((item, *refs))

        if items_with_refs:
            self._fetch_item_fields(items_with_refs)

        if reverse_map:
            for item in items:
                for managed_name, serializer_name in reverse_map.items():
                    if managed_name in item and serializer_name not in item:
                        item[serializer_name] = item[managed_name]

        return items, total_rows

    def _execute_paginated_search(self, kql, page, page_size, post_filters, reverse_map):
        if not post_filters:
            start_row = (page - 1) * page_size
            items, total_rows = self._execute_search_page(kql, start_row, page_size, reverse_map=reverse_map)
            logger.info(f"Graph Search API: {total_rows} total, returned {len(items)} for page {page}")
            return items, total_rows

        # Cache scan results in-process so every page sees the same pool
        # regardless of Django's cache backend.
        scan_key = hashlib.md5(
            json.dumps(
                {
                    "kql": kql,
                    "post_filters": dict(sorted(post_filters.items())),
                    "page_size": page_size,
                },
                sort_keys=True,
            ).encode(),
            usedforsecurity=False,
        ).hexdigest()

        all_items = _get_scan_cache(scan_key)
        if all_items is None:
            all_items = self._scan_all_post_filtered(kql, page_size, post_filters, reverse_map)
            _set_scan_cache(scan_key, all_items)

        total_rows = len(all_items)
        offset = (page - 1) * page_size
        items = all_items[offset : offset + page_size]

        logger.info(f"Graph Search API: {total_rows} total, returned {len(items)} for page {page}")
        return items, total_rows

    def _scan_all_post_filtered(self, kql, page_size, post_filters, reverse_map):
        """Scan ahead and return ALL post-filtered items (no page slicing)."""
        all_items = []
        max_scanned = 5

        for scan_offset in range(max_scanned):
            start_row = scan_offset * page_size
            page_items, page_total = self._execute_search_page(kql, start_row, page_size, reverse_map=reverse_map)

            page_items = [
                it for it in page_items if self._matches_post_filters(it, post_filters, reverse_map=reverse_map)
            ]
            all_items.extend(page_items)

            if page_total == 0:
                break
            if start_row + page_size >= page_total:
                break

        return all_items

    def search(
        self,
        search=None,
        filters=None,
        page=1,
        searchable_properties=None,
        **kwargs,
    ):
        """Search SharePoint content using the Microsoft Graph Search API.

        Uses the /search/query endpoint with KQL to find matching items
        across all document libraries. Returns (items, total_rows) matching
        the format existing serializers expect.

        Args:
            search: Optional free-text KQL search string (e.g. path exclusions).
            filters: Dict of managed-property-name -> value. The caller is
                     responsible for mapping URL param names to managed property
                     names before passing them in.
            page: 1-indexed page number.
            searchable_properties: Set of managed property names that are
                     searchable via KQL. Properties NOT in this set are
                     excluded from KQL and applied as post-filters after batch
                     enrichment. If None, all properties are treated as post-filters.
            **kwargs: Extra keyword arguments for API compatibility.
                      Accepted kwargs:
                      - reverse_map: Dict mapping managed property names ->
                        serializer field names for enrichment reverse-mapping.
                      - page_size: Number of items per page. Defaults to
                        config.GRAPH_PAGE_SIZE.

        """
        reverse_map = kwargs.pop("reverse_map", None)
        page_size = kwargs.pop("page_size", None) or config.GRAPH_PAGE_SIZE
        searchable_filters = {}
        post_filters = {}
        if filters:
            for name, value in filters.items():
                raw_name = name.split("__")[0].lstrip("-")
                if searchable_properties and raw_name in searchable_properties:
                    searchable_filters[name] = value
                else:
                    post_filters[name] = value

        kql = RestBuilder.build_kql(search=search, filters=searchable_filters)
        return self._execute_paginated_search(kql, page, page_size, post_filters, reverse_map)

    def read_list_items(self, list_name):
        """Read all items from a SharePoint list via Graph API.

        Uses pagination to fetch all items from the specified list.
        Returns a list of item dicts (including expanded field values).

        Args:
            list_name: Display name of the SharePoint list.

        """
        items = []
        site_path = quote(self.site_id, safe="")
        list_path = quote(list_name, safe="")
        url = f"{GRAPH_URL}/sites/{site_path}/lists/{list_path}/items?expand=fields&$top=500"
        while url:
            response = self.get(url)
            data = response.json()
            items.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
        return items
