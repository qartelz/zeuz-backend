from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import TradeOrder,MarginLocked
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


"""tades history of all trades taken by the user"""

class UserTradesView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request):
        # Get all trades for the authenticated user
        trades = TradesTaken.objects.filter(user=request.user)

        # Serialize the trades
        serializer = TradesTakenSerializer(trades, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class TradeHistoryView(APIView):
    permission_classes = [IsAuthenticated]  # Optional: Restrict access to authenticated users

    def get(self, request, trade_id):
        try:
            # Get the TradesTaken object for the given trade_id
            trade = TradesTaken.objects.get(id=trade_id, user=request.user)

            # Get all related trade history for this trade
            trade_history = TradeHistory.objects.filter(trade=trade)

            # Serialize the trade history
            serializer = TradeHistorySerializer(trade_history, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except TradesTaken.DoesNotExist:
            return Response(
                {"error": "Trade not found or you do not have permission to access it."},
                status=status.HTTP_404_NOT_FOUND,
            )

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
        margin_required = data.get("margin_required")
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
            print(beetle_coins)
        except BeetleCoins.DoesNotExist:
            return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)

        # if beetle_coins.coins < invested_amount:
        #     return Response(
        #         {"error": "Insufficient Beetle Coins to execute the trade."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )
        """ this conditionn checks whtether the user has enough coin"""
        # checking whether the user has enount coins to trade
        try:
            margin =MarginLocked.objects.get(user = user)
            print(margin)
            
        except BeetleCoins.DoesNotExist:
            return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
            print("here")
            return Response(
                {"error": "You don't have enough coins to execute the trade."},
                status=status.HTTP_404_NOT_FOUND,
            )
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
                beetle_coins.coins-=invested_amount
                beetle_coins.used_coins+=invested_amount
                beetle_coins.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Buy",
                    quantity=quantity,
                    trade_price=trade_price,
                )
                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                existing_trade.invested_coin-=existing_trade.quantity*existing_trade.avg_price
                

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()
                invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                beetle_coins.coins+=invested_amount
                beetle_coins.used_coins-=(invested_amount-profit_loss)
                beetle_coins.save()

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
                existing_trade.invested_coin=existing_trade.quantity*existing_trade.avg_price
                # beetle_coins.coins+=profit_loss

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()
                beetle_coins.coins+=invested_amount
                beetle_coins.used_coins-=(invested_amount-profit_loss)
                beetle_coins.save()
                
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
                beetle_coins.coins-=invested_amount
                beetle_coins.used_coins+=invested_amount
                beetle_coins.save()

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
            elif trade_type == "Buy" or trade_type  == "Sell" and existing_trade.quantity == 0 and existing_trade.trade_status == "completed":
                print("here")
                # Create a new trade since the existing one is complete
                data["user"] = user.id  # Associate the new trade with the user
                serializer = TradesTakenSerializer(data=data)  # Use serializer to validate and create new trade data

                if serializer.is_valid():
                    new_trade = serializer.save()  # Save the new trade
                    print(f"New trade created: {new_trade}")

                    # Add the new trade to TradeHistory
                    TradeHistory.objects.create(
                        trade=new_trade,
                        trade_type=trade_type,
                        quantity=quantity,
                        trade_price=trade_price,
                    )

                    beetle_coins.coins-=invested_amount
                    beetle_coins.used_coins+=invested_amount
                    beetle_coins.save()

                    # Deduct invested coins for the new trade
                    # try:
                    #     beetle_coins.use_coins(invested_amount)
                    # except ValidationError as e:
                    #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                    return Response(
                        {
                            "message": "New trade created as the previous one was complete.",
                            "data": TradesTakenSerializer(new_trade).data,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # elif trade_type == "Buy" or trade_type  == "Sell" and existing_trade.quantity == 0 and existing_trade.trade_status == "completed":
            #     print("here")
            #     # Create a new trade since the existing one is complete
            #     data["user"] = user.id  # Associate the new trade with the user
            #     serializer = TradesTakenSerializer(data=data)  # Use serializer to validate and create new trade data

            #     if serializer.is_valid():
            #         new_trade = serializer.save()  # Save the new trade
            #         print(f"New trade created: {new_trade}")

            #         # Add the new trade to TradeHistory
            #         TradeHistory.objects.create(
            #             trade=new_trade,
            #             trade_type=trade_type,
            #             quantity=quantity,
            #             trade_price=trade_price,
            #         )

            #         # Deduct invested coins for the new trade
            #         try:
            #             beetle_coins.use_coins(invested_amount)
            #         except ValidationError as e:
            #             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            #         return Response(
            #             {
            #                 "message": "New trade created as the previous one was complete.",
            #                 "data": TradesTakenSerializer(new_trade).data,
            #             },
            #             status=status.HTTP_201_CREATED,
            #         )

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

            beetle_coins.coins-=invested_amount
            beetle_coins.used_coins+=invested_amount
            beetle_coins.save()
            # try:
            #     beetle_coins.use_coins(invested_amount)
            # except ValidationError as e:
            #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"message": "New trade created.......", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class FuturesCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        ticker = data.get("ticker")
        trade_type = data.get("trade_type")
        trade_price = data.get("avg_price")
        quantity = data.get("quantity")
        invested_amount = data.get("invested_coin")
        expiry_date =data.get("expiry_date")
        margin_required = data.get("margin_required")
        print(ticker,trade_type,trade_price,quantity,invested_amount)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        if trade_type not in ["Buy", "Sell"]:
            return Response({"error": "Invalid trade type. Use 'Buy' or 'Sell'."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if an existing trade exists for this user and ticker
        existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).order_by('-created_at').first()
        print(existing_trade)

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
        except BeetleCoins.DoesNotExist:
            return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)
        
        """ this conditionn checks whtether the user has enough coin"""
        # checking whether the user has enount coins to trade
        try:
            margin =MarginLocked.objects.get(user = user)
            print(margin)
            
        except BeetleCoins.DoesNotExist:
            return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)
        
        print(margin_required + margin.margin,beetle_coins.coins,beetle_coins.coins,invested_amount)
        if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
            print("here")
            return Response(
                {"error": "You don't have enough coins to execute the trade."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        
        if existing_trade:
            print("True")
            if trade_type == "Buy" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete" and existing_trade:
                print("here")
                # Update the existing trade (Buy + Buy)
                existing_trade.avg_price = (
                    (existing_trade.avg_price * existing_trade.quantity + trade_price * quantity)
                    / (existing_trade.quantity + quantity)
                )
                existing_trade.quantity += quantity
                existing_trade.invested_coin+=invested_amount
                existing_trade.save()

                beetle_coins.coins-=invested_amount
                beetle_coins.used_coins+=invested_amount
                beetle_coins.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Buy",
                    quantity=quantity,
                    trade_price=trade_price,
                )
                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                    existing_trade.invested_coin=existing_trade.quantity*existing_trade.avg_price

                    # If the trade is now fully completed, mark it as complete
                    if existing_trade.quantity == 0:
                        existing_trade.trade_status = "complete"

                    # Save the updated trade state
                    existing_trade.save()
                    beetle_coins.coins+=invested_amount
                    beetle_coins.used_coins-=(invested_amount-profit_loss)
                    beetle_coins.save()
                    # invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                    

                    # Check and deduct Beetle Coins before proceeding
                    # try:
                    #     beetle_coins.use_coins(invested_amount)
                    # except ValidationError as e:
                    #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                    

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
                existing_trade.invested_coin=existing_trade.quantity*existing_trade.avg_price
                beetle_coins.coins+=profit_loss

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()
                beetle_coins.coins+=invested_amount
                beetle_coins.used_coins-=(invested_amount-profit_loss)
                beetle_coins.save()
                
                # invested_amount = (existing_trade.avg_price * quantity) + profit_loss

                # Check and deduct Beetle Coins before proceeding
                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                

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
                existing_trade.invested_coin=existing_trade.quantity*existing_trade.avg_price
                existing_trade.save()
                beetle_coins.coins+=invested_amount
                beetle_coins.used_coins-=invested_amount
                beetle_coins.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Sell",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                return Response(
                    {
                        "message": "Existing incomplete sell trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,
                )
            elif trade_type == "Buy" or trade_type  == "Sell" and existing_trade.quantity == 0 and existing_trade.trade_status == "completed":
                print("here")
                # Create a new trade since the existing one is complete
                data["user"] = user.id  # Associate the new trade with the user
                serializer = TradesTakenSerializer(data=data)  # Use serializer to validate and create new trade data

                if serializer.is_valid():
                    new_trade = serializer.save()  # Save the new trade
                    print(f"New trade created: {new_trade}")

                    # Add the new trade to TradeHistory
                    TradeHistory.objects.create(
                        trade=new_trade,
                        trade_type=trade_type,
                        quantity=quantity,
                        trade_price=trade_price,
                    )
                    beetle_coins.coins-=invested_amount
                    beetle_coins.used_coins+=invested_amount
                    beetle_coins.save()

                    # Deduct invested coins for the new trade
                    # try:
                    #     beetle_coins.use_coins(invested_amount)
                    # except ValidationError as e:
                    #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                    return Response(
                        {
                            "message": "New trade created as the previous one was complete.",
                            "data": TradesTakenSerializer(new_trade).data,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response(
                    {"error": "Invalid trade update scenario."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            
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
            beetle_coins.coins-=invested_amount
            beetle_coins.used_coins+=invested_amount
            beetle_coins.save()
            # try:
            #     beetle_coins.use_coins(invested_amount)
            # except ValidationError as e:
            #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"message": "New trade created.......", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




class OptionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        ticker = data.get("ticker")
        trade_type = data.get("trade_type")
        trade_price = data.get("avg_price")
        quantity = data.get("quantity")
        invested_amount = data.get("invested_coin")
        expiry_date =data.get("expiry_date")
        margin_required = data.get("margin_required")
        print(ticker,trade_type,trade_price,quantity,invested_amount)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        if trade_type not in ["Buy", "Sell"]:
            return Response({"error": "Invalid trade type. Use 'Buy' or 'Sell'."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if an existing trade exists for this user and ticker
       

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
            
        except BeetleCoins.DoesNotExist:
            return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)
        

        """ this conditionn checks whtether the user has enough coin"""
        # checking whether the user has enount coins to trade
        try:
            margin =MarginLocked.objects.get(user = user)
            print(margin)
            
        except BeetleCoins.DoesNotExist:
            return Response({"error": "User's Beetle Coins record not found."}, status=status.HTTP_404_NOT_FOUND)
        
        print(margin_required + margin.margin,beetle_coins.coins,beetle_coins.coins,invested_amount)
        if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
            print("here")
            return Response(
                {"error": "You don't have enough coins to execute the trade."},
                status=status.HTTP_404_NOT_FOUND,
            )
    

        existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).order_by('-created_at').first()
        print(existing_trade)

        if existing_trade:
            print("True")
            if trade_type == "Buy" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete" and existing_trade:
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
                beetle_coins.coins-=invested_amount
                beetle_coins.used_coins+=invested_amount
                beetle_coins.save()
                
                return Response(
                    {
                        "message": "Existing incomplete buy trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,
                )
            
            # elif trade_type == "Buy" and existing_trade.trade_type == "Sell" and existing_trade.trade_status == "incomplete":
            # # Validate the requested quantity
            #         if quantity > existing_trade.quantity:
            #             return Response(
            #                 {"error": "Cannot buy more than the available sell quantity."},
            #                 status=status.HTTP_400_BAD_REQUEST,
            #             )
                    
            #         profit_loss = (float(existing_trade.avg_price) -float(trade_price)) * quantity

            #         # Calculate profit/loss for this transaction (Short Selling Scenario)

            #         print(profit_loss)
                    
            #         ClosedTrades.objects.create(
            #         trade=existing_trade,
            #         sell_quantity=quantity,
            #         sell_price=trade_price,
            #         profit_loss=profit_loss,
            #     )

            #         # Calculate profit/loss for this transaction

            #         # Record the Buy in TradeHistory
            #         TradeHistory.objects.create(
            #             trade=existing_trade,
            #             trade_type="Buy",
            #             quantity=quantity,
            #             trade_price=trade_price,
            #         )

            #         # Record the Sell in ClosedTrades (always append)
                    
            #         # Adjust the existing trade quantity
            #         existing_trade.quantity -= quantity
            #         existing_trade.invested_coin=existing_trade.quantity*existing_trade.avg_price

            #         # If the trade is now fully completed, mark it as complete
            #         if existing_trade.quantity == 0:
            #             existing_trade.trade_status = "complete"

            #         # Save the updated trade state
            #         existing_trade.save()
            #         invested_amount = (existing_trade.avg_price * quantity) + profit_loss
            #         beetle_coins.coins+=invested_amount
            #         beetle_coins.used_coins-=(invested_amount-profit_loss)
            #         beetle_coins.save()

            #         # Check and deduct Beetle Coins before proceeding
                    
                    

            #         # Build response message
            #         message = (
            #             "Trade completed and recorded." if existing_trade.trade_status == "complete"
            #             else "Partial trade executed and recorded."
            #         )

            #         return Response(
            #             {
            #                 "message": message,
            #                 "trade_history": TradeHistory.objects.filter(trade=existing_trade).values(),
            #                 "closed_trades": ClosedTrades.objects.filter(trade=existing_trade).values(),
            #             },
            #             status=status.HTTP_200_OK,
            #         )
            elif trade_type == "Buy" and existing_trade.trade_type== "Sell" and existing_trade.trade_status == "incomplete":
                if quantity > existing_trade.quantity:
        # Calculate and execute the available quantity in the existing trade
                    # available_quantity = existing_trade.quantity
                    profit_loss = (float(existing_trade.avg_price) - float(trade_price)) * quantity
                    avg_margin = existing_trade.margin_required/existing_trade.quantity

                    print(f"Executing available quantity: {quantity}, Profit/Loss: {profit_loss}")

                    # Record the available quantity as a ClosedTrade
                    ClosedTrades.objects.create(
                        trade=existing_trade,
                        sell_quantity=quantity,
                        sell_price=trade_price,
                        profit_loss=profit_loss,
                    )

                    # Record the Buy for the available quantity in TradeHistory
                    TradeHistory.objects.create(
                        trade=existing_trade,
                        trade_type="Buy",
                        quantity=quantity,
                        trade_price=trade_price,
                    )

                    # Adjust the existing trade's remaining quantity and mark as complete
                    existing_trade.quantity -= quantity
                    existing_trade.invested_coin = existing_trade.quantity * existing_trade.avg_price
                    existing_trade.trade_status = "complete" if existing_trade.quantity == 0 else "incomplete"
                    
                    existing_trade.margin_required = avg_margin*existing_trade.quantity
                    existing_trade.save()

                    # Update Beetle Coins for the available quantity
                    invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= (invested_amount - profit_loss)
                    beetle_coins.save()
                    

                    # Handle the remaining quantity by creating a new trade
                    remaining_quantity = existing_trade.quantity
                    print(f"Creating a new trade for remaining quantity: {remaining_quantity}")

                    new_trade_data = {
                        "user": existing_trade.user,
                        "trade_type": "Buy",
                        "quantity": remaining_quantity,
                        "avg_price": trade_price,
                        "invested_coin": remaining_quantity * trade_price,
                        "trade_status": "incomplete",
                    }
                    new_trade = TradesTaken.objects.create(**new_trade_data)

                    # Record the new trade in TradeHistory
                    TradeHistory.objects.create(
                        trade=new_trade,
                        trade_type="Buy",
                        quantity=remaining_quantity,
                        trade_price=trade_price,
                    )

                    # Deduct Beetle Coins for the new trade
                    beetle_coins.coins -= new_trade_data["invested_coin"]
                    beetle_coins.used_coins += new_trade_data["invested_coin"]
                    beetle_coins.save()
                    


                    return Response(
                        {
                            "message": "Partial trade executed and remaining quantity recorded as a new trade.",
                            "existing_trade": {
                                "trade_status": existing_trade.trade_status,
                                "remaining_quantity": existing_trade.quantity,
                            },
                            "new_trade": {
                                "id": new_trade.id,
                                "quantity": remaining_quantity,
                                "invested_coin": new_trade.invested_coin,
                            },
                            "updated_beetle_coins": {
                                "total_coins": beetle_coins.coins,
                                "used_coins": beetle_coins.used_coins,
                            },
                            "trade_history": list(
                                TradeHistory.objects.filter(
                                    trade__in=[existing_trade, new_trade]
                                ).values()
                            ),
                            "closed_trades": list(
                                ClosedTrades.objects.filter(trade=existing_trade).values()
                            ),
                        },
                        status=status.HTTP_200_OK,
                    )

                else:
                    # Execute normally if quantity <= existing_trade.quantity
                    profit_loss = (float(existing_trade.avg_price) - float(trade_price)) * quantity

                    print(f"Executing trade for full quantity: {quantity}, Profit/Loss: {profit_loss}")

                    # Record the full quantity as a ClosedTrade
                    ClosedTrades.objects.create(
                        trade=existing_trade,
                        sell_quantity=quantity,
                        sell_price=trade_price,
                        profit_loss=profit_loss,
                    )

                    # Record the Buy in TradeHistory
                    TradeHistory.objects.create(
                        trade=existing_trade,
                        trade_type="Buy",
                        quantity=quantity,
                        trade_price=trade_price,
                    )

                    # Adjust the existing trade's remaining quantity and invested coins
                    existing_trade.quantity -= quantity
                    existing_trade.invested_coin = existing_trade.quantity * existing_trade.avg_price
                    if existing_trade.quantity == 0:
                        existing_trade.trade_status = "complete"
                    existing_trade.save()

                    # Update Beetle Coins
                    invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= (invested_amount - profit_loss)
                    beetle_coins.save()

                    return Response(
                        {
                            "message": "Trade completed and recorded.",
                            "trade_status": existing_trade.trade_status,
                            "remaining_quantity": existing_trade.quantity,
                            "profit_loss": profit_loss,
                            "updated_beetle_coins": {
                                "total_coins": beetle_coins.coins,
                                "used_coins": beetle_coins.used_coins,
                            },
                            "trade_history": list(
                                TradeHistory.objects.filter(trade=existing_trade).values()
                            ),
                            "closed_trades": list(
                                ClosedTrades.objects.filter(trade=existing_trade).values()
                            ),
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
                    # existing_trade.invested_coin-=invested_amount
                    existing_trade.invested_coin=existing_trade.quantity*existing_trade.avg_price
                    beetle_coins.coins+=profit_loss

                    # If the trade is now fully completed, mark it as complete
                    if existing_trade.quantity == 0:
                        existing_trade.trade_status = "complete"

                    # Save the updated trade state
                    existing_trade.save()
                    
                    invested_amount = (existing_trade.avg_price * quantity) + profit_loss

                    # Check and deduct Beetle Coins before proceeding
                    beetle_coins.coins+=invested_amount
                    beetle_coins.used_coins-=(invested_amount-profit_loss)
                    beetle_coins.save()
                    

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

                beetle_coins.coins-=invested_amount
                beetle_coins.used_coins+=invested_amount
                beetle_coins.save()

                return Response(
                    {
                        "message": "Existing incomplete sell trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,


                )
            
            # this trade is sucesfully completed checking new conditions

            # elif trade_type == "Buy" or trade_type  == "Sell" and existing_trade.quantity == 0 and existing_trade.trade_status == "completed":
            #     print("here")
            #     # Create a new trade since the existing one is complete
            #     data["user"] = user.id  # Associate the new trade with the user
            #     serializer = TradesTakenSerializer(data=data)  # Use serializer to validate and create new trade data

            #     if serializer.is_valid():
            #         new_trade = serializer.save()  # Save the new trade
            #         print(f"New trade created: {new_trade}")

            #         # Add the new trade to TradeHistory
            #         TradeHistory.objects.create(
            #             trade=new_trade,
            #             trade_type=trade_type,
            #             quantity=quantity,
            #             trade_price=trade_price,
            #         )
            #         print(data["margin_required"])
            #         margin.margin+=data["margin_required"]
            #         margin.save()

            #         # Deduct invested coins for the new trade
            #         beetle_coins.coins-=invested_amount
            #         beetle_coins.used_coins+=invested_amount
            #         beetle_coins.save()
            #         print(data["margin_required"])
            #         margin.margin+=data["margin_required"]
            #         margin.save()

            #         return Response(
            #             {
            #                 "message": "New trade created as the previous one was complete.",
            #                 "data": TradesTakenSerializer(new_trade).data,
            #             },
            #             status=status.HTTP_201_CREATED,
            #     )
            #     else:
            #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ########################################################################


            elif trade_type == "Buy" and existing_trade.trade_type == "Sell" and existing_trade.trade_status == "incomplete":
                # Check if Buy quantity is greater than Sell quantity
                if quantity > existing_trade.quantity:
                    # Step 1: Execute the available Sell quantity in the existing trade
                    available_quantity = existing_trade.quantity
                    profit_loss = (float(existing_trade.avg_price) - float(trade_price)) * available_quantity
                    avg_margin = existing_trade.margin_required / existing_trade.quantity

                    print(f"Executing available Sell quantity: {available_quantity}, Profit/Loss: {profit_loss}")

                    # Record the Sell quantity as a ClosedTrade
                    ClosedTrades.objects.create(
                        trade=existing_trade,
                        sell_quantity=available_quantity,
                        sell_price=trade_price,
                        profit_loss=profit_loss,
                    )

                    # Record the executed Buy in TradeHistory
                    TradeHistory.objects.create(
                        trade=existing_trade,
                        trade_type="Buy",
                        quantity=available_quantity,
                        trade_price=trade_price,
                    )

                    # Update the existing trade's remaining quantity and margin
                    existing_trade.quantity -= available_quantity
                    existing_trade.invested_coin = existing_trade.quantity * existing_trade.avg_price
                    existing_trade.margin_required = avg_margin * existing_trade.quantity
                    existing_trade.trade_status = "complete" if existing_trade.quantity == 0 else "incomplete"
                    existing_trade.save()

                    # Update Beetle Coins for the executed quantity
                    invested_amount = (existing_trade.avg_price * available_quantity) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= (invested_amount - profit_loss)
                    beetle_coins.save()

                    # Step 2: Handle the remaining Buy quantity by creating a new trade
                    remaining_quantity = quantity - available_quantity
                    print(f"Creating a new trade for remaining Buy quantity: {remaining_quantity}")

                    new_trade_data = {
                        "user": existing_trade.user,
                        "trade_type": "Buy",
                        "quantity": remaining_quantity,
                        "avg_price": trade_price,
                        "invested_coin": remaining_quantity * trade_price,
                        "trade_status": "incomplete",
                    }
                    new_trade = TradesTaken.objects.create(**new_trade_data)

                    # Record the new trade in TradeHistory
                    TradeHistory.objects.create(
                        trade=new_trade,
                        trade_type="Buy",
                        quantity=remaining_quantity,
                        trade_price=trade_price,
                    )

                    # Deduct Beetle Coins for the new trade
                    beetle_coins.coins -= new_trade_data["invested_coin"]
                    beetle_coins.used_coins += new_trade_data["invested_coin"]
                    beetle_coins.save()

                    return Response(
                        {
                            "message": "Partial Sell executed and remaining Buy quantity recorded as a new trade.",
                            "existing_trade": {
                                "trade_status": existing_trade.trade_status,
                                "remaining_quantity": existing_trade.quantity,
                            },
                            "new_trade": {
                                "id": new_trade.id,
                                "quantity": remaining_quantity,
                                "invested_coin": new_trade.invested_coin,
                            },
                            "updated_beetle_coins": {
                                "total_coins": beetle_coins.coins,
                                "used_coins": beetle_coins.used_coins,
                            },
                            "trade_history": list(
                                TradeHistory.objects.filter(
                                    trade__in=[existing_trade, new_trade]
                                ).values()
                            ),
                            "closed_trades": list(
                                ClosedTrades.objects.filter(trade=existing_trade).values()
                            ),
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    # Execute normally if Buy quantity <= Sell quantity
                    profit_loss = (float(existing_trade.avg_price) - float(trade_price)) * quantity
                    avg_margin = existing_trade.margin_required / existing_trade.quantity

                    print(f"Executing Buy quantity: {quantity}, Profit/Loss: {profit_loss}")

                    # Record the Sell quantity as a ClosedTrade
                    ClosedTrades.objects.create(
                        trade=existing_trade,
                        sell_quantity=quantity,
                        sell_price=trade_price,
                        profit_loss=profit_loss,
                    )

                    # Record the executed Buy in TradeHistory
                    TradeHistory.objects.create(
                        trade=existing_trade,
                        trade_type="Buy",
                        quantity=quantity,
                        trade_price=trade_price,
                    )

                    # Update the existing trade's remaining quantity and margin
                    existing_trade.quantity -= quantity
                    existing_trade.invested_coin = existing_trade.quantity * existing_trade.avg_price
                    existing_trade.margin_required = avg_margin * existing_trade.quantity
                    existing_trade.trade_status = "complete" if existing_trade.quantity == 0 else "incomplete"
                    existing_trade.save()

                    # Update Beetle Coins for the executed quantity
                    invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= (invested_amount - profit_loss)
                    beetle_coins.save()

                    return Response(
                        {
                            "message": "Sell executed and Buy quantity recorded.",
                            "trade_status": existing_trade.trade_status,
                            "remaining_quantity": existing_trade.quantity,
                            "profit_loss": profit_loss,
                            "updated_beetle_coins": {
                                "total_coins": beetle_coins.coins,
                                "used_coins": beetle_coins.used_coins,
                            },
                            "trade_history": list(
                                TradeHistory.objects.filter(trade=existing_trade).values()
                            ),
                            "closed_trades": list(
                                ClosedTrades.objects.filter(trade=existing_trade).values()
                            ),
                        },
                        status=status.HTTP_200_OK,
                    )


        ###################################################################
        else:
            return Response(
                {"error": "Invalid trade update scenario."},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        data["user"] = user.id  # Add user to the data
        serializer = TradesTakenSerializer(data=data)

        if serializer.is_valid():
            option_type = data.get("option_type")
            
            
            if option_type == "CE" or option_type == "PE" and trade_type  == "Sell" :
               
                print("lets work on Sell cases my boy")
                new_trade = serializer.save()
                print(new_trade)
                TradeHistory.objects.create(
                    trade=new_trade,
                    trade_type=data["trade_type"],
                    quantity=data["quantity"],
                    trade_price=data["avg_price"],  
                )

                beetle_coins.coins -= data["invested_coin"]
                beetle_coins.used_coins += data["invested_coin"]
                beetle_coins.save()

                # margin.+=data["margin_required"]
                print(data["margin_required"])
                margin.margin+=data["margin_required"]
                margin.save()

                return Response(
                    {"message": "New trade created.......", "data": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
                
                
            elif option_type == "PE" or option_type == "CE" and trade_type == "Buy":
                
                print("Its working on well with buY WITH PE and CE")
                new_trade = serializer.save()
                print(new_trade)


                TradeHistory.objects.create(
                    trade=new_trade,
                    trade_type=data["trade_type"],
                    quantity=data["quantity"],
                    trade_price=data["avg_price"],  
                )

                
                beetle_coins.coins -= data["invested_coin"]
                beetle_coins.used_coins += data["invested_coin"]
                beetle_coins.save()

                return Response(
                    {"message": "New trade created.......", "data": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
                
                
            # else:
                
            #     print("No valid option_type provided or not applicable (e.g., FUT).")

            
            
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


        """this is the actual working  trade which i have created and is workig"""
        # data["user"] = user.id  # Add user to the data
        # serializer = TradesTakenSerializer(data=data)

        # if serializer.is_valid():
            
        #     new_trade = serializer.save()
        #     print(new_trade)

        #     # Add to TradeHistory
        #     TradeHistory.objects.create(
        #         trade=new_trade,
        #         trade_type=trade_type,
        #         quantity=quantity,
        #         trade_price=trade_price,
        #     )
        #     beetle_coins.coins-=invested_amount
        #     beetle_coins.used_coins+=invested_amount
        #     beetle_coins.save()

        #     return Response(
        #         {"message": "New trade created.......", "data": serializer.data},
        #         status=status.HTTP_201_CREATED,
        #     )
        # else:
        #     return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)










# class UserTradesView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         # Get the authenticated user
#         user = request.user

#         # Query all trades taken by this user
#         user_trades = TradesTaken.objects.filter(user=user)

#         # Serialize the data
#         serializer = TradesTakenSerializer(user_trades, many=True)

#         # Return the response
#         return Response(
#             {"message": "User trades retrieved successfully.", "data": serializer.data},
#             status=status.HTTP_200_OK
#         )

