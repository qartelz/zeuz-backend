from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import TradeOrder
from account.models import BeetleCoins
from .serializers import TradeOrderSerializer

from rest_framework.permissions import IsAuthenticated

from rest_framework import status  

class TradeOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        
        current_day = datetime.now().weekday()
        
        if current_day == 5 or current_day == 6:  
            status = "Pending"
        else:  
            status = "Executed"

       
        user = request.user

        
        quantity = request.data.get('quantity')
        price = request.data.get('price')

        
        total_cost = quantity * price

        
        beetle_coins = BeetleCoins.objects.get(user=user)

        
        if beetle_coins.coins < total_cost:
            return Response({"detail": "Insufficient BeetleCoins."}, status=status.HTTP_400_BAD_REQUEST)

        beetle_coins.use_coins(total_cost)
        request.data['status'] = status

        serializer = TradeOrderSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()  
            return Response(serializer.data)  

        return Response(serializer.errors)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TradesTaken, ClosedTrades, TradeHistory
from .serializers import TradesTakenSerializer, ClosedTradesSerializer, TradeHistorySerializer

class TradesTakenView(APIView):

    permission_classes = [IsAuthenticated]  

    def get(self, request):
        user = request.user
        print(user,">>>>>>>>")
        trades = TradesTaken.objects.filter(user=request.user)
        print(trades,"?>>>>>>>")
        serializer = TradesTakenSerializer(trades, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TradesTaken, TradeHistory
from .serializers import TradesTakenSerializer
from rest_framework_simplejwt.tokens import AccessToken


""" this is a tested ok for the first case scenario"""

# class TradeCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         # print(request.data)

#         # auth = request.headers.get('Authorization')

#         # token_str = auth.split(" ")[1]
        
#         # token = AccessToken(token_str)
#         # user_id = token["user_id"]
#         # print(user_id)

#         user = request.user
#         data = request.data

#         ticker = data.get("ticker")
#         trade_type = data.get("trade_type")
#         trade_price = data.get("avg_price")
#         quantity = data.get("quantity")
#         lot_size = data.get("lot_size", 1)

#         # Validate required fields
#         if not ticker or not trade_type or not trade_price or not quantity:
#             return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

#         # Validate trade type
#         if trade_type not in ["Buy", "Sell"]:
#             return Response({"error": "Invalid trade type. Use 'Buy' or 'Sell'."}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if trade with the given ticker exists for the user
#         existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).first()

    
        
#         if existing_trade:

            
#             return Response(
#                 {"message": "Trade with this ticker already exists for the user.", "data": TradesTakenSerializer(existing_trade).data},
#                 status=status.HTTP_200_OK,
#             )

       
#         serializer = TradesTakenSerializer(data=data)
#         if serializer.is_valid():
#             new_trade = serializer.save()

#             # Add to TradeHistory
#             TradeHistory.objects.create(
#                 trade=new_trade,
#                 trade_type=trade_type,
#                 quantity=quantity,
#                 trade_price=trade_price,
#             )

#             return Response({"message": "New trade created.", "data": serializer.data}, status=status.HTTP_201_CREATED)
#         else:
#             return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        if trade_type not in ["Buy", "Sell"]:
            return Response({"error": "Invalid trade type. Use 'Buy' or 'Sell'."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if an existing trade exists for this user and ticker
        existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).first()

        if existing_trade:
            # Handle different conditions based on `trade_type` and `trade_status`
            if trade_type == "Buy" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete":
                # Update the existing trade (Buy + Buy)
                existing_trade.avg_price = (
                    (existing_trade.avg_price * existing_trade.quantity + trade_price * quantity)
                    / (existing_trade.quantity + quantity)
                )
                existing_trade.quantity += quantity
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Buy",
                    quantity=quantity,
                    trade_price=trade_price,
                )

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
                
                profit_loss = (existing_trade.avg_price - trade_price) * quantity
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

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()

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
                # Handle sell logic for an existing buy trade (Sell + Buy)
                if quantity > existing_trade.quantity:
                    return Response(
                        {"error": "Cannot sell more than the available quantity."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                existing_trade.quantity -= quantity
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Sell",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                return Response(
                    {
                        "message": "Sell trade executed for existing buy trade.",
                        "data": TradesTakenSerializer(existing_trade).data,
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
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Sell",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                return Response(
                    {
                        "message": "Existing incomplete sell trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,
                )

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

            # Add to TradeHistory
            TradeHistory.objects.create(
                trade=new_trade,
                trade_type=trade_type,
                quantity=quantity,
                trade_price=trade_price,
            )

            return Response(
                {"message": "New trade created.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




# class TradeCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):

#         print(request.data)
#         user = request.user
#         data = request.data
        
#         print(user)
#         ticker = data.get("ticker")
#         trade_type = data.get("trade_type")
#         trade_price = data.get("avg_price")
#         quantity = data.get("quantity")
#         lot_size = data.get("lot_size", 1)
#         print(ticker,"kjdchfhjbjhcbhjekfbfefvgherf")
#         print(trade_type,"kjdchfhjbjhcbhjekfbfefvgherf")
#         print(trade_price,"kjdchfhjbjhcbhjekfbfefvgherf")
#         print(quantity,"kjdchfhjbjhcbhjekfbfefvgherf")
#         print(lot_size,"kjdchfhjbjhcbhjekfbfefvgherf")

#         if not ticker or not trade_type or not trade_price or not quantity:
#             return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

#         if trade_type not in ["Buy", "Sell"]:
#             return Response({"error": "Invalid trade type. Use 'buy' or 'sell'."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Check if a trade with the given ticker already exists for the user
#             existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker)
#             print(existing_trade,"test this trade")
            
#             if not existing_trade:
#                 # Create a new trade if it doesn't exist
#                 new_trade = TradesTaken.objects.create(
#                     user=user,
#                     ticker=ticker,
#                     trade_type=trade_type,
#                     quantity=quantity if trade_type == "buy" else 0,
#                     avg_price=trade_price if trade_type == "buy" else 0,
#                     trade_status="incomplete",
#                     lot_size=lot_size,
#                 )
#                 print(new_trade)
#                 # Add to TradeHistory
#                 TradeHistory.objects.create(
#                     trade=new_trade,
#                     trade_type=trade_type,
#                     quantity=quantity,
#                     trade_price=trade_price,
#                 )
#                 return Response({"message": "New trade created.", "data": TradesTakenSerializer(new_trade).data}, status=status.HTTP_201_CREATED)
#             else:
#                 # Update the existing trade
#                 if trade_type == "buy":
#                     if existing_trade.trade_status == "completed":
#                         return Response({"error": "Cannot buy for a completed trade."}, status=status.HTTP_400_BAD_REQUEST)
                    
#                     # Update average price and quantity
#                     total_invested = (existing_trade.avg_price * existing_trade.quantity) + (trade_price * quantity)
#                     total_quantity = existing_trade.quantity + quantity
#                     existing_trade.avg_price = total_invested / total_quantity
#                     existing_trade.quantity = total_quantity
#                     existing_trade.trade_status = "incomplete"
                
#                 elif trade_type == "sell":
#                     if existing_trade.quantity < quantity:
#                         return Response({"error": "Sell quantity exceeds available quantity."}, status=status.HTTP_400_BAD_REQUEST)
                    
#                     existing_trade.quantity -= quantity
#                     if existing_trade.quantity == 0:
#                         existing_trade.trade_status = "completed"
                
#                 existing_trade.save()

#                 # Add to TradeHistory
#                 TradeHistory.objects.create(
#                     trade=existing_trade,
#                     trade_type=trade_type,
#                     quantity=quantity,
#                     trade_price=trade_price,
#                 )
#                 return Response({"message": "Trade updated.", "data": TradesTakenSerializer(existing_trade).data}, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
