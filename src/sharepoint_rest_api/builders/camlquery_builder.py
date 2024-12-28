import logging

from office365.sharepoint.listitems.caml.query import CamlQuery
from office365.sharepoint.views.scope import ViewScope

from sharepoint_rest_api.utils import to_camel

logger = logging.getLogger(__name__)


def recursive_builder(queries, operator="And"):
    if queries:
        query = queries.pop()
        if len(queries) == 0:
            return query
        if len(queries) == 1:
            last_query = queries.pop()
            return f"<{operator}>" + query + last_query + f"</{operator}>"
        return f"<{operator}>" + query + recursive_builder(queries, operator) + f"</{operator}>"
    return ""


class CamlQueryBuilder:
    """Helper Class to create queries in CamlQuery format."""

    date_operators = ["Geq", "Gt", "Leq", "Lt"]
    mapping_operator = {
        "gte": "Geq",
        "gt": "Gt",
        "lte": "Leq",
        "lt": "Lt",
        "not": "Neq",
        "contains": "Contains",
        "eq": "Eq",
    }

    def __init__(self, filters=None, scope=None):
        super().__init__()
        self.scope = scope
        self.filters = {} if filters is None else filters

    def create_query(self):
        where_condition = ""

        if self.filters.keys():
            filter_queries = []
            for base_filter_name, filter_value in self.filters.items():
                querystring_operator = base_filter_name.split("__")[-1]
                operator = self.mapping_operator.get(querystring_operator, "Eq")

                filter_name = to_camel(base_filter_name.split("__")[0])
                if operator in self.date_operators:
                    column_type, value = "DateTime", f"{filter_value}T00:00:00Z"  # 2016-03-26
                    query = (
                        f'<{operator}><FieldRef Name="{filter_name}" />'
                        f'<Value Type="{column_type}">{value}</Value>'
                        f"</{operator}>"
                    )
                elif operator == "Contains":
                    column_type = "Text"
                    query = (
                        f'<{operator}><FieldRef Name="{filter_name}" />'
                        f'<Value Type="{column_type}">{filter_value}</Value>'
                        f"</{operator}>"
                    )
                else:
                    column_type, values = "Text", filter_value.split(",")
                    queries = [
                        (
                            f'<{operator}><FieldRef Name="{filter_name}" />'
                            f'<Value Type="{column_type}">{value}</Value>'
                            f"</{operator}>"
                        )
                        for value in values
                    ]
                    query = recursive_builder(queries, "Or")
                filter_queries.append(query)
            where_condition = recursive_builder(filter_queries)
            if len(filter_queries) > 1:
                where_condition = f"<And>{where_condition}</And>"

        scope = f' Scope="{self.scope}"' if self.scope else ""
        return f"<View{scope}><Query><Where>{where_condition}</Where></Query></View>"

    def get_query(self):
        return CamlQuery.parse(self.create_query(), ViewScope.RecursiveAll)
