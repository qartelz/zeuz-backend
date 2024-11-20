from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from .utils import generate_otp, set_otp_in_cache, send_otp_email
from .models import Profile,BeetleCoins
from trades.models import ClosedTrades

User = get_user_model()


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['email', 'name', 'phone_number', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        otp_code = generate_otp()
        set_otp_in_cache(user.email, otp_code, purpose="email_verification")
        send_otp_email(user.email, otp_code, purpose="email verification")
        return user


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid login credentials")


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'bio', 'address', 'city']

    def create(self, validated_data):
        user = self.context['user']
        validated_data['user'] = user
        return Profile.objects.create(**validated_data)
    

class ClosedTradesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosedTrades
        fields = ['sell_quantity', 'sell_price', 'sell_date', 'profit_loss']

# Serializer for BeetleCoins
class BeetleCoinsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeetleCoins
        fields = ['coins', 'used_coins']