from rest_framework import serializers
from .models import TradeOrder

class TradeOrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # User is read-only and will be set via the context

    class Meta:
        model = TradeOrder
        fields = ['user', 'trading_symbol', 'display_name', 'quantity', 'price', 'order_type', 'transaction_type', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user  
        validated_data['user'] = user  
        return TradeOrder.objects.create(**validated_data)


from rest_framework import serializers
from .models import TradesTaken, ClosedTrades, TradeHistory
from account.models import User

class TradesTakenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradesTaken
        fields = "__all__"
        read_only_fields = ["id", "profit_loss", "created_at", "updated_at"]


    # def is_valid(self, raise_exception=False):
    #     # Check for missing fields
    #     missing_fields = [field for field in self.fields if field not in self.initial_data]
    #     if missing_fields:
    #         errors = {field: ["This field is required."] for field in missing_fields}
    #         raise serializers.ValidationError(errors)
        
    #     # Call the default validation logic
    #     return super().is_valid(raise_exception=raise_exception)


class ClosedTradesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosedTrades
        fields = "__all__"

    # def create(self, validated_data):
    #     """
    #     Override create method to adjust quantity and user BeetleCoins.
    #     """
    #     closed_trade = super().create(validated_data)
    #     trade = closed_trade.trade
    #     user = trade.user

    #     # Update the trade's quantity
    #     trade.quantity -= closed_trade.sell_quantity
    #     if trade.quantity <= 0:
    #         trade.quantity = 0
    #         trade.invested_coin = 0
    #     else:
    #         trade.invested_coin = trade.quantity * trade.avg_price
    #     trade.save()

    #     # Update the user's BeetleCoins
    #     if hasattr(user, 'beetle_coins'):
    #         user.beetle_coins += closed_trade.profit_loss
    #         user.save()

    #     # Log the transaction in TradeHistory
    #     TradeHistory.objects.create(
    #         trade=trade,
    #         trade_type="sell",
    #         quantity=closed_trade.sell_quantity,
    #         trade_price=closed_trade.sell_price,
    #     )

    #     return closed_trade


class TradeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeHistory
        fields = "__all__"
