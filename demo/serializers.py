from datetime import datetime, timedelta
import random
from django.conf import settings
from rest_framework import serializers

from .models import UserModel
from demo.utils import send_otp
class UserSerializer(serializers.ModelSerializer):
   

    password1 = serializers.CharField(
        write_only=True,
        min_length=settings.MIN_PASSWORD_LENGTH,
        error_messages={
            "min_length": "Password must be longer than {} characters".format(
                settings.MIN_PASSWORD_LENGTH
            )
        },
    )
    password2 = serializers.CharField(
        write_only=True,
        min_length=settings.MIN_PASSWORD_LENGTH,
        error_messages={
            "min_length": "Password must be longer than {} characters".format(
                settings.MIN_PASSWORD_LENGTH
            )
        },
    )

    class Meta:
        model = UserModel
        fields = (
            "id",
            "phone_number",
            "email",
            "password1",
            "password2"
        )
        read_only_fields = ("id",)
        
    def validate(self, data):
        """
        Validates if both password are same or not.
        """

        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match")
        return data
    

    def create(self, validated_data):
       
        otp = random.randint(1000, 9999)
        otp_expiry = datetime.now() + timedelta(minutes = 10)

        user = UserModel(
            phone_number=validated_data["phone_number"],
            email=validated_data["email"],
            otp=otp,
            otp_expiry=otp_expiry,
            max_otp_try=settings.MAX_OTP_TRY,
        )
        user.set_password(validated_data["password1"])
        user.save()
        send_otp(validated_data["phone_number"], otp)
        return user 
    
    
    
    
    
    #extra
    # class LoginSerializer(serializers.Serializer):
    #     phone_number = serializers.CharField()
    #     password = serializers.CharField(write_only=True)

    # def validate(self, attrs):
    #     phone_number = attrs.get('phone_number')
    #     password = attrs.get('password')

    #     if not phone_number or not password:
    #         raise serializers.ValidationError({
    #             "error": "Both phone number and password are required."
    #         })
    #     return attrs   