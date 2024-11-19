from .models import Profile, User
from adminlogin.models import Tokens
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import generate_otp, set_otp_in_cache, get_otp_from_cache, delete_otp_from_cache, send_otp_email
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import AccessToken, TokenError

from .serializers import SignUpSerializer, LoginSerializer, OTPVerificationSerializer, ResetPasswordSerializer, ForgotPasswordSerializer, ProfileSerializer


class SignUpView(APIView):
    # permission_classes = [AllowAny]

    def post(self, request):
       
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'email': user.email,
                'name': user.name,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):

    def post(self, request):
        print(request.data)
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():

            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            print(user)

            try:
                token_data = Tokens.objects.get(id=1)
                broadcast_token = token_data.broadcast_token
                broadcast_userid = token_data.broadcast_userid
            except Tokens.DoesNotExist:
                return Response({
                    'detail': 'Token data not found'
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'email': user.email,
                'name': user.name,
                'broadcast_token': broadcast_token,
                'broadcast_userid': broadcast_userid,
                'detail': 'Login Successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WelcomeView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        user = request.user  
        welcome_message = f"Welcome {user.name}!" if user.name else "Welcome!"
        return Response({
            'message': welcome_message
        }, status=status.HTTP_200_OK)


class OTPVerificationView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            cached_otp = get_otp_from_cache(email, "email_verification")

            if cached_otp == otp_code:
                user = User.objects.get(email=email)
                user.is_active = True  
                user.save()
                delete_otp_from_cache(email, "email_verification")
                return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                otp_code = generate_otp()
                set_otp_in_cache(user.email, otp_code, purpose="password_reset")
                send_otp_email(user.email, otp_code, purpose="password reset")
                return Response({'message': 'OTP has been sent to your email for password reset.'},
                                status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']
            cached_otp = get_otp_from_cache(email, "password_reset")

            if cached_otp == otp_code:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save() 
                delete_otp_from_cache(email, "password_reset")
                return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProfileCreateView(APIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        print(request, "test the user data")
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return Response({"detail": "Authorization header is missing."}, status=400)
        
        token_str = auth_header.split(" ")[1]
        
        token = AccessToken(token_str)
        user_id = token["user_id"]

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if Profile.objects.filter(user=user).exists():
            return Response({"detail": "Profile already exists for this user."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProfileSerializer(data=request.data, context={'user': user})

        print(serializer,"profile") 
        if serializer.is_valid():

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        auth = request.headers.get('Authorization')

        token_str = auth.split(" ")[1]
        
        token = AccessToken(token_str)
        user_id = token["user_id"]
        print(user_id)

        try:
            user = User.objects.get(id=user_id)
            profile = Profile.objects.get(user=user)
            serializer = ProfileSerializer(profile)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)




class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)


# from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import BeetleCoins
from rest_framework import status

class GetBeetleCoinsView(APIView):
    permission_classes = [AllowAny]  
    def get(self, request):
        email = request.query_params.get('email')  
        if not email:
            return Response({"error": "Email parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)  
            beetle_coins = BeetleCoins.objects.get(user=user)  
            
            data = {
                "user": user.email,
                "coins": beetle_coins.coins,
                "used_coins": beetle_coins.used_coins,
            }
            return Response(data, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
        except BeetleCoins.DoesNotExist:
            return Response({"error": "Beetle coins record not found for this user."}, status=status.HTTP_404_NOT_FOUND)




