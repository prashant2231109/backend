import datetime
import random

from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from demo.utils import send_otp

from .models import UserModel
from .serializers import UserSerializer

from rest_framework import serializers 
from django.contrib.auth import authenticate,login
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view

from django.contrib.auth.models import User
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token







class UserViewSet(viewsets.ModelViewSet):

    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Add default permission for the ViewSet
   
    
    @action(detail=True, methods=["PATCH"])
    def verify_otp(self, request, pk=None):
        instance = self.get_object()
        if (
            not instance.is_active
            and instance.otp == request.data.get("otp")
            and instance.otp_expiry
            and timezone.now() < instance.otp_expiry
        ):
            instance.is_active = True
            instance.otp_expiry = None
            instance.max_otp_try = settings.MAX_OTP_TRY
            instance.otp_max_out = None
            instance.save()
            return Response(
                "Successfully verified the user.", status=status.HTTP_200_OK
            )

        return Response(
            "User active or Please enter the correct OTP.",
            status=status.HTTP_400_BAD_REQUEST,
        )
    @action(detail=True, methods=["PATCH"])
    def regenerate_otp(self, request, pk=None):
        """
        Regenerate OTP for the given user and send it to the user.
        """
        instance = self.get_object()
        if int(instance.max_otp_try) == 0 and timezone.now() < instance.otp_max_out:
            return Response(
                "Max OTP try reached, try after an hour",
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        otp = random.randint(1000, 9999)
        otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
        max_otp_try = int(instance.max_otp_try) - 1

        instance.otp = otp
        instance.otp_expiry = otp_expiry
        instance.max_otp_try = max_otp_try
        if max_otp_try == 0:
            # Set cool down time
            otp_max_out = timezone.now() + datetime.timedelta(hours=1)
            instance.otp_max_out = otp_max_out
        elif max_otp_try == -1:
            instance.max_otp_try = settings.MAX_OTP_TRY
        else:
            instance.otp_max_out = None
            instance.max_otp_try = max_otp_try
        instance.save()
        send_otp(instance.phone_number, otp)
        return Response("Successfully generate new OTP.", status=status.HTTP_200_OK) 
    
# 
# 



    # @action(detail=False, methods=['POST'], permission_classes=[AllowAny])
    # def login(self, request):
    #     phone_number = request.data.get('phone_number')
    #     password = request.data.get('password')
        
    #     if not phone_number or not password:
    #         return Response({
    #             'error': 'Please provide both phone_number and password'
    #         }, status=status.HTTP_400_BAD_REQUEST)
        
    #     user = authenticate(request, username=phone_number, password=password)
        
    #     if user is not None:
    #         login(request, user)
    #         return Response({
    #             'message': 'Login successful',
    #             'user_id': user.id
    #         }, status=status.HTTP_200_OK)
    #     else:
    #         return Response({
    #             'error': 'Invalid credentials'
    #         }, status=status.HTTP_401_UNAUTHORIZED)
            
            
    # demo/views.py

    
    @action(detail=False, methods=['POST'])
    def login(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        
        if not phone_number or not password:
            return Response({
                'error': 'Please provide both phone_number and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=phone_number, password=password)
        
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'Login successful',
                'token': token.key,
                'user_id': user.id
            })
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        serializer = self.get_serializer(request.user)


# Add this to your existing UserViewSet class


    @action(detail=False, methods=['GET'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Get the profile information of the logged-in user
        """
        try:
            # Get the current logged-in user
            user = request.user
            user_profile = UserModel.objects.get(phone_number=user.phone_number)
            
            # Serialize the user data
            serializer = self.get_serializer(user_profile)
            
            return Response({
                'status': 'success',
                'message': 'Profile data retrieved successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except UserModel.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout the currently authenticated user by deleting their auth token
        """
        try:
            # Ensure the user has a token to delete
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
                return Response({
                    'status': 'success',
                    'message': 'Successfully logged out'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'User does not have a valid token'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)