from django.shortcuts import render
from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout

from rest_framework.settings import api_settings
from rest_framework.response import Response
from rest_framework import status
from core.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from user.api.serializers import UserSerializer, AuthTokenSerializer

# Create your views here.

class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer

class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user"""
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    def get_object(self):
        return self.request.user
class UserDeleteView(generics.DestroyAPIView):
    """Delete the authenticated user"""
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    def get_object(self):
        return self.request.user
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)

class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access
    serializer_class = UserSerializer
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user:
            # Generate or get existing token
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "message": "Login successful"})
        
        return Response({"error": "Invalid credentials"}, status=400)
    
class LogoutView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"})
    
    