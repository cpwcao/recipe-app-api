"""Serializers for the core app."""

from rest_framework import status
from httpcore import Response
from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient
 
class RecipeImageSerializer(serializers.ModelSerializer):
    "serializes for uploading images to recipes."""
    image = serializers.ImageField(max_length=None, use_url=True)
    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': False}}


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
        fields = ['id', 'title', 'description', 'time_minutes', 'price', 'link', 'ingredients', 
                  'tags', 'ingredient_names', 'tag_names','image']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create and return a recipe."""
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user =self.context['request'].user
        recipe.ingredients.set(ingredients)
        recipe.tags.set(tags) 
        return recipe
    
    def update(self, instance, validated_data):

        """Update a recipe, setting the ingredients correctly and return it"""
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.ingredients.set(ingredients)
        instance.tags.set(tags)
        instance.save()  # Save the instance before returning it to ensure the foreign key relationships are updated
        
        return instance  # Return the updated instance  to the  database    
         
    
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
        read_only_fields = RecipeSerializer.Meta.read_only_fields
        
