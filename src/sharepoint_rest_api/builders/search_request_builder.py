from office365.sharepoint.search.query.sort.sort import Sort

from sharepoint_rest_api import config
from sharepoint_rest_api.utils import to_camel


class SearchRequestBuilder:
    """Helper class to build queries in Keyword Query Language (KQL)."""

    select = None

    mapping_operator = {
        "gte": ">=",
        "gt": ">",
        "lte": "<=",
        "lt": "<",
        "not": "<>",
        "not_in": ":",
        "eq": ":",
        "between": "..",
        "contains": "*",
    }

    def __init__(self, search=None, filters=None, select=None, order_by=None, source_id=None, start_row=None):  # noqa
        self.search = search
        self.filters = {} if filters is None else filters
        self.select = select
        self.order_by = order_by
        self.source_id = source_id
        self.start_row = start_row

    def get_select_properties(self):
        return self.select

    def get_order_by(self):
        if self.order_by:
            order = to_camel(self.order_by).split(",")
            return [Sort(item[1:], 1) if item.startswith("-") else Sort(item, 0) for item in order]
        return None

    def get_query(self):
        filter_queries = []
        if self.filters.keys():
            filter_queries = []
            for qs_filter_name, filter_value in self.filters.items():
                filter_name = qs_filter_name.split("__")[0]
                querystring_operator = qs_filter_name.split("__")[-1]
                operator = self.mapping_operator.get(querystring_operator, ":")
                if operator == "..":
                    filter_value_from, filter_value_to = filter_value.split("__")
                    query = f"{filter_name}:{filter_value_from}{operator}{filter_value_to}"
                elif operator == "*":
                    query = f'{filter_name}:"{filter_value}{operator}"'
                else:
                    values = filter_value.split(",")
                    if querystring_operator == "not_in":
                        filter_values = "(" + " ".join([f'-"{value}"' for value in values]) + ")"
                    elif len(values) == 1:
                        filter_values = f'"{values[0]}"'
                    else:
                        filter_values = "(" + " OR ".join([f'"{value}"' for value in values]) + ")"
                    query = f"{filter_name}{operator}{filter_values}"
                filter_queries.append(query)
        if not filter_queries:
            return f"{self.search}" if self.search else "*"
        qry = " AND ".join(f"{query}" for query in filter_queries)
        return f"{self.search} {qry}" if self.search else qry

    def build(self):
        return {
            "query_text": self.get_query(),
            "sort_list": self.get_order_by(),
            "select_properties": self.get_select_properties(),
            "start_row": self.start_row,
            "row_limit": config.SHAREPOINT_PAGE_SIZE,
            "trim_duplicates": False,
            "SourceId": self.source_id,
        }
