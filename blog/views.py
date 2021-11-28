from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.utils.functional import cached_property
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
import django.contrib.auth.views as authview
from django.urls import reverse_lazy, reverse
from .forms import *
from . import models

User = get_user_model()


class ContextMolding:

    @staticmethod
    def raw_queryset_normal(raw_qs): 
        columns = raw_qs.columns
        data = []
        for row in raw_qs:
            r = {}
            for col in columns:
                r[col] = getattr(row, col)
            data.append(r)
        return data

    @staticmethod
    def raw_queryset_dict(raw_qs): 
        columns = raw_qs.columns
        data = []
        tags_name = None
        for row in raw_qs:
            r = {}
            pimp = []
            for col in columns:
                base = getattr(row, col)
                if col == 'tag_name': 
                    tags_name = base.split(',')
                else:
                    r[col] = base
            for i in range(len(tags_name)):
                pimp.append({
                    'name': tags_name[i],
                })
            r['tags'] = pimp
            data.append(r)
        return data


    @staticmethod
    def clean_archive():
        archive_date = ContextMolding.raw_queryset_normal(models.Content.select_date())
        try:
            dty_min, dtm_min = int(archive_date[0]['dt_min'][:4]), int(archive_date[0]['dt_min'][-2:])
            dty_max, dtm_max = int(archive_date[0]['dt_max'][:4]), int(archive_date[0]['dt_max'][-2:])
            archive_date = []
            for year in range(dty_min, dty_max + 1):
                if year == dty_max:
                    for month in range(dtm_min, dtm_max + 1):
                        month = str(month)
                        month = month if len(month) == 2 else '0' + month
                        archive_date.append(str(year) + '-' + month)
                else:
                    for month in range(dtm_min, 13):
                        month = str(month)
                        month = month if len(month) == 2 else '0' + month
                        archive_date.append(str(year) + '-' + str(month))
                dtm_min = 1
            return archive_date
        except:
            return None


class Top(generic.ListView, ContextMolding):
    template_name = 'blog/main.html'
    model = models.Content

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content_cnt = 7

    def get(self, request, *args, **kwargs):
        self.tag = request.GET.get('tag')
        self.archive = request.GET.get('archive')
        self.page = request.GET.get('page')
        return super().get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags_list'] = self.__class__.raw_queryset_dict(models.Tag.select_tags())
        ctx['archive_date'] = self.__class__.clean_archive()
        data = self.__class__.raw_queryset_dict(self.model.select_all())

        if self.tag is not None:
            data = self.__class__.raw_queryset_dict(self.model.select_tagmatch(self.tag))
            if len(data) == 0: 
                data = None
            else:
                ctx['get_param'] = '?tag={}&&'.format(self.tag)
            

        if self.archive is not None:
            try:
                year = int(self.archive[:4])
                month = int(self.archive[-2:])
                max_date = self.max_date(year, month)
                
                data = self.__class__.raw_queryset_dict(self.model.select_datematch(self.archive, max_date))
            except Exception as e:
                data = None
            else:
                ctx['get_param'] = '?archive={}&&'.format(self.archive)


        if data is None or len(data) == 0:
            raise Http404("投稿は存在しません")
        else:
            if 'get_param' not in ctx.keys(): 
                ctx['get_param'] = '?'
            data = self.paginate_query(data, self.content_cnt)
            ctx['posts'] = data

        return ctx

    def max_date(self, year, month):
        if month == 12:
            return str(year + 1) + '-01'
        else:
            return str(year) + '-' + str(month + 1) if month >= 9 else str(year) + '-0' + str(month + 1)



    def paginate_query(self, queryset, count):
        paginator = Paginator(queryset, count)
        try:
            page_obj = paginator.page(self.page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return page_obj



class Detail(generic.DetailView, ContextMolding):
    template_name = 'blog/detail.html'
    model = models.Content

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags_list'] = self.__class__.raw_queryset_dict(models.Tag.select_tags())
        ctx['archive_date'] = self.__class__.clean_archive()
        ctx['posts'] = self.__class__.raw_queryset_dict(self.model.select_detail(self.kwargs['pk']))
        return ctx


class Admin(LoginRequiredMixin, generic.FormView):
    template_name = 'blog/admin.html'
    form_class = ContentForm
    success_url = '/admin'

    def get(self, request, *args, **kwargs):
        self.content_id= request.GET.get('content_id')
        return super().get(request)

    def post(self, request, *args, **kwargs):
        self.content_id= request.GET.get('content_id')
        return super().post(request)

    def form_valid(self, form):
        if self.content_id is None:
            model = form.get_model()
            content = model.objects.create(
                title = form.cleaned_data['title'],
                caption = form.cleaned_data['caption'],
                content = form.cleaned_data['content'],
            )
            content.updated()

            for tid in form.cleaned_data['tags']:
                models.TagMap.objects.create(
                    content_id = content.id,
                    tag_id = tid,
                )
        else:
            content = form.get_model().objects.get(pk=self.content_id)
            content.title = form.cleaned_data['title']
            content.caption = form.cleaned_data['caption']
            content.content = form.cleaned_data['content']
            content.save()
            content.updated()
            models.TagMap.objects.filter(content_id=self.content_id).delete()

            for tid in form.cleaned_data['tags']:
                models.TagMap.objects.create(
                    content_id = self.content_id,
                    tag_id = tid,
                )

        return super().form_valid(form)


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if self.content_id is not None:
            try:
                content_id = self.content_id
                selected_tags = [tmap.tag_id for tmap in models.TagMap.objects.filter(content_id=content_id)]
                content = models.Content.objects.get(pk=content_id)
                ctx['form'] = self.form_class(initial={
                    'tags': selected_tags,
                    'title': content.title,
                    'caption': content.caption,
                    'content': content.content,
                })
                ctx['submit'] = '更新'
            except Exception as e:
                raise Http404("投稿IDが存在しません")
        else:
            ctx['submit'] = '投稿'

        ctx['page'] = 'blog_admin'
        return ctx


class Tag(LoginRequiredMixin, generic.FormView):
    template_name = 'blog/tag_register.html'
    form_class = TagForm
    success_url = '/admin/tag-register'

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tag_list'] = models.Tag.objects.all()
        return ctx



class Login(authview.LoginView):
    form_class = LoginForm
    template_name = 'blog/login.html'



