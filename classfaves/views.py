from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.db import transaction
from django.core import serializers
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth.models import User

RESPONSE_MAPPING = {
    'application/json': 'json',
    'text/xml': 'xml',
}

class FavoriteBase(object):
    """
    This is the base class that all of the class-based views for this app
    will subclass.
    """
    def __init__(self, favorite, content_model, fk_name=None, extra_context={},
        context_init=RequestContext, next_field='next',
        response_mapping=RESPONSE_MAPPING, use_transactions=True):
        self.favorite = favorite
        self.content_model = content_model
        self.extra_context = extra_context
        self.context_init = context_init
        self.response_mapping = response_mapping
        self.next_field = next_field
        self.use_transactions = use_transactions
        
        # If we have no explicitly-set foreign key name, we attempt to
        # determine that information by traversing all of the related fields
        # and choose the first one that relates to the content model
        if fk_name is None:
            for field in self.favorite._meta.fields:
                if field.rel and field.rel.to == self.content_model:
                    fk_name = field.name
                    break
        if fk_name is None:
            raise ValueError('Could not find related field between %s and '
                '%s. Please either specify it to %s using the keyword '
                'argument fk_name, and ensure that your models are '
                'constructed properly' % (
                    self.favorite, self.content_model, self.__class__.__name__
                )
            )
        self.fk_name = fk_name
    
    def __call__(self, request, *args, **kwargs):
        """
        By implementing the call method, we allow the class itself to act as
        the view function, taking in the request object and returning the
        response.  This method is responsible for dealing with transaction
        management, dispatching to the proper instance methods, and returning
        a valid HttpResponse.
        """
        if self.use_transactions:
            transaction.commit_unless_managed()
            transaction.enter_transaction_management()
            transaction.managed(True)
        
        context = self.view(request, *args, **kwargs)
        if isinstance(context, HttpResponseRedirect):
            return context
        context.update(self.extra_context)
        
        if self.next_field in request.REQUEST:
            next = request.REQUEST[self.next_field]
            if ':/' not in next:
                return HttpResponseRedirect(next)
        
        response = self.create_response(request, context)
        if self.use_transactions:
            transaction.commit()
            transaction.leave_transaction_management()
        
        return response
    
    def create_response(self, request, context):
        """
        This method receives the proper context variables and, based upon the
        ``HTTP_ACCEPT`` from the request, it will dispatch the context to the
        proper method for creating HttpResponse objects.  This could involve
        rendering HTML using templates, or it could simply be serialization
        using one of JSON or XML renderers.
        """
        try:
            http_accept = request.META['HTTP_ACCEPT'].split(',')[0]
        except (KeyError, IndexError):
            http_accept = None
        response_kind = self.response_mapping.get(http_accept, 'html')
        context_instance = None
        if response_kind == 'html':
            context_instance = self.context_init(request)
        responder = getattr(self, response_kind)
        return responder(context, context_instance=context_instance)
    
    def json(self, context, context_instance):
        """
        Given some context variables, this method returns a JSON representation
        of those variables.
        """
        raise NotImplemented
    
    def xml(self, context, context_instance):
        """
        Given some context variables, this method returns an XML representation
        of those variables.
        """
        raise NotImplemented
    
    def html(self, context, context_instance):
        """
        Given some context variables, this method returns rendered HTML for
        those variables.
        """
        raise NotImplemented


class CreateFavorite(FavoriteBase):
    """
    This is a class that allows for the favoriting of your content objects.
    """
    def __init__(self, *args, **kwargs):
        self.template_name = kwargs.pop('template_name',
            'favorites/created.html')
        super(CreateFavorite, self).__init__(*args, **kwargs)
    
    def json(self, context, context_instance):
        """
        Given some context variables, this method returns a JSON representation
        of those variables.
        """
        data = serializers.serialize('json', [context['favorite']])
        return HttpResponse(data, content_type='application/json')
    
    def xml(self, context, context_instance):
        """
        Given some context variables, this method returns an XML representation
        of those variables.
        """
        data = serializers.serialize('xml', [context['favorite']])
        return HttpResponse(data, content_type='text/xml')
    
    def html(self, context, context_instance):
        """
        Given some context variables, this method returns rendered HTML for
        those variables.
        """
        return render_to_response(self.template_name, context,
            context_instance=context_instance)
    
    def view(self, request, pk=None):
        """
        Given the request and a primary key (of the content object), this
        method is responsible for returning a dictionary of context variables
        suitable for being passed to one of the serialization methods.
        """
        if not request.user.is_authenticated():
            return HttpResponseRedirect('%s?next=%s' % (
                settings.LOGIN_URL,
                request.path,
            ))
        content_object = get_object_or_404(self.content_model, pk=pk)
        favorite, created = self.favorite.objects.get_or_create(**{
            'user': request.user,
            self.fk_name: content_object,
        })
        return {'favorite': favorite, 'created': created, 'item': content_object}


class DeleteFavorite(FavoriteBase):
    """
    This is a class that allows for the un-favoriting of your content objects.
    """
    def __init__(self, *args, **kwargs):
        self.template_name = kwargs.pop('template_name',
            'favorites/deleted.html')
        super(DeleteFavorite, self).__init__(*args, **kwargs)
    
    def json(self, context, context_instance):
        """
        Given some context variables, this method returns a JSON representation
        of those variables.
        """
        data = serializers.serialize('json', [context['item']])
        return HttpResponse(data, content_type='application/json')
    
    def xml(self, context, context_instance):
        """
        Given some context variables, this method returns an XML representation
        of those variables.
        """
        data = serializers.serialize('xml', [context['item']])
        return HttpResponse(data, content_type='text/xml')
    
    def html(self, context, context_instance):
        """
        Given some context variables, this method returns rendered HTML for
        those variables.
        """
        return render_to_response(self.template_name, context,
            context_instance=context_instance)
    
    def view(self, request, pk=None):
        """
        Given the request and a primary key (of the content object), this
        method is responsible for returning a dictionary of context variables
        suitable for being passed to one of the serialization methods.
        """
        if not request.user.is_authenticated():
            return HttpResponseRedirect('%s?next=%s' % (
                settings.LOGIN_URL,
                request.path,
            ))
        content_object = get_object_or_404(self.content_model, pk=pk)
        favorites = self.favorite.objects.filter(**{
            'user': request.user,
            self.fk_name: content_object,
        })
        i = 0
        for i, favorite in enumerate(favorites):
            favorite.delete()
        return {
            'num_deleted': i,
            'item': content_object,
            self.fk_name: content_object,
        }

class UserFavorites(FavoriteBase):
    """
    This is a class that can produce a list of a user's favorite content
    objects.
    """
    def __init__(self, *args, **kwargs):
        self.template_name = kwargs.pop('template_name',
            'favorites/list.html')
        self.extra_filter = kwargs.pop('extra_filter', lambda x: x)
        super(UserFavorites, self).__init__(*args, **kwargs)
    
    def json(self, context, context_instance):
        """
        Given some context variables, this method returns a JSON representation
        of those variables.
        """
        data = serializers.serialize('json', context['favorites'])
        return HttpResponse(data, content_type='application/json')
    
    def xml(self, context, context_instance):
        """
        Given some context variables, this method returns an XML representation
        of those variables.
        """
        data = serializers.serialize('xml', context['favorites'])
        return HttpResponse(data, content_type='text/xml')
    
    def html(self, context, context_instance):
        """
        Given some context variables, this method returns rendered HTML for
        those variables.
        """
        return render_to_response(self.template_name, context,
            context_instance=context_instance)
    
    def view(self, request, username=None):
        """
        Given the request and a primary key (of the content object), this
        method is responsible for returning a dictionary of context variables
        suitable for being passed to one of the serialization methods.
        """
        # The username can be None, but then the user must be logged in.
        # If the username is None and the user's not logged in, we redirect
        # them to the login page
        if username is None:
            if not request.user.is_authenticated():
                return HttpResponseRedirect('%s?next=%s' % (
                    settings.LOGIN_URL,
                    request.path,
                ))
            user = request.user
        else:
            user = get_object_or_404(User, username__iexact=username)
        
        # Sometimes it can be useful to know if the user is looking at their
        # own page, so we determine that as a convenience
        is_self = user == request.user
        
        # TODO: Can the following queries be made more efficient?
        base_faves = self.favorite.objects.filter(user=user)
        content_ids = self.extra_filter(base_faves).values_list(self.fk_name,
            flat=True).query
        # TODO: Ensure that the content models are returned in order of when
        #       they were favorited.
        favorites = self.content_model.objects.filter(pk__in=content_ids)
        return {
            'favorites': favorites,
            'favorite_user': user,
            'is_self': is_self,
        }