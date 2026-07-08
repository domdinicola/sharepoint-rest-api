import logging

from sharepoint_rest_api import config

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SEARCH_URL = "https://graph.microsoft.com/v1.0/search/query"
GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]


class RestBuilderError(Exception):
    """Exception when communicating with the Graph API."""


class RestBuilder:
    """Builds JSON request bodies for Microsoft Graph API queries.

    Provides static methods to construct Graph API request payloads,
    including KQL query strings and structured JSON bodies for the
    search and batch endpoints.  Does not perform any HTTP calls.
    """

    @staticmethod
    def build_kql_clause(qs_filter_name, filter_value):
        """Build a single KQL clause from a filter expression."""
        parts = qs_filter_name.split("__")
        raw_name = parts[0]
        operator_key = parts[-1] if len(parts) > 1 else "eq"

        kql_op_map = {
            "not": "<>",
            "contains": ":",
            "eq": ":",
            "gte": ">=",
            "gt": ">",
            "lte": "<=",
            "lt": "<",
            "between": ":",
        }
        kql_op = kql_op_map.get(operator_key, ":")
        values = [v.strip() for v in filter_value.split(",")]

        if operator_key == "not_in":
            result = [f'-"{v}"' for v in values]
        elif operator_key == "contains":
            result = [f'{raw_name}:"{values[0]}*"']
        elif kql_op == "<>":
            result = [f'-{raw_name}:"{values[0]}"']
        elif operator_key in ("gte", "gt", "lte", "lt"):
            result = [f"{raw_name}{kql_op}{values[0]}"]
        elif operator_key == "between":
            range_parts = filter_value.split("__")
            result = [f"{raw_name}:{range_parts[0]}..{range_parts[-1]}"]
        elif len(values) == 1:
            result = [f'{raw_name}:"{values[0]}"']
        else:
            or_parts = [f'"{v}"' for v in values]
            result = [f"{raw_name}:({' OR '.join(or_parts)})"]
        return result

    @staticmethod
    def build_kql(search=None, filters=None):
        """Build a KQL query string from already-mapped managed property names.

        Filters dict keys are managed property names (mapped by caller).
        Supports DRF-style operators (__not, __contains) and multi-value.
        """
        if filters is None:
            filters = {}

        clauses = []
        for qs_filter_name, filter_value in filters.items():
            clauses.extend(RestBuilder.build_kql_clause(qs_filter_name, filter_value))

        if not clauses:
            return search or "*"
        if search:
            return f"{search} {' '.join(clauses)}"
        return " ".join(clauses)

    @staticmethod
    def build_search_request_body(kql, start_row, page_size, fields=None):
        """Build the JSON POST body for a Graph Search API request.

        Args:
            kql: KQL query string.
            start_row: Zero-based row offset.
            page_size: Number of results to fetch.
            fields: Optional list of managed property names to include
                    in search results for each hit. If omitted, only
                    default resource properties are returned.

        """
        request_body = {
            "entityTypes": ["driveItem"],
            "query": {"queryString": kql},
            "region": config.GRAPH_REGION,
            "from": start_row,
            "size": page_size,
        }
        if fields:
            request_body["fields"] = fields
        return {"requests": [request_body]}

    @staticmethod
    def build_batch_body(requests):
        """Build the JSON POST body for a Graph batch request."""
        return {"requests": requests[:20]}
