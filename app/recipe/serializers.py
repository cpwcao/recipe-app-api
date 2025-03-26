"""Serializers for the core app."""

from httpcore import Response
from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient

class MySerializer(serializers.Serializer):
    my_field = serializers.BooleanField(allow_null=True, required=False)

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create and return an ingredient."""
        return Ingredient.objects.create(**validated_data)


class IngredientDetailSerializer(IngredientSerializer):
    class Meta(IngredientSerializer.Meta):
        fields = IngredientSerializer.Meta.fields + ['recipe']
        read_only_fields = IngredientSerializer.Meta.read_only_fields + ['recipe']  
        
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create and return a tag."""
        return Tag.objects.create(**validated_data)

class TagDetailSerializer(TagSerializer):
    class Meta(TagSerializer.Meta):
        fields = TagSerializer.Meta.fields + ['recipe']
        read_only_fields = TagSerializer.Meta.read_only_fields + ['recipe']
        
class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredient_names = serializers.SerializerMethodField()
    tag_names = serializers.SerializerMethodField()
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'description', 'time_minutes', 'price', 'link', 'ingredients', 'tags', 'ingredient_names', 'tag_names']
        read_only_fields = ['id','user']
    
    def create(self, validated_data):
        """Create and return a recipe."""
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.ingredients.set(ingredients)
        recipe.tags.set(tags)
        return Response(recipe,status_code=status.HTTP_201_CREATED)
    
    def get_ingredient_names(self, obj):
        return [ingredient.name for ingredient in obj.ingredients.all()]

    # Method to get the tag names
    def get_tag_names(self, obj):
        return [tag.name for tag in obj.tags.all()]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['ingredients', 'tags']
        read_only_fields = RecipeSerializer.Meta.read_only_fields + ['ingredients', 'tags']
        
