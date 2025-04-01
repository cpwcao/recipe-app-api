from django.shortcuts import render
from django.test import tag
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets,generics,mixins,status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.generics import  RetrieveAPIView
from core.models import Recipe, Ingredient, Tag
from recipe.serializers import (RecipeSerializer, RecipeDetailSerializer,IngredientSerializer,TagSerializer,
RecipeImageSerializer)
from drf_spectacular.utils import (extend_schema, 
                                   extend_schema_view,
                                   OpenApiParameter,
                                   OpenApiTypes
                            )

# Create your views here.
# @extend_schema_view(
#     list=extend_schema(
#         parameters=[
#             OpenApiParameter(
#                 name='ingredients',
#                 description='A comma-separated list of ingredient IDs.',
#                 type=OpenApiTypes.STR,
#             ),
#             OpenApiParameter(
#                 name='tags',
#                 description='A comma-separated list of tag IDs.',
#                 type=OpenApiTypes.STR,
#             ),
#         ]
#     )
# )
class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def _params_to_ints(self,qs):
        return [int(pk) for pk in qs.split(',') if pk.isdigit()]
        
    def perform_update(self, serializer):
        """Override update to ensure update works properly"""
        serializer.save()

    def get_queryset(self):
        """Retrieve recipes for the authenticated user"""
        qs = self.request.query_params.get('ingredients',None)
        if qs is not None:
            qs = self._params_to_ints(qs)
            recipe_ingredients = Ingredient.objects.filter(pk__in=qs)
            self.queryset = self.queryset.filter(ingredients__in=recipe_ingredients)
        qs =self.request.query_params.get('tags',None)
        if qs is not None:
            qs = self._params_to_ints(qs)
            recipe_tags = Tag.objects.filter(pk__in=qs)
            self.queryset = self.queryset.filter(tags__in=recipe_tags)
        return self.queryset.filter(user=self.request.user).order_by('-id')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeSerializer
        if self.action == 'upload_image':
            return RecipeImageSerializer
        return self.serializer_class
    @action(methods=['POST'],detail=True,url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Handle uploading of recipe image"""
        recipe = self.get_object()
        serializer = self.get_serializer_class()(recipe, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request

        return context
    
    def perform_create(self, serializer): 
        recipe = serializer.save(user=self.request.user)        
        recipe.ingredients.set(serializer.validated_data.get('ingredients', []))        
        recipe.tags.set(serializer.validated_data.get('tags', []))
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name='ingredients',
                description='A comma-separated list of ingredient IDs.',
                type=OpenApiTypes.STR),
            OpenApiParameter(
                name='tags',
                description='A comma-separated list of tag IDs.',
                type=OpenApiTypes.STR)
        ]),
    ) 
# class RecipeDetail(RetrieveAPIView):
class RecipeDetail(generics.RetrieveUpdateAPIView):
    """Retrieve a recipe by ID"""
    queryset = Recipe.objects.all()
    serializer_class = RecipeDetailSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    lookup_field = 'id'
    lookup_url_kwarg = 'pk' 

    def _params_to_ints(self,qs):
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(',')]
    
    def get_queryset(self):
        """Filter recipes by the authenticated user"""
        queryset = self.queryset.filter(user=self.request.user)
        qs_params = self.request.query_params.get('ingredients', None)
        if qs_params is not None:
            queryset = queryset.filter(ingredients__id__in=self._params_to_ints(qs_params))
        qs_params = self.request.query_params.get('tags', None)
        if qs_params is not None:
            queryset = queryset.filter(tags__id__in=self._params_to_ints(qs_params))
        return queryset 
        
    
    
    def perform_update(self, serializer): 
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
class RecipeList(generics.ListAPIView):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title', 'ingredients', 'tags__name']  # Filter by title, author, and tag names
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id')
    
    
class RecipeCreate(generics.CreateAPIView):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def perform_create(self, serializer): 
        try:
            # Start a transaction to handle any failures
            with transaction.atomic():  
                recipe = serializer.save(user=self.request.user)
                ingredients = serializer.validated_data.get('ingredients', [])
                tags = serializer.validated_data.get('tags', [])
                
                # Attempt to set ingredients and tags
                recipe.ingredients.set(ingredients)
                recipe.tags.set(tags)

                return Response(RecipeSerializer(recipe).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Delete recipe if setting ingredients/tags fails
            if recipe:
                recipe.delete()
            
            return Response(
                {"error": f"Recipe creation failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class IngredientCreate(generics.CreateAPIView):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
class IngredientList(generics.ListAPIView):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id')
   
class IngredientDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id')

class TagCreate(generics.CreateAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class TagList(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id') 
    
class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id') 