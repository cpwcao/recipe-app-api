"""Serializers for the user API view"""

from rest_framework import serializers

from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _
from rest_framework.authtoken.models import Token
from core.models import User
 
class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}


    def create(self, validated_data):
        """Create and return a user with encrypted password"""
        return User.objects.create_user(**validated_data)   
    
    
class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user authentication object"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = ('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authorization')
        
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        """Generate a token for the user"""
        user = validated_data['user']
        token = Token.objects.create(user=user)
        return user, token  
        