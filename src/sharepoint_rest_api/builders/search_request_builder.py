from office365.sharepoint.search.query.sort import Sort
from office365.sharepoint.search.search_request import SearchRequest

from sharepoint_rest_api import config
from sharepoint_rest_api.utils import to_camel


class SearchRequestBuilder:
    """Helper class to build queries in Keyword Query Language (KQL)"""
    filters = {}
    select = None

    mapping_operator = {
        'gte': '>=',
        'gt': '>',
        'lte': '<=',
        'lt': '<',
        'not': '<>',
        'eq': ':',
        'between': '..',
        'contains': '*'
    }

    def __init__(self, search=None, filters=None, select=None, order_by=None, source_id=None, start_row=None):
        self.search = search
        self.filters = filters
        self.select = select
        self.order_by = order_by
        self.source_id = source_id
        self.start_row = start_row

    def get_select_properties(self):
        if self.select:
            return self.select

    def get_order_by(self):
        if self.order_by:
            order = to_camel(self.order_by).split(',')
            return [Sort(item[1:], 1) if item.startswith('-') else Sort(item, 0) for item in order]

    def get_query(self):
        filter_queries = []
        if self.filters.keys():
            filter_queries = []
            for qs_filter_name, filter_value in self.filters.items():
                filter_name = qs_filter_name.split('__')[0]
                querystring_operator = qs_filter_name.split('__')[-1]
                operator = self.mapping_operator.get(querystring_operator, ':')
                if operator == '..':
                    filter_value_from, filter_value_to = filter_value.split('__')
                    query = '{}:{}{}{}'.format(filter_name, filter_value_from, operator, filter_value_to)
                elif operator == "*":
                    query = '{}:"{}{}"'.format(filter_name, filter_value, operator)
                else:
                    values = filter_value.split(',')
                    if len(values) == 1:
                        filter_values = f'\"{values[0]}\"'
                    else:
                        filter_values = "(" + " OR ".join(['\"{}\"'.format(value) for value in values]) + ')'
                    query = '{}{}{}'.format(filter_name, operator, filter_values)
                filter_queries.append(query)
        if not filter_queries:
            return '*'
        qry = ' AND '.join('{}'.format(query) for query in filter_queries)
        return f'{self.search} {qry}' if self.search else qry

    def build(self):
        return SearchRequest(
            self.get_query(),
            sort_list=self.get_order_by(),
            select_properties=self.get_select_properties(),
            start_row=self.start_row,
            row_limit=config.SHAREPOINT_PAGE_SIZE,
            trim_duplicates=False,
            SourceId=self.source_id,
            # source_id=self.source_id,
        )
