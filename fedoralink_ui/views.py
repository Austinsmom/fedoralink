from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import resolve
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render
from django.template import Template, RequestContext
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext as _
from django.views.generic import View, CreateView, DetailView, UpdateView

from fedoralink.forms import FedoraForm
from fedoralink.indexer.models import IndexableFedoraObject
from fedoralink.models import FedoraObject
from fedoralink.type_manager import FedoraTypeManager
from fedoralink.utils import get_class
from fedoralink_ui.template_cache import FedoraTemplateCache
from fedoralink_ui.templatetags.fedoralink_tags import id_from_path, rdf2lang


def appname(request):
    print('appname: ')
    print(request.path)
    print(resolve(request.path).app_name)
    return {'appname': resolve(request.path).app_name}


def breadcrumbs(request, context={}, resolver_match=None, path=None, **initkwargs):
    if path.endswith('/'):
        path = path[:-1]

    if path != request.path:
        return

    obj = context['object']
    breadcrumb_list = []
    while isinstance(obj, IndexableFedoraObject):
        object_id = id_from_path(obj.pk, initkwargs.get('fedora_prefix', None))
        if object_id:
            breadcrumb_list.insert(0, (
                reverse('%s:%s' % (resolver_match.app_name, resolver_match.url_name),
                        kwargs={'pk': object_id}),
                str(rdf2lang(obj.title))
            ))
        else:
            # reached root of the portion of repository given by fedora_prefix
            break

        parent_id = obj.fedora_parent_uri
        if parent_id:
            obj = FedoraObject.objects.get(pk=parent_id)
        else:
            # reached root of the repository
            break

    return breadcrumb_list


def get_model(collection_id, fedora_prefix = None):
    if fedora_prefix:
        collection_id = fedora_prefix + '/' + collection_id
    model = FedoraTemplateCache.get_collection_model(FedoraObject.objects.get(pk=collection_id))
    model = FedoraTypeManager.get_model_class_from_fullname(model)
    return model


class GenericIndexView(View):
    app_name = None

    # noinspection PyUnusedLocal
    def get(self, request, *args, **kwargs):
        app_name = self.app_name
        if app_name is None:
            app_name = appname(request)['appname']
        return HttpResponseRedirect(reverse(app_name + ':extended_search',
                                            kwargs={'parameters': '',
                                                    'collection_id': kwargs.get('collection_id', '')
                                                    }))


class GenericSearchView(View):
    template_name = 'fedoralink_ui/search.html'
    list_item_template = 'fedoralink_ui/search_result_row.html'
    orderings = ()
    facets = None
    title = None
    create_button_title = None
    search_fields = ()
    fedora_prefix = ''

    # noinspection PyCallingNonCallable,PyUnresolvedReferences
    def get(self, request, *args, **kwargs):

        model = get_model(collection_id = kwargs['collection_id'], fedora_prefix=self.fedora_prefix)

        if self.facets and callable(self.facets):
            requested_facets = self.facets(request)
        else:
            requested_facets = self.facets

        within_collection = None
        if 'path' in kwargs:
            within_collection = FedoraObject.objects.get(pk=kwargs['path'])

        requested_facet_ids = [x[0] for x in requested_facets]

        data = model.objects.all()

        if requested_facets:
            data = data.request_facets(*requested_facet_ids)

        if 'searchstring' in request.GET and request.GET['searchstring'].strip():
            q = None
            for fld in self.search_fields:
                q1 = Q(**{fld.replace('@', '__') + "__fulltext": request.GET['searchstring'].strip()})
                if q:
                    q |= q1
                else:
                    q = q1
            data = data.filter(q)

        for k in request.GET:
            if k.startswith('facet__'):
                values = request.GET.getlist(k)
                k = k[len('facet__'):]
                q = None
                for v in values:
                    if not q:
                        q = Q(**{k: v})
                    else:
                        q |= Q(**{k: v})
                if q:
                    data = data.filter(q)

        if within_collection:
            data = data.filter(_fedora_parent__exact=within_collection.id)

        sort = request.GET.get('sort', self.orderings[0][0])
        if sort:
            data = data.order_by(*[x.strip() for x in sort.split(',')])
        page = request.GET.get('page', )
        paginator = Paginator(data, 10)

        try:
            page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page = paginator.page(paginator.num_pages)

        template = None
        if 'path' in kwargs:
            template = FedoraTemplateCache.get_template_string(within_collection,
                                                               'search')

        if not template:
            template = get_template(self.template_name)

        context = RequestContext(request, {
            'page': page,
            'data': data,
            'item_template': self.list_item_template,
            'facet_names': {k: v for k, v in requested_facets},
            'searchstring': request.GET.get('searchstring', ''),
            'orderings': self.orderings,
            'ordering': sort,
            'title': self.title,
            'create_button_title': self.create_button_title,
            'fedora_prefix': self.fedora_prefix
        })

        return TemplateResponse(request, template, context)




# noinspection PyAttributeOutsideInit,PyProtectedMember
class GenericDetailView(DetailView):
    template_name = 'fedoralink_ui/detail.html'
    fedora_prefix = None

    def get_queryset(self):
        return FedoraObject.objects.all()

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None).replace("_", "/")
        if self.fedora_prefix and 'prefix_applied' not in self.kwargs:
            pk = self.fedora_prefix + '/' + pk
            self.kwargs['prefix_applied'] = True
        print("pk", pk)
        self.kwargs[self.pk_url_kwarg] = pk
        retrieved_object = super().get_object(queryset)
        if not isinstance(retrieved_object, IndexableFedoraObject):
            raise Exception("Can not use object with pk %s in a generic view as it is not of a known type" % pk)
        return retrieved_object

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # noinspection PyTypeChecker
        template = FedoraTemplateCache.get_template_string(self.object, view_type='view')
        if template:
            context = self.get_context_data(object=self.object)
            return HttpResponse(
                Template("{% extends '" + self.template_name + "' %}" + template).render(
                    RequestContext(request, context)))
        return super(GenericDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fedora_prefix'] = self.fedora_prefix
        return context

    @classonlymethod
    def as_view(cls, **initkwargs):
        ret = super().as_view(**initkwargs)

        # def breadcrumbs(request, context={}, resolver_match=None, path=None):
        #     if path.endswith('/'):
        #         path = path[:-1]
        #
        #     if path != request.path:
        #         return
        #
        #     obj = context['object']
        #     breadcrumb_list = []
        #     while isinstance(obj, IndexableFedoraObject):
        #         object_id = id_from_path(obj.pk, initkwargs.get('fedora_prefix', None))
        #         if object_id:
        #             breadcrumb_list.insert(0, (
        #                 reverse('%s:%s' % (resolver_match.app_name, resolver_match.url_name),
        #                         kwargs={'pk': object_id}),
        #                 str(rdf2lang(obj.title))
        #             ))
        #         else:
        #             # reached root of the portion of repository given by fedora_prefix
        #             break
        #
        #         parent_id = obj.fedora_parent_uri
        #         if parent_id:
        #             obj = FedoraObject.objects.get(pk=parent_id)
        #         else:
        #             # reached root of the repository
        #             break
        #
        #     return breadcrumb_list

        ret.urlbreadcrumbs_verbose_name = breadcrumbs
        return ret


# class GenericCollectionDetailView(View):
#     model = None
#     template_name = 'fedoralink_ui/collection_detail.html'
#     list_item_template = 'fedoralink_ui/search_result_row.html'
#     orderings = ()
#     default_ordering = ''
#     facets = None
#     title = None
#     create_button_title = None
#
#     def get(self, request, parameters):
#         # if isinstance(self.model, str):
#         #     self.model = get_class(self.model)
#         #
#         # if self.facets and callable(self.facets):
#         #     requested_facets = self.facets(request, parameters)
#         # else:
#         #     requested_facets = self.facets
#         #
#         # requested_facet_ids = [x[0] for x in requested_facets]
#         #
#         # data = self.model.objects.all()
#         #
#         # if requested_facets:
#         #     data = data.request_facets(*requested_facet_ids)
#         #
#         # if 'searchstring' in request.GET and request.GET['searchstring'].strip():
#         #     data = data.filter(solr_all_fields=request.GET['searchstring'].strip())
#         #
#         # for k in request.GET:
#         #     if k.startswith('facet__'):
#         #         values = request.GET.getlist(k)
#         #         k = k[len('facet__'):]
#         #         q = None
#         #         for v in values:
#         #             if not q:
#         #                 q = Q(**{k: v})
#         #             else:
#         #                 q |= Q(**{k: v})
#         #         if q:
#         #             data = data.filter(q)
#         #
#         # sort = request.GET.get('sort', self.default_ordering or self.orderings[0][0])
#         # if sort:
#         #     data = data.order_by(*[x.strip() for x in sort.split(',')])
#         # page = request.GET.get('page', )
#         # paginator = Paginator(data, 10)
#         #
#         # try:
#         #     page = paginator.page(page)
#         # except PageNotAnInteger:
#         #     # If page is not an integer, deliver first page.
#         #     page = paginator.page(1)
#         # except EmptyPage:
#         #     # If page is out of range (e.g. 9999), deliver last page of results.
#         #     page = paginator.page(paginator.num_pages)
#
#         return render(request, self.template_name, {
#             # 'page': page,
#             # 'data': data,
#             'item_template': self.list_item_template,
#             # 'facet_names': {k: v for k, v in requested_facets},
#             'searchstring': request.GET.get('searchstring', ''),
#             'orderings': self.orderings,
#             # 'ordering': sort,
#             'title': self.title,
#             'create_button_title': self.create_button_title
#         })


class GenericCreateView(CreateView):
    fields = '__all__'
    # TODO: parent_collection nebude potrebny, moznost ziskat z url
    parent_collection = None
    success_url_param_names = ()
    template_name = 'fedoralink_ui/create.html'
    fedora_prefix = ''

    def form_valid(self, form):
        inst = form.save(commit=False)
        inst.save()
        self.object = inst
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        ret = super().get_form_kwargs()
        parent = self.get_parent_object()
        if parent is None:
            if callable(self.parent_collection):
                parent = self.parent_collection(self)
            else:
                parent = self.parent_collection
        model = get_model(collection_id=self.kwargs.get('pk'), fedora_prefix=self.fedora_prefix)
        self.object = ret['instance'] = parent.create_child('', flavour=model)

        return ret

    def get_queryset(self):
        return FedoraObject.objects.all()

    # noinspection PyUnusedLocal,PyProtectedMember
    def get_parent_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URL conf, but subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        queryset = self.get_queryset()

        # Next, try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            queryset = queryset.filter(pk=self.fedora_prefix+"/"+pk)

            try:
                # Get the single item from the filtered queryset
                obj = queryset.get()
            except queryset.model.DoesNotExist:
                raise Http404(_("No %(verbose_name)s found matching the query") %
                              {'verbose_name': queryset.model._meta.verbose_name})
            return obj
        else:
            return None

    def get_form_class(self):
        print(self.kwargs)
        model = get_model(collection_id=self.kwargs.get('pk'), fedora_prefix=self.fedora_prefix)
        meta = type('Meta', (object, ), {'model': model, 'fields': '__all__'})
        return type(model.__name__ + 'Form', (FedoraForm,), {
            'Meta': meta
        })

    @classonlymethod
    def as_view(cls, **initkwargs):
        ret = super().as_view(**initkwargs)
        def breadcrumbs(request, context={}, resolver_match=None, path=None):
            if path.endswith('/'):
                path = path[:-1]

            if path != request.path:
                return

            obj = context['object']
            breadcrumb_list = []
            while isinstance(obj, IndexableFedoraObject):
                object_id = id_from_path(obj.pk, initkwargs.get('fedora_prefix', None))
                if object_id:
                    breadcrumb_list.insert(0, (
                        reverse('%s:%s' % (resolver_match.app_name, resolver_match.url_name),
                                kwargs={'pk': object_id}),
                        str(rdf2lang(obj.title))
                    ))
                else:
                    # reached root of the portion of repository given by fedora_prefix
                    break

                parent_id = obj.fedora_parent_uri
                if parent_id:
                    obj = FedoraObject.objects.get(pk=parent_id)
                else:
                    # reached root of the repository
                    break

            return breadcrumb_list
        ret.urlbreadcrumbs_verbose_name = breadcrumbs
        return ret

    # noinspection PyProtectedMember
    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response, using the `response_class` for this
        view, with a template rendered with the given context.

        If any keyword arguments are provided, they will be
        passed to the constructor of the response class.
        """
        model = get_model(self.kwargs.get('pk'), fedora_prefix=self.fedora_prefix)
        template = FedoraTemplateCache.get_template_string(self.object if self.object else model,
                                                           view_type='create')
        if template:
            return HttpResponse(
                Template("{% extends '" + self.template_name + "' %}" + template).render(
                    RequestContext(self.request, context)))
        return super().render_to_response(context, **response_kwargs)

    def get_success_url(self):
        return reverse(self.success_url,
                       kwargs={k: _convert(k, getattr(self.object, k)) for k in self.success_url_param_names})


class GenericEditView(UpdateView):
    model = None
    fields = '__all__'
    success_url_param_names = ('id',)
    template_name = 'fedoralink_ui/edit.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        return FedoraObject.objects.all()

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None).replace("_", "/")
        self.kwargs[self.pk_url_kwarg] = pk
        retrieved_object = super().get_object(queryset)
        if not isinstance(retrieved_object, IndexableFedoraObject):
            raise Exception("Can not use object with pk %s in a generic view as it is not of a known type" % pk)
        return retrieved_object

    def get_form_class(self):
        meta = type('Meta', (object,), {'model': self.model, 'fields': '__all__'})
        return type(self.model.__name__ + 'Form', (FedoraForm,), {
            'Meta': meta
        })

    # noinspection PyAttributeOutsideInit,PyProtectedMember
    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response, using the `response_class` for this
        view, with a template rendered with the given context.

        If any keyword arguments are provided, they will be
        passed to the constructor of the response class.
        """
        self.object = self.get_object()
        form = self.get_form()
        context = self.get_context_data(object=self.object, form=form, **response_kwargs)
        # noinspection PyTypeChecker
        template = FedoraTemplateCache.get_template_string(self.object, view_type='edit')

        if template:
            return HttpResponse(
                Template("{% extends '" + self.template_name + "' %}" + template).render(
                    RequestContext(self.request, context)))
        return super().render_to_response(context, **response_kwargs)

    def get_success_url(self):
        return reverse(self.success_url,
                       kwargs={k: _convert(k, getattr(self.object, k)) for k in self.success_url_param_names})


def _convert(name, value):
    if name == 'pk' or name == 'id':
        return id_from_path(value)
    return value
