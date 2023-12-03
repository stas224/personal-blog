import markdown
from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe

from ..models import Post

# Экземпляр класса, который используется для регистрации библиотеки тегов и фильтров приложения
register = template.Library()


@register.simple_tag
def total_posts():
    """
    Регистрация простого тега, название функции будет использоваться как название шаблонного тега
     @register.simple_tag(name='my_tag') - изменение имени функции на кастомное для тега
    """
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    """
    Регистрация тега включения для шаблона, который будет прорисовываться возвращаемыми значениями
    """
    latest_posts = Post.published.order_by('-publish')[:count]
    context = {'latest_posts': latest_posts}
    return context


@register.simple_tag
def get_most_commented_posts(count=5):
    """
    Тег, возвращающий наиболее комментируемые посты
    (с помощью annotate формируем набор запросов с агрегацией кол-ва комментариев к каждому посту)
    """
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]


@register.filter(name='markdown')
def markdown_format(text):
    """
    Конвертация markdown-текста
    mark-safe - помечает текст как безопасный
    """
    return mark_safe(markdown.markdown(text))
