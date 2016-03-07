import django.db.models
import django.forms
from django.apps import apps
from django.db.models.signals import class_prepared
from django.utils.translation import ugettext_lazy as _

from fedoralink.forms import LangFormTextField, LangFormTextAreaField, MultiValuedFedoraField, GPSField


class IndexedField:
    __global_order = 0

    MANDATORY   = 'mandatory'
    RECOMMENDED = 'recommended'
    OPTIONAL    = "optional"

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False, attrs=None, level=None):
        self.rdf_name     = rdf_name
        self.required     = required
        self.verbose_name = verbose_name
        self.attrs        = attrs if attrs else {}
        self.multi_valued = multi_valued
        self.order = IndexedField.__global_order
        if level is None:
            if required:
                level = IndexedField.MANDATORY
            else:
                level = IndexedField.OPTIONAL
        self.level = level
        IndexedField.__global_order += 1


class IndexedLanguageField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)


    def formfield(self, **kwargs):
        if 'textarea' in self.attrs.get('presentation', ''):
            defaults = {'form_class': LangFormTextAreaField}
        else:
            defaults = {'form_class': LangFormTextField}

        defaults.update(kwargs)
        return super().formfield(**defaults)
    #
    # for debugging
    #
    # def __getattribute__(self,name):
    #     attr = object.__getattribute__(self, name)
    #     if hasattr(attr, '__call__') and name not in ('__class__', ):
    #         def newfunc(*args, **kwargs):
    #             print('before calling %s' %attr.__name__)
    #             result = attr(*args, **kwargs)
    #             print('done calling %s: %s' %(attr.__name__, result))
    #             try:
    #                 if len(result) == 2:
    #                     print("in")
    #             except:
    #                 pass
    #             return result
    #         return newfunc
    #     else:
    #         return attr


class IndexedTextField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def formfield(self, **kwargs):
        if self.multi_valued:
            defaults = {'form_class': MultiValuedFedoraField }
        else:
            defaults = {'form_class': django.forms.CharField}

        defaults.update(kwargs)
        return super().formfield(**defaults)

    def get_internal_type(self):
        if self.multi_valued:
            return None
        return 'TextField'


class IndexedIntegerField(IndexedField, django.db.models.IntegerField):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.IntegerField.__init__(self, verbose_name=verbose_name, help_text=help_text)


class IndexedDateTimeField(IndexedField, django.db.models.DateTimeField):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.DateTimeField.__init__(self, verbose_name=verbose_name, help_text=help_text)


class IndexedDateField(IndexedField, django.db.models.DateField):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.DateField.__init__(self, verbose_name=verbose_name, help_text=help_text)


def register_model_lookup(field, related_model):
    if isinstance(related_model, str):
        app_label, model_name = related_model.split('.')
        try:
            field.related_model = apps.get_registered_model(app_label, model_name)
        except LookupError:
            def resolve(**kwargs):
                clz = kwargs['sender']
                if clz._meta.app_label == app_label and clz._meta.object_name == model_name:
                    field.related_model = clz
                    class_prepared.disconnect(resolve, weak=False)

            class_prepared.connect(resolve, weak=False)
    else:
        field.related_model = related_model



class IndexedLinkedField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, related_model, required=False, verbose_name=None, multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

        register_model_lookup(self, related_model)

    def get_internal_type(self):
        return 'TextField'


class IndexedBinaryField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, related_model, required=False, verbose_name=None, multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

        register_model_lookup(self, related_model)

    def formfield(self, **kwargs):
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {'form_class': django.forms.FileField}
        defaults.update(kwargs)
        return super(IndexedBinaryField, self).formfield(**defaults)

    def get_internal_type(self):
        return 'FileField'


class IndexedGPSField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, required=False, verbose_name=None, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=False, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def formfield(self, **kwargs):
        defaults = {'form_class': GPSField}

        defaults.update(kwargs)
        return super().formfield(**defaults)

    def get_internal_type(self):
        return 'TextField'