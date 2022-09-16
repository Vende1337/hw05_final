from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def get_page(queryset, page_number):
    paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
    return paginator.get_page(page_number)


def index(request):
    page_obj = get_page(
        Post.objects
        .select_related('author'), request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_page(group.posts.select_related(
        'author'), request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    page_obj = get_page(author.posts.select_related(
        'group'), request.GET.get('page'))
    following = request.user.is_authenticated and not (
        Follow.objects.filter(
            user__follower__author=author,
            author__following__user=request.user)
        .exists() and request.user == author)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html/', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'), id=post_id)
    comments = post.comments.select_related('author')
    context = {
        'form': CommentForm(),
        'post': post,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, "posts/create_post.html", {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author'), pk=post_id)
    if post.author == request.user:
        form = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
        return render(request, 'posts/create_post.html',
                      {'form': form, 'is_edit': True, })
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    page_obj = get_page(
        Post.objects
        .select_related('author', 'group')
        .filter(author__following__user=request.user), request.GET.get('page'))
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:profile', username=username)
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
