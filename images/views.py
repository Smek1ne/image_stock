from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404

from .forms import ImageCreateForm
from .models import Image


@login_required
def create_image(request):
    if request.method == "POST":
        form = ImageCreateForm(request.POST)
        if form.is_valid():
            image = form.save(commit=False)
            image.user = request.user
            image.save()
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
    return render(
        request,
        "images/image/detail.html",
        {"section": "images", "image": image}
    )
