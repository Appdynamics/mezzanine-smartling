import re
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet

# The majority of this code was taken from https://pypi.python.org/pypi/django-reversion
# There are slight rewrites to tailor to the needs of the page_translations app


class RegistrationError(Exception):
    """Exception thrown when registration with page_translations goes wrong."""


class FollowAdapter(object):
    follow = ()

    def __init__(self, model):
        """Initializes the version adapter."""
        self.model = model

    def get_followed_relations(self, obj):
        """Returns an iterable of related models that should be included in the revision data."""
        for relationship in self.follow:
            # Clear foreign key cache.
            try:
                related_field = obj._meta.get_field(relationship)
            except models.FieldDoesNotExist:
                pass
            else:
                if isinstance(related_field, models.ForeignKey):
                    if hasattr(obj, related_field.get_cache_name()):
                        delattr(obj, related_field.get_cache_name())
            # Get the referenced obj(s).
            try:
                related = getattr(obj, relationship)
            except ObjectDoesNotExist:
                continue
            if isinstance(related, models.Model):
                yield related
            elif isinstance(related, (models.Manager, QuerySet)):
                for related_obj in related.all():
                    yield related_obj
            elif related is not None:
                raise TypeError("Cannot follow the relationship {relationship}. Expected a model or QuerySet, found {related}".format(
                    relationship = relationship,
                    related = related,
                ))


class RelationalManager(object):
    def __init__(self):
        self._registered_models = {}

    def is_registered(self, model):
        """
        Checks whether the given model has been registered with this relational
        manager.
        """
        return model in self._registered_models

    def register(self, model, adapter_cls=FollowAdapter, **field_overrides):
        if self.is_registered(model):
            return
        if model._meta.proxy:
            raise RegistrationError("Proxy models cannot be used with page_translations, register the parent class instead")
        if field_overrides:
            adapter_cls = type(adapter_cls.__name__, (adapter_cls,), field_overrides)
        adapter_obj = adapter_cls(model)
        self._registered_models[model] = adapter_obj

    def get_registered_models(self):
        """Returns an iterable of all registered models."""
        return list(self._registered_models.keys())

    def get_adapter(self, model):
        """Returns the registration information for the given model class."""
        if self.is_registered(model):
            return self._registered_models[model]
        return False
        raise RegistrationError("{model} has not been registered with page_translations".format(
            model = model,
        ))

    def follow_relationships(self, objects):
        """Follows all relationships in the given set of objects."""
        followed = set()
        def _follow(obj):
            if obj in followed or obj.pk is None:
                return
            followed.add(obj)
            adapter = self.get_adapter(obj.__class__)
            if adapter:
                for related in adapter.get_followed_relations(obj):
                    _follow(related)
        for obj in objects:
            _follow(obj)
        return followed

default_relational_manager = RelationalManager()

