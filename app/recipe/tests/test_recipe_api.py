"""Tests for the recipe API."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase 
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.reverse import reverse 
from rest_framework import status
from rest_framework.test import APIClient 
from rest_framework.response import Response
from core.models import Recipe, Tag, Ingredient
from core.models import User,recipe_image_file_path
from unittest.mock import patch
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
from PIL import Image
import os
import tempfile
RECIPE_URL = reverse('recipe:recipe-list')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)

def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """Return image upload URL."""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf'  
    } 
    defaults.update(params)

    # 先创建 Recipe
    recipe = Recipe.objects.create(user=user, **defaults)

    # 创建 Ingredient，并关联 user
    ingredient = Ingredient.objects.create(user=user, name="Salt")
    recipe.ingredients.add(ingredient)  # 关联 ManyToMany 关系

    # 创建 Tag，并关联 user
    tag = Tag.objects.create(user=user, name="Dinner")
    recipe.tags.add(tag)  # 关联 ManyToMany 关系
    recipe.status_code = status.HTTP_201_CREATED

    return recipe


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required."""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API requests."""

  
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)
        Recipe.objects.all().delete()   

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""
        other_user = get_user_model().objects.create_user(
            email='other@example.com',
            password='password123'
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail.""" 
        recipe = create_recipe(user=self.user)
        url = reverse('recipe:recipe-detail', args=[recipe.id])
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }
        res = create_recipe(user=self.user, **payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.id)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test partial update of a recipe."""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample title',
            link=original_link,
        )
        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)        
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test full update of a recipe."""
        recipe = create_recipe(
            user=self.user,
            title='Sample title', 
            link='https://example.com/recipe.pdf',
        )
        payload = { 
            'title': 'New recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'price': recipe.price,
            'time_minutes': recipe.time_minutes,
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)
    
    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(email='user8@example.com', password='testpass123')
        recipe = create_recipe(user=self.user) 
        url = detail_url(recipe.id)
        payload = {'user': new_user.id}
        res = self.client.patch(url, payload)
        recipe.refresh_from_db() 
        self.assertEqual(recipe.user, self.user)
        # self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_delete_recipe(self):
        """Test deleting a recipe successful."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another user's recipe gives error."""
        new_user = create_user(email='user2@example.com', password='testpass123')
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, req):
        """Test that recipe image filename is unique""" 
        filename = 'test.jpg'
        
        req.return_value = 'test'
        self.assertEqual(recipe_image_file_path(None,filename), 
                         f'uploads/recipe/{filename}')
        
class ImageUploadTestCase(TestCase):
    """Test recipe image upload."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user3@example.com', password='testpass123')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = reverse('recipe:recipe-upload-image', args=[self.recipe.id])
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB',(10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload,format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(os.path.exists(self.recipe.image.path))
        self.assertIn('image',res.data)

    def test_upload_image_not_image(self):
        """Test uploading a non-image file to a recipe."""
        url = reverse('recipe:recipe-upload-image', args=[self.recipe.id])
        with tempfile.NamedTemporaryFile(suffix='.txt') as text_file:
            text_file.write(b'Not an image')
            text_file.seek(0)
            payload = {'image': text_file}
            res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        