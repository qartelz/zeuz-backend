from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import TradeOrder
from account.models import BeetleCoins
from .serializers import TradeOrderSerializer
from account.models import BeetleCoins
from rest_framework.permissions import IsAuthenticated

from rest_framework import status  


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TradesTaken, ClosedTrades, TradeHistory
from .serializers import TradesTakenSerializer, ClosedTradesSerializer, TradeHistorySerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TradesTaken, TradeHistory
from .serializers import TradesTakenSerializer
from rest_framework_simplejwt.tokens import AccessToken



"""this is the more condition being checked for trades"""

class TradeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        # Extract data from request
        ticker = data.get("ticker")
        trade_type = data.get("trade_type")
        trade_price = data.get("avg_price")
        quantity = data.get("quantity")
        invested_amount = data.get("invested_coin")
        print(ticker,trade_type,trade_price,quantity,invested_amount)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        if trade_type not in ["Buy", "Sell"]:
            return Response({"error": "Invalid trade type. Use 'Buy' or 'Sell'."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if an existing trade exists for this user and ticker
        existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).first()
        print(existing_trade)

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
        except BeetleCoins.DoesNotExist:
            return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)

        # if beetle_coins.coins < invested_amount:
        #     return Response(
        #         {"error": "Insufficient Beetle Coins to execute the trade."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        if existing_trade:
            print("Already")
            # Handle different conditions based on `trade_type` and `trade_status`
            print(trade_type,existing_trade.trade_type,existing_trade.trade_status)
            if trade_type == "Buy" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete":
                print("here")
                # Update the existing trade (Buy + Buy)
                existing_trade.avg_price = (
                    (existing_trade.avg_price * existing_trade.quantity + trade_price * quantity)
                    / (existing_trade.quantity + quantity)
                )
                existing_trade.quantity += quantity
                existing_trade.invested_coin+=invested_amount
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Buy",
                    quantity=quantity,
                    trade_price=trade_price,
                )
                try:
                    beetle_coins.use_coins(invested_amount)
                except ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                return Response(
                    {
                        "message": "Existing incomplete buy trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,
                )
            
            elif trade_type == "Buy" and existing_trade.trade_type == "Sell" and existing_trade.trade_status == "incomplete":
                # Validate the requested quantity
                if quantity > existing_trade.quantity:
                    return Response(
                        {"error": "Cannot buy more than the available sell quantity."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                profit_loss = (float(existing_trade.avg_price) -float(trade_price)) * quantity

                # Calculate profit/loss for this transaction (Short Selling Scenario)

               

                print(profit_loss)
                
                ClosedTrades.objects.create(
                trade=existing_trade,
                sell_quantity=quantity,
                sell_price=trade_price,
                profit_loss=profit_loss,
            )

                # Calculate profit/loss for this transaction
                    


                # Record the Buy in TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Buy",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                # Record the Sell in ClosedTrades (always append)
                
                # Adjust the existing trade quantity
                existing_trade.quantity -= quantity
                existing_trade.invested_coin-=invested_amount

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()
                invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                beetle_coins.coins+=profit_loss

                # Check and deduct Beetle Coins before proceeding
                try:
                    beetle_coins.use_coins(invested_amount)
                except ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                

                # Build response message
                message = (
                    "Trade completed and recorded." if existing_trade.trade_status == "complete"
                    else "Partial trade executed and recorded."
                )

                return Response(
                    {
                        "message": message,
                        "trade_history": TradeHistory.objects.filter(trade=existing_trade).values(),
                        "closed_trades": ClosedTrades.objects.filter(trade=existing_trade).values(),
                    },
                    status=status.HTTP_200_OK,
                )




            elif trade_type == "Sell" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete":
           
            # Validate the requested quantity
                if quantity > existing_trade.quantity:
                    return Response(
                        {"error": "Cannot sell more than the available buy quantity."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                # Calculate profit/loss for this transaction (Buy + Sell Scenario)
                profit_loss = (float(trade_price) - float(existing_trade.avg_price)) * quantity
                print(profit_loss)

                # Record the Sell in ClosedTrades
                ClosedTrades.objects.create(
                    trade=existing_trade,
                    sell_quantity=quantity,
                    sell_price=trade_price,
                    profit_loss=profit_loss,
                )

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Sell",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                # Adjust the existing trade quantity
                existing_trade.quantity -= quantity
                existing_trade.invested_coin-=invested_amount
                beetle_coins.coins+=profit_loss

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()
                
                invested_amount = (existing_trade.avg_price * quantity) + profit_loss

                # Check and deduct Beetle Coins before proceeding
                try:
                    beetle_coins.use_coins(invested_amount)
                except ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                

                # Build response message
                message = (
                    "Trade completed and recorded." if existing_trade.trade_status == "complete"
                    else "Partial trade executed and recorded."
                )

                return Response(
                    {
                        "message": message,
                        "trade_history": TradeHistory.objects.filter(trade=existing_trade).values(),
                        "closed_trades": ClosedTrades.objects.filter(trade=existing_trade).values(),
                    },
                    status=status.HTTP_200_OK,
                )

            

            elif trade_type == "Sell" and existing_trade.trade_type == "Sell" and existing_trade.trade_status == "incomplete":
                # Update the existing sell trade (Sell + Sell)
                existing_trade.avg_price = (
                    (existing_trade.avg_price * existing_trade.quantity + trade_price * quantity)
                    / (existing_trade.quantity + quantity)
                )
                existing_trade.quantity += quantity
                existing_trade.invested_coin+=invested_amount
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Sell",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                try:
                    beetle_coins.use_coins(invested_amount)
                except ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                return Response(
                    {
                        "message": "Existing incomplete sell trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,
                )
        #     else:
        #         if existing_trade and existing_trade.trade_status == "complete":
        #             # Create a new trade since the existing one is complete
        #             new_trade = TradesTaken.objects.create(
        #                 user=user,
        #                 ticker=ticker,
        #                 trade_type=trade_type,
        #                 avg_price=trade_price,
        #                 quantity=quantity,
        #                 trade_status="incomplete",  
        #             )

        #             # Record this new trade in TradeHistory
        #             TradeHistory.objects.create(
        #                 trade=new_trade,
        #                 trade_type=trade_type,
        #                 quantity=quantity,
        #                 trade_price=trade_price,
        #             )
        #             try:
        #                 beetle_coins.use_coins(invested_amount)
        #             except ValidationError as e:
        #                 return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        #             return Response(
        #                 {
        #                     "message": "New trade created for the completed ticker.",
        #                     "data": TradesTakenSerializer(new_trade).data,
        #                 },
        #                 status=status.HTTP_201_CREATED,
        # )


            else:
                return Response(
                    {"error": "Invalid trade update scenario."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # If no existing trade, create a new one
        data["user"] = user.id  # Add user to the data
        serializer = TradesTakenSerializer(data=data)

        if serializer.is_valid():
            
            new_trade = serializer.save()
            print(new_trade)

            # Add to TradeHistory
            TradeHistory.objects.create(
                trade=new_trade,
                trade_type=trade_type,
                quantity=quantity,
                trade_price=trade_price,
            )
            try:
                beetle_coins.use_coins(invested_amount)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"message": "New trade created.......", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




class UserTradesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the authenticated user
        user = request.user

        # Query all trades taken by this user
        user_trades = TradesTaken.objects.filter(user=user)

        # Serialize the data
        serializer = TradesTakenSerializer(user_trades, many=True)

        # Return the response
        return Response(
            {"message": "User trades retrieved successfully.", "data": serializer.data},
            status=status.HTTP_200_OK
        )

