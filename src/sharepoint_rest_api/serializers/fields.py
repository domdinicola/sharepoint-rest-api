from rest_framework import serializers

from sharepoint_rest_api.utils import first_upper, to_camel


class SharePointPropertyField(serializers.ReadOnlyField):
    """Get attribute from the object or properties, convering camlcase from_date --> fromDate"""

    def get_attribute(self, instance):
        camel_case = to_camel(self.source)
        if getattr(instance, 'properties') and camel_case in instance.properties:
            return instance.properties[camel_case]
        return super().get_attribute(instance)


class UpperSharePointPropertyField(serializers.ReadOnlyField):
    """Get attribute from the object or properties, it changes to upper case e.g uuid --> UUID"""

    def get_attribute(self, instance):
        upper_case = self.source.upper()
        if getattr(instance, 'properties') and upper_case in instance.properties:
            return instance.properties[upper_case]
        return super().get_attribute(instance)


class SharePointPropertyManyField(serializers.ReadOnlyField):
    """Get attribute from the object or properties, handles multivalue"""

    def get_attribute(self, instance):
        camel_case = to_camel(self.source)
        if getattr(instance, 'properties') and camel_case in instance.properties:
            values = instance.properties[camel_case]
            if values:
                values = values.replace('; ', ';').split(';')
            return values
        return super().get_attribute(instance)


class RawSearchSharePointField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        return [item['Value'] for item in instance if item['Key'] == self.source][0]


class SearchSharePointField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        field_name = to_camel(self.source)
        return [item['Value'] for item in instance if item['Key'] == field_name][0]


class CapitalizeSearchSharePointField(serializers.ReadOnlyField):
    def get_attribute(self, instance):
        field_name = first_upper(self.source)
        return [item['Value'] for item in instance if item['Key'] == field_name][0]
