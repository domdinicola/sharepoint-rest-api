from office365.sharepoint.caml.utils import to_camel


class SearchRequestBuilder:
    filters = {}

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

    def __init__(self, filters):
        if filters:
            self.filters = filters

    def get_query(self):
        filter_queries = []
        if self.filters.keys():
            filter_queries = []
            for qs_filter_name, filter_value in self.filters.items():
                filter_name = to_camel(qs_filter_name.split('__')[0])
                querystring_operator = qs_filter_name.split('__')[-1]
                operator = self.mapping_operator.get(querystring_operator, ':')
                if operator == '..':
                    filter_value_from, filter_value_to = filter_value.split('__')
                    query = '{}:{}{}{}'.format(filter_name, filter_value_from, operator, filter_value_to)
                elif operator == "*":
                    query = '{}:{}{}'.format(filter_name, filter_value, operator)
                else:
                    values = filter_value.split(',')
                    if len(values) == 1:
                        filter_values = values[0]
                    else:
                        filter_values = '(' + ' OR '.join(["{}".format(value) for value in values]) + ')'
                    query = '{}{}{}'.format(filter_name, operator, filter_values)
                filter_queries.append(query)
        if not filter_queries:
            return '*'
        qry = ' AND '.join('{}'.format(query) for query in filter_queries)
        return qry
