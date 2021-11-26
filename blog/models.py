from django.db import models
from django.utils import timezone
from mdeditor.fields import MDTextField
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.


class Tag(models.Model):
    name = models.TextField(unique=True)

    @staticmethod
    def select_tags():
        return Tag.objects.raw('''
        SELECT
        tag_id AS id,
        name AS tag_name,
        COUNT(tag_id) AS count
        FROM
        blog_tag AS tag
        LEFT JOIN blog_tagmap AS tagmap ON tag.id = tagmap.tag_id 
        GROUP BY tag.id
        ORDER BY tag.id DESC
        ''')


class TagMap(models.Model):
    content_id = models.IntegerField([MinValueValidator(1)])
    tag_id = models.IntegerField([MinValueValidator(1)])



class Content(models.Model):
    title = models.TextField(max_length=50)
    caption = models.TextField(max_length=100)
    content = MDTextField()
    finished = models.DateTimeField(null=True)

    def updated(self):
        self.finished = timezone.now()
        self.save()
        return self


    @staticmethod
    def select_all():
        return Content.objects.raw('''
        SELECT content.id,
        content.title,
        content.caption,
        group_concat(tag.name, ',') AS tag_name 
        FROM blog_content AS content 
        LEFT JOIN blog_tagmap AS tagmap ON content.id = tagmap.content_id
        LEFT JOIN blog_tag AS tag ON tagmap.tag_id = tag.id 
        GROUP BY content.id ORDER BY content.id DESC
        ''')

    @staticmethod
    def select_tagmatch(tname):
        return Content.objects.raw('''
        SELECT 
        content.id,
        content.title,
        content.caption,
        group_concat(tag.name, ',') as tag_name 
        FROM (
        SELECT tagmap.content_id
        FROM (SELECT * FROM blog_tag WHERE blog_tag.name = %s) AS search_tag 
        INNER JOIN blog_tagmap AS tagmap ON search_tag.id = tagmap.tag_id
        ) AS sr_content 
        INNER JOIN blog_content AS content ON sr_content.content_id = content.id
        INNER JOIN blog_tagmap AS tagmap ON content.id = tagmap.content_id
        INNER JOIN blog_tag AS tag ON tagmap.tag_id = tag.id 
        GROUP BY content.id ORDER BY content.id ASC
        ''',[tname]
        )

    @staticmethod
    def select_datematch(min_date, max_date):
        return Content.objects.raw('''
        SELECT 
        content.id,
        content.title,
        content.caption,
        group_concat(tag.name, ',') AS tag_name 
        FROM
        (SELECT
        id AS content_id
        FROM
        (
        (SELECT datetime('%(min_date)s-01 00:00:00') AS dt_min, datetime('%(max_date)s-01 00:00:00') AS dt_max)
        LEFT JOIN blog_content
        ON 
        strftime('%s', dt_min) + strftime('%f', dt_min) - round( strftime('%f', dt_min) ) <= strftime('%s', finished) + strftime('%f', finished) - round( strftime('%f', finished) )
        AND
        strftime('%s', dt_max) + strftime('%f', dt_max) - round( strftime('%f', dt_max) ) > strftime('%s', finished) + strftime('%f', finished) - round( strftime('%f', finished) )
        ) AS base_dt)
        AS sr_content
        INNER JOIN blog_content AS content ON sr_content.content_id = content.id
        INNER JOIN blog_tagmap AS tagmap ON content.id = tagmap.content_id
        INNER JOIN blog_tag AS tag ON tagmap.tag_id = tag.id 
        GROUP BY content.id ORDER BY content.id ASC
        ''', {"min_date":min_date, "max_date":max_date})


    @staticmethod
    def select_detail(cid):
        return Content.objects.raw('''
        SELECT 
        content.id,
        strftime(%s, date(content.finished)) AS posted_date,
        content.title,
        content.content,
        group_concat(tag.name, ',') AS tag_name 
        FROM blog_content as content 
        LEFT JOIN blog_tagmap AS tagmap ON content.id = tagmap.content_id 
        LEFT JOIN blog_tag AS tag ON tagmap.tag_id = tag.id 
        where content.id = %s
        ''' ,['%Y年%m月%d日', cid]
        )


    @staticmethod
    def select_date():
        return Content.objects.raw('''
        SELECT
        1 AS id,
        strftime('%Y-%m', MIN(finished)) AS dt_min,
        strftime('%Y-%m', MAX(finished)) AS dt_max
        FROM  blog_content AS content
        ''')

