from office365.runtime.client_value import ClientValue


class SearchRequest(ClientValue):

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def entity_type_name(self):
        return "Microsoft.Office.Server.Search.REST.SearchRequest"
