from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from taggit.models import Tag

from .forms import CommentForm, EmailPostForm
from .models import Comment, Post


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:  # фильтрация по тегу
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        #  Если страница не из диапазона, выдаем последнюю
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        posts = paginator.page(1)

    context = {'posts': posts, 'tag': tag}
    return render(request, 'blog/post/list.html', context)


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             slug=post)

    # список комментариев к посту
    comments = post.comments.filter(active=True)

    # Форма для комментирования пользователями
    form = CommentForm()

    # Список схожих постов по тегу

    # Получаем список тегов (без кортежей flat=True)
    post_tags_ids = post.tags.values_list('id', flat=True)
    # Все посты с совпадающими тегами, кроме текущего
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    # Агрегация по количеству общих тегов, сортировка по убыванию общих тегов и публикации, первые 4 поста
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    context = {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts}

    return render(request, 'blog/post/detail.html', context)


def post_share(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)

    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'stas224stas@ya.ru', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()

    context = {'post': post, 'form': form, 'sent': sent}
    return render(request, 'blog/post/share.html', context)


# доступно только по методу POST
@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)

    if form.is_valid():
        # создается новый экземпляр comment, но не сохраняется в базу
        comment = form.save(commit=False)
        comment.post = post
        # а теперь сохраняется в БД
        comment.save()

    context = {'post': post, 'form': form, 'comment': comment}

    return render(request, 'blog/post/comment.html', context)

# Представление классом
# from django.views.generic import ListView
# class PostListView(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'
