from django.contrib.auth import get_user_model

import factory

from sharepoint_rest_api.models import SharePointLibrary, SharePointSite, SharePointTenant


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: "user%03d" % n)

    last_name = factory.Faker('last_name')
    first_name = factory.Faker('first_name')

    email = factory.Sequence(lambda n: "m%03d@mailinator.com" % n)
    password = 'password'
    is_superuser = False
    is_active = True

    @classmethod
    def _prepare(cls, create, **kwargs):

        password = kwargs.pop('password')
        user = super()._prepare(cls, create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class SharePointTenantFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = SharePointTenant
        django_get_or_create = ('url',)


class SharePointSiteFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "name%03d" % n)

    class Meta:
        model = SharePointSite
        django_get_or_create = ('name',)


class SharePointLibraryFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "name%03d" % n)

    class Meta:
        model = SharePointLibrary
        django_get_or_create = ('name',)
