from rest_framework import serializers
from .models import UploadedFile, TradingInstrument

class TradingInstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingInstrument
        fields = "__all__"
