from django.urls import path
from .views import SignUpView, LoginView, WelcomeView, OTPVerificationView, ForgotPasswordView, ResetPasswordView, ProfileCreateView, ProfileDetailView, ProfileUpdateView,UserTradeSummaryView
from rest_framework_simplejwt.views import TokenRefreshView
# from trades.views import TradeOrderCreateView
from .views import GetBeetleCoinsView
urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/welcome/', WelcomeView.as_view(), name='welcome'),
    path('verify-email/', OTPVerificationView.as_view(), name='verify-email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('profile/create/', ProfileCreateView.as_view(), name='profile-create'),
    path('profile/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),

    # path('trade-order/', TradeOrderCreateView.as_view(), name='trade-order-create'),
    path('get-beetle-coins/', GetBeetleCoinsView.as_view(), name='get_beetle_coins'),

    path('trade-summary/', UserTradeSummaryView.as_view(), name='user-trade-summary'),
]
