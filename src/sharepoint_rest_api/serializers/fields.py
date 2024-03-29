from rest_framework import serializers

from sharepoint_rest_api.utils import first_upper, to_camel


class SharePointPropertyField(serializers.ReadOnlyField):
    """
    Get attribute from the object or properties converting it to camlcase
    e.g. from_date --> fromDate
    """

    def get_attribute(self, instance):
        camel_case = to_camel(self.source)
        if isinstance(instance, dict) and camel_case in instance:
            return instance[camel_case]
        return super().get_attribute(instance)


class UpperSharePointPropertyField(serializers.ReadOnlyField):
    """
    Get attribute from the object or properties, it changes to upper case
    e.g uuid --> UUID
    """

    def get_attribute(self, instance):
        upper_case = self.source.upper()
        if isinstance(instance, dict) and upper_case in instance:
            return instance[upper_case]
        return super().get_attribute(instance)


class SharePointPropertyManyField(serializers.ReadOnlyField):
    """
    Get attribute from the object or properties, handles multivalues
    """

    def get_attribute(self, instance):
        camel_case = to_camel(self.source)
        if isinstance(instance, dict) and camel_case in instance:
            values = instance[camel_case]
            if values:
                values = values.replace('; ', ';').split(';')
            return values
        return super().get_attribute(instance)


class RawSearchSharePointField(serializers.ReadOnlyField):
    """
    Gets the name of the field without any transformation
    """
    def get_attribute(self, instance):
        return instance.get(self.source, 'N/A')


class SearchSharePointField(serializers.ReadOnlyField):
    """
    Gets the name of the field transforming the name with caml query function
    e.g. last_name -> LastName
    """
    def get_attribute(self, instance):
        field_name = to_camel(self.source)
        return instance.get(field_name, 'N/A')


class CapitalizeSearchSharePointField(serializers.ReadOnlyField):
    """
    Gets the name of the field capitalizing the name of the field
    e.g. example -> Example
    """
    def get_attribute(self, instance):
        field_name = first_upper(self.source)
        return instance.get(field_name, 'N/A')
