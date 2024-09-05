"""
.. module:: utils.functions
   :synopsis: Generic functions used throughout the site.
"""

import json
from django.http import HttpResponse
from itertools import *
from django.db.models.fields.related import ManyToManyField

def renderjson(data, status=200):
    return HttpResponse(
        json.dumps(data, separators=(",", ":")),
        content_type="application/json",
        status=status)


def to_dict(instance):
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, ManyToManyField):
            if instance.pk is None:
                data[f.name] = []
            else:
                data[f.name] = list(f.value_from_object(instance).values_list('pk', flat=True))
        else:
            data[f.name] = f.value_from_object(instance)
    return data

def model_to_dict(instance, fields=None, exclude=None):
    """
    Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    # avoid a circular import
    opts = instance._meta
    # print opts
    data = {}
    for f in chain(opts.concrete_fields, opts.virtual_fields, opts.many_to_many):
        # print f
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, DateTimeField):
            if f.value_from_object(instance):
                try:
                    data[f.name] = f.value_from_object(instance).strftime("%d/%m/%Y %H:%M %p")
                except:
                    data[f.name] = str(f.value_from_object(instance))
            else:
                data[f.name] = ""
        elif isinstance(f, DateField):
            if f.value_from_object(instance):
                try:
                    data[f.name] = f.value_from_object(instance).strftime("%d/%m/%Y")
                except:
                    data[f.name] = str(f.value_from_object(instance))
            else:
                data[f.name] = ""
        elif isinstance(f, UUIDField):
            data[f.name] = str(f.value_from_object(instance))
        elif isinstance(f, ManyToManyField):
            # If the object doesn't have a primary key yet, just use an empty
            # list for its m2m fields. Calling f.value_from_object will raise
            # an exception.
            if instance.pk is None:
                data[f.name] = []
            else:
                # MultipleChoiceWidget needs a list of pks, not object instances.
                qs = f.value_from_object(instance)
                if qs._result_cache is not None:
                    data[f.name] = [item.pk for item in qs]
                else:
                    values_list = list(qs.values())
                    for obj in values_list:
                        for key, value in obj.iteritems():
                            if type(value) == datetime.datetime:
                                obj[key] = value.strftime("%d/%m/%Y %H:%M %p")

                    data[f.name] = values_list
                    # print data
        else:
            data[f.name] = f.value_from_object(instance)
        # print data

    return data


from django.conf import settings
import json
def translation(lang='en'):
    translation = {}
    with open(settings.LANG_FILE, 'r', encoding="utf-8") as f:
        load_lang = json.load(f)
        for key, value in load_lang.items():
            translation[str(key)] = value[lang]
    return translation
    
    