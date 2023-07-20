import redis
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST

from actions.utils import create_action
from .forms import ImageCreateForm
from .models import Image

r = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
)


@login_required
def create_image(request):
    if request.method == "POST":
        form = ImageCreateForm(request.POST)
        if form.is_valid():
            image = form.save(commit=False)
            image.user = request.user
            image.save()
            create_action(request.user, "bookmarks", image)
            messages.success(request, "Image created successfully")
            return redirect(image.get_absolute_url())
    else:
        form = ImageCreateForm(data=request.GET)

    return render(
        request,
        "images/image/create.html",
        {"section": "images", "form": form},
    )


def image_detail(request, id, slug):
    image = get_object_or_404(Image, id=id, slug=slug)
    total_views = r.incr(f"image:{image.id}:views")
    r.zincrby("image_ranking", 1, image.id)
    return render(
        request,
        "images/image/detail.html",
        {"section": "images", "image": image, "total_views": total_views},
    )


@login_required
@require_POST
def image_like(request):
    image_id = request.POST.get("id")
    action = request.POST.get("action")

    if image_id and action:
        try:
            image = Image.objects.get(id=image_id)
            if action == "like":
                image.users_like.add(request.user)
                create_action(request.user, "likes", image)
            else:
                image.users_like.remove(request.user)
            return JsonResponse({"status": "ok"})
        except Image.DoesNotExist:
            pass

    return JsonResponse({"status": "error"})


@login_required
def image_list(request):
    """
    images_only tells what we need to show, all images or just requested page.
    All images for browser request and 1 page of images in Fetch Api case
    """

    images = Image.objects.all()
    paginator = Paginator(images, 8)
    images_only, page = request.GET.get("images_only"), request.GET.get("page")

    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        images = paginator.page(1)
    except EmptyPage:
        if images_only:
            return HttpResponse("")
        images = paginator.page(paginator.num_pages)

    # if AJAX request
    if images_only:
        doc = "images/image/list_images.html"
    else:
        doc = "images/image/list.html"

    return render(request, doc, {"section": images, "images": images})


@login_required
def image_ranking(request):
    """Most viewed images"""
    images = r.zrange("image_ranking", 0, -1, desc=True)[:10]
    images_ids = [int(image_id) for image_id in images]
    images = list(Image.objects.filter(id__in=images_ids))
    images.sort(key=lambda x: images_ids.index(x.id))

    return render(
        request,
        "images/image/rating.html",
        {"section": images, "most_viewed_images": images},
    )
