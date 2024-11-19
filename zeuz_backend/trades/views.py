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


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from .models import TradesTaken, TradeHistory, ClosedTrades
# from .serializers import TradesTakenSerializer

# class TradeCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         data = request.data

#         # Extract data from request
#         ticker = data.get("ticker")
#         trade_type = data.get("trade_type")
#         trade_price = float(data.get("avg_price", 0))
#         quantity = int(data.get("quantity", 0))

#         # Validate required fields
#         if not ticker or not trade_type or trade_price <= 0 or quantity <= 0:
#             return Response({"error": "Missing or invalid required fields."}, status=status.HTTP_400_BAD_REQUEST)

#         if trade_type not in ["Buy", "Sell"]:
#             return Response({"error": "Invalid trade type. Use 'Buy' or 'Sell'."}, status=status.HTTP_400_BAD_REQUEST)

#         # Calculate the invested amount
#         invested_amount = trade_price * quantity

#         # Check user's Beetle Coins
#         try:
#             beetle_coins = BeetleCoins.objects.get(user=user)
#         except BeetleCoins.DoesNotExist:
#             return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)

#         if beetle_coins.coins < invested_amount:
#             return Response(
#                 {"error": "Insufficient Beetle Coins to execute the trade."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Deduct the coins for the trade
#         try:
#             beetle_coins.use_coins(invested_amount)
#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#         # Proceed with trade logic
#         existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).first()

#         if existing_trade:
#             if trade_type == "Buy" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete":
#                 # Update the existing trade (Buy + Buy)
#                 existing_trade.avg_price = (
#                     (existing_trade.avg_price * existing_trade.quantity + trade_price * quantity)
#                     / (existing_trade.quantity + quantity)
#                 )
#                 existing_trade.quantity += quantity
#                 existing_trade.save()

#                 TradeHistory.objects.create(
#                     trade=existing_trade,
#                     trade_type="Buy",
#                     quantity=quantity,
#                     trade_price=trade_price,
#                 )

#                 return Response(
#                     {
#                         "message": "Existing incomplete buy trade updated.",
#                         "data": TradesTakenSerializer(existing_trade).data,
#                     },
#                     status=status.HTTP_200_OK,
#                 )

#             elif trade_type == "Buy" and existing_trade.trade_type == "Sell" and existing_trade.trade_status == "incomplete":
#                 if quantity > existing_trade.quantity:
#                     beetle_coins.return_coins(invested_amount)  # Refund coins
#                     return Response(
#                         {"error": "Cannot buy more than the available sell quantity."},
#                         status=status.HTTP_400_BAD_REQUEST,
#                     )

#                 profit_loss = (existing_trade.avg_price - trade_price) * quantity

#                 ClosedTrades.objects.create(
#                     trade=existing_trade,
#                     sell_quantity=quantity,
#                     sell_price=trade_price,
#                     profit_loss=profit_loss,
#                 )

#                 TradeHistory.objects.create(
#                     trade=existing_trade,
#                     trade_type="Buy",
#                     quantity=quantity,
#                     trade_price=trade_price,
#                 )

#                 existing_trade.quantity -= quantity
#                 if existing_trade.quantity == 0:
#                     existing_trade.trade_status = "complete"

#                 existing_trade.save()

#                 message = (
#                     "Trade completed and recorded."
#                     if existing_trade.trade_status == "complete"
#                     else "Partial trade executed and recorded."
#                 )

#                 return Response(
#                     {
#                         "message": message,
#                         "trade_history": TradeHistory.objects.filter(trade=existing_trade).values(),
#                         "closed_trades": ClosedTrades.objects.filter(trade=existing_trade).values(),
#                     },
#                     status=status.HTTP_200_OK,
#                 )

#         # Handle new trade creation
#         new_trade = TradesTaken.objects.create(
#             user=user,
#             ticker=ticker,
#             trade_type=trade_type,
#             avg_price=trade_price,
#             quantity=quantity,
#             trade_status="incomplete",
#         )

#         TradeHistory.objects.create(
#             trade=new_trade,
#             trade_type=trade_type,
#             quantity=quantity,
#             trade_price=trade_price,
#         )

        # return Response(
        #     {
        #         "message": "New trade created successfully.",
        #         "data": TradesTakenSerializer(new_trade).data,
        #     },
        #     status=status.HTTP_201_CREATED,
        # )



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
