from sharepoint_rest_api.libs.search_request import SearchRequest


class SearchRequestBuilder:
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

    def __init__(self, filters=None, select=None, source_id=None, start_row=None):
        self.filters = filters
        self.select = select
        self.source_id = source_id
        self.start_row = start_row

    def get_select_properties(self):
        if self.select:
            return {'results': self.select}

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
        return qry

    def build(self):
        qry = self.get_query()
        selected_properties = self.get_select_properties()
        return SearchRequest(
            qry,
            selected_properties=selected_properties,
            source_id=self.source_id,
            start_row=self.start_row
        )
