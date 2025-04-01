"""URLs for the recipe API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
    path('recipes/<int:id>/', views.RecipeDetail.as_view(), name='recipe-detail'),
    path('recipe-list/', views.RecipeList.as_view(), name='recipe-list'),
    # path("recipesgv/", views.RecipeList.as_view, name="recipesgv"),
    path('recipe-create/', views.RecipeCreate.as_view(), name='recipe-create'),
    path('ingredients/create/', views.IngredientCreate.as_view(), name='ingredient-create'),
    path('ingredients/', views.IngredientList.as_view(), name='ingredient-list'),
    path('ingredients/<int:id>/', views.IngredientDetail.as_view(), name='ingredient-detail'),
    path('tags/create/', views.TagCreate.as_view(), name='tag-create'),
    path('tags/', views.TagList.as_view(), name='tag-list'),
    path('tags/<int:id>/', views.TagDetail.as_view(), name='tag-detail'),
    
]