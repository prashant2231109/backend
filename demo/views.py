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
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny




class UserViewSet(viewsets.ModelViewSet):

    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
   
    
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
    
    
    

# # Add this action to your existing UserViewSet class
# class UserViewSet(viewsets.ModelViewSet):
#     queryset = UserModel.objects.all()
#     serializer_class = UserSerializer

    # Add your existing verify_otp and regenerate_otp methods here...

    # @action(detail=False, methods=['POST'])
    # def login(self, request):
    #     serializer = LoginSerializer(data=request.data)
    #     if not serializer.is_valid():
    #         return Response(
    #             serializer.errors,
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     phone_number = serializer.validated_data['phone_number']
    #     password = serializer.validated_data['password']

    #     try:
    #         user = UserModel.objects.get(phone_number=phone_number)
            
    #         if not user.check_password(password):
    #             return Response(
    #                 {"error": "Invalid credentials"},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         if not user.is_active:
    #             # Generate OTP for inactive users
    #             otp = random.randint(1000, 9999)
    #             otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
                
    #             user.otp = otp
    #             user.otp_expiry = otp_expiry
    #             user.max_otp_try = settings.MAX_OTP_TRY
    #             user.save()
                
    #             # Send OTP
    #             send_otp(user.phone_number, otp)
                
    #             return Response({
    #                 "message": "Account not verified. OTP sent to your phone number.",
    #                 "user_id": user.id,
    #                 "requires_otp": True
    #             }, status=status.HTTP_200_OK)

    #         # User is active and credentials are valid
    #         return Response({
    #             "message": "Login successful",
    #             "user_id": user.id,
    #             "phone_number": user.phone_number,
    #             "is_active": user.is_active
    #         }, status=status.HTTP_200_OK)

    #     except UserModel.DoesNotExist:
    #         return Response(
    #             {"error": "User not found"},
    #             status=status.HTTP_404_NOT_FOUND
    #         )