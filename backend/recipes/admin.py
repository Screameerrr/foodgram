import csv


from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag, TagRecipe
from django.http import HttpResponseRedirect
from .forms import ImportForm


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    extra = 1


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (TagRecipeInline, IngredientRecipeInline)
    list_display = ("name", "author", "favorite_count_display")
    search_fields = ("author__username", "name")
    list_filter = ("tags",)
    readonly_fields = ("favorite_count_display", "short_link")

    @admin.display(description="Добавили в Избранное")
    def favorite_count_display(self, obj):
        return obj.favorited_by.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)
    def upload_csv(self, request):
        if request.method == 'POST':
            form = ImportForm(
                request.POST,
                request.FILES
            )
            if form.is_valid():
                form_object = form.save()
                with form_object.csv_file.open(mode='r') as csv_file:
                    rows = csv.reader(
                        csv_file,
                        delimiter=','
                    )
                    for row in rows:
                        Ingredient.objects.update_or_create(
                            name=row[0],
                            measurement_unit=row[1]
                        )
                url = reverse('admin:index')
                messages.success(
                    request,
                    'Файл импортирован'
                )
                return HttpResponseRedirect(url)
        form = ImportForm()
        return render(
            request,
            'admin/csv_import_page.html',
            {'form': form}
        )