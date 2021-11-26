from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
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
        tags_id = None
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


class Top(generic.TemplateView, ContextMolding):
    template_name = 'blog/main.html'
    model = models.Content

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        self.tag = self.request.GET.get('tag')
        self.archive = self.request.GET.get('archive')
        self.page = self.request.GET.get('page')
        return super().get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags_list'] = self.__class__.raw_queryset_dict(models.Tag.select_tags())
        ctx['archive_date'] = self.clean_archive()
        data = self.__class__.raw_queryset_dict(self.model.select_all())

        if self.tag is not None:
            data = self.__class__.raw_queryset_dict(self.model.select_tagmatch(self.tag))
            if len(data) == 0: data = None

        if self.archive is not None:
            try:
                year = int(self.archive[:4])
                month = int(self.archive[-2:])

                if month == 12:
                    max_date = str(year + 1) + '-01'
                else:
                    max_date = str(year) + '-' + str(month + 1) if month >= 9 else str(year) + '-0' + str(month + 1)
                data = self.__class__.raw_queryset_dict(self.model.select_datematch(self.archive, max_date))
                print(data)
            except Exception as e:
                print(e)
                data = None

        if data is None or len(data) == 0:
            raise Http404("投稿は存在しません")
        else:
            ctx['posts'] = data

        return ctx


    def clean_archive(self):
        archive_date = self.__class__.raw_queryset_normal(self.model.select_date())
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
            return False




class Detail(generic.DetailView, ContextMolding):
    template_name = 'blog/detail.html'
    model = models.Content

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags'] = models.Tag.objects.order_by('id')
        data = self.model.select_detail(self.kwargs['pk'])
        ctx['posts'] = self.__class__.raw_queryset_dict(data)
        return ctx


class Admin(LoginRequiredMixin, generic.FormView):
    template_name = 'blog/admin.html'
    form_class = ContentForm
    success_url = '/admin'


    def form_valid(self, form):
        model = form.get_model()
        content = model.objects.create(
            title = form.cleaned_data['title'],
            caption = form.cleaned_data['caption'],
            content = form.cleaned_data['content'],
        )
        content.updated()
        cid = content.id
        for tid in form.cleaned_data['tags']:
            tid = int(tid)
            models.TagMap.objects.create(
                content_id = cid,
                tag_id = tid,
            )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
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



