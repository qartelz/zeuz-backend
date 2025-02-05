from datetime import datetime
from rest_framework.views import APIView
from decimal import Decimal
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import TradeOrder, MarginLocked
from account.models import BeetleCoins
from .serializers import TradeOrderSerializer
from account.models import BeetleCoins
from rest_framework.permissions import IsAuthenticated

from rest_framework import status


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TradesTaken, ClosedTrades, TradeHistory, LimitOrder
from .serializers import (
    TradesTakenSerializer,
    ClosedTradesSerializer,
    TradeHistorySerializer,
    LimitOrderSerializer,
)


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
    permission_classes = [
        IsAuthenticated
    ]  # Optional: Restrict access to authenticated users

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
                {
                    "error": "Trade not found or you do not have permission to access it."
                },
                status=status.HTTP_404_NOT_FOUND,
            )


"""closed trades view"""


class ClosedTradesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        closed_trades = ClosedTrades.objects.filter(trade__user=user)
        serializer = ClosedTradesSerializer(closed_trades, many=True)
        return Response(serializer.data)


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
        product_type = data.get("product_type")
        print(ticker, trade_type, trade_price, quantity, invested_amount)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trade_type not in ["Buy", "Sell"]:
            return Response(
                {"error": "Invalid trade type. Use 'Buy' or 'Sell'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if an existing trade exists for this user and ticker
        # existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).first()
        existing_trade = (
            TradesTaken.objects.filter(
                user=user, ticker=ticker, product_type=product_type
            )
            .order_by("-created_at")
            .first()
        )
        print(existing_trade)

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
            print(beetle_coins)
        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # if beetle_coins.coins < invested_amount:
        #     return Response(
        #         {"error": "Insufficient Beetle Coins to execute the trade."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )
        """ this conditionn checks whtether the user has enough coin"""
        # checking whether the user has enount coins to trade
        try:
            margin = MarginLocked.objects.get(user=user)
            print(margin)

        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
        #     print("here")
        #     return Response(
        #         {"error": "You don't have enough coins to execute the trade."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )

        # if beetle_coins.coins <= invested_amount:
        #     print("here")
        #     return Response(
        #         {"error": "You don't have enough coins to execute the trade."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )
        if beetle_coins.coins <= invested_amount:
            if existing_trade and (
                (trade_type == "Sell" and existing_trade.trade_type == "Sell")
                or (trade_type == "Buy" and existing_trade.trade_type == "Buy")
            ):
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            elif not existing_trade:
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        # if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
        #     print(f"Margin required: {margin_required}, Margin: {margin.margin}, Coins: {beetle_coins.coins}, Invested amount: {invested_amount}")
        #     return Response(
        #         {"error": "You don't have enough coins to execute the trade."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )
        if existing_trade:
            print("Already")
            # Handle different conditions based on `trade_type` and `trade_status`
            print(trade_type, existing_trade.trade_type, existing_trade.trade_status)
            if (
                trade_type == "Buy"
                and existing_trade.trade_type == "Buy"
                and existing_trade.trade_status == "incomplete"
            ):
                print("here")
                # Update the existing trade (Buy + Buy)
                existing_trade.avg_price = (
                    existing_trade.avg_price * existing_trade.quantity
                    + float(trade_price) * quantity
                ) / (existing_trade.quantity + quantity)
                existing_trade.quantity += quantity
                existing_trade.invested_coin += invested_amount

                existing_trade.save()

                beetle_coins.coins -= Decimal(invested_amount)
                beetle_coins.used_coins += Decimal(invested_amount)
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

            elif (
                trade_type == "Buy"
                and existing_trade.trade_type == "Sell"
                and existing_trade.trade_status == "incomplete"
            ):
                # Validate the requested quantity
                if quantity > existing_trade.quantity:
                    return Response(
                        {"error": "Cannot buy more than the available sell quantity."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                profit_loss = (
                    float(existing_trade.avg_price) - float(trade_price)
                ) * quantity

                # Calculate profit/loss for this transaction (Short Selling Scenario)

                print(profit_loss)

                ClosedTrades.objects.create(
                    trade=existing_trade,
                    product_type=existing_trade.product_type,
                    sell_quantity=quantity,
                    avg_price=existing_trade.avg_price,
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
                existing_trade.invested_coin -= (
                    existing_trade.quantity * existing_trade.avg_price
                )

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()
                invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                beetle_coins.coins += Decimal(invested_amount)
                beetle_coins.used_coins -= Decimal(invested_amount - profit_loss)
                beetle_coins.save()

                # Check and deduct Beetle Coins before proceeding
                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                # Build response message
                message = (
                    "Trade completed and recorded."
                    if existing_trade.trade_status == "complete"
                    else "Partial trade executed and recorded."
                )

                return Response(
                    {
                        "message": message,
                        "trade_history": TradeHistory.objects.filter(
                            trade=existing_trade
                        ).values(),
                        "closed_trades": ClosedTrades.objects.filter(
                            trade=existing_trade
                        ).values(),
                    },
                    status=status.HTTP_200_OK,
                )

            elif (
                trade_type == "Sell"
                and existing_trade.trade_type == "Buy"
                and existing_trade.trade_status == "incomplete"
            ):

                # Validate the requested quantity
                if quantity > existing_trade.quantity:
                    return Response(
                        {"error": "Cannot sell more than the available buy quantity."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Calculate profit/loss for this transaction (Buy + Sell Scenario)
                profit_loss = (
                    float(trade_price) - float(existing_trade.avg_price)
                ) * quantity
                print(profit_loss)

                # Record the Sell in ClosedTrades
                ClosedTrades.objects.create(
                    trade=existing_trade,
                    product_type=existing_trade.product_type,
                    sell_quantity=quantity,
                    avg_price=existing_trade.avg_price,
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
                existing_trade.invested_coin = (
                    existing_trade.quantity * existing_trade.avg_price
                )
                # beetle_coins.coins+=profit_loss

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()
                beetle_coins.coins += Decimal(invested_amount)
                # beetle_coins.coins+=invested_amount
                # test this scenario
                print(beetle_coins.coins)

                beetle_coins.used_coins -= Decimal(invested_amount - profit_loss)
                beetle_coins.save()

                # commented for testing the invested coin not working properly

                # invested_amount = (existing_trade.avg_price * quantity) + profit_loss

                # Check and deduct Beetle Coins before proceeding
                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                # Build response message
                message = (
                    "Trade completed and recorded."
                    if existing_trade.trade_status == "complete"
                    else "Partial trade executed and recorded."
                )

                return Response(
                    {
                        "message": message,
                        "trade_history": TradeHistory.objects.filter(
                            trade=existing_trade
                        ).values(),
                        "closed_trades": ClosedTrades.objects.filter(
                            trade=existing_trade
                        ).values(),
                    },
                    status=status.HTTP_200_OK,
                )

            elif (
                trade_type == "Sell"
                and existing_trade.trade_type == "Sell"
                and existing_trade.trade_status == "incomplete"
            ):
                # Update the existing sell trade (Sell + Sell)
                existing_trade.avg_price = (
                    existing_trade.avg_price * existing_trade.quantity
                    + trade_price * quantity
                ) / (existing_trade.quantity + quantity)
                existing_trade.quantity += quantity
                existing_trade.invested_coin += invested_amount
                existing_trade.save()
                # beetle_coins.coins -= invested_amount
                # beetle_coins.used_coins += invested_amount
                # beetle_coins.save()
                beetle_coins.coins -= Decimal(str(invested_amount))  # Convert float to Decimal
                beetle_coins.used_coins += Decimal(str(invested_amount))
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
            elif (
                trade_type == "Buy"
                or trade_type == "Sell"
                and existing_trade.quantity == 0
                and existing_trade.trade_status == "completed"
            ):
                print("here")
                # Create a new trade since the existing one is complete
                data["user"] = user.id  # Associate the new trade with the user
                serializer = TradesTakenSerializer(
                    data=data
                )  # Use serializer to validate and create new trade data

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

                    beetle_coins.coins -= Decimal(invested_amount)
                    beetle_coins.used_coins += Decimal(invested_amount)
                    beetle_coins.save()

                    # beetle_coins.coins-=invested_amount
                    # beetle_coins.used_coins+=invested_amount
                    # beetle_coins.save()

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
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )


            else:
                return Response(
                    {"error": "Invalid trade update scenario."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # If no existing trade, create a new one
        # data["user"] = user.id  # Add user to the data
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

            beetle_coins.coins -= Decimal(invested_amount)
            beetle_coins.used_coins += Decimal(invested_amount)
            beetle_coins.save()

            # beetle_coins.coins-=invested_amount

            # beetle_coins.used_coins+=invested_amount
            # beetle_coins.save()
            # try:
            #     beetle_coins.use_coins(invested_amount)
            # except ValidationError as e:
            #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"message": "New trade created.......", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )


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
        expiry_date = data.get("expiry_date")
        margin_required = data.get("margin_required")
        product_type = data.get("product_type")
        prctype = data.get("prctype")
        print(ticker, trade_type, trade_price, quantity, product_type)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trade_type not in ["Buy", "Sell"]:
            return Response(
                {"error": "Invalid trade type. Use 'Buy' or 'Sell'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if an existing trade exists for this user and ticker
        existing_trade = (
            TradesTaken.objects.filter(
                user=user, ticker=ticker, product_type=product_type
            )
            .order_by("-created_at")
            .first()
        )
        print(existing_trade)

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        """ this conditionn checks whtether the user has enough coin"""

        # checking whether the user has enount coins to trade
        try:
            margin = MarginLocked.objects.get(user=user)
            print(margin)

        except MarginLocked.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        print(
            # margin_required + margin.margin,
            beetle_coins.coins,
            beetle_coins.coins,
            invested_amount,
        )
        # if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
        # print("here")
        # return Response(
        #     {"error": "You don't have enough coins to execute the trade."},
        #     status=status.HTTP_404_NOT_FOUND,
        # )
        """this is tested"""

        # if (beetle_coins.coins <= invested_amount) and (trade_type == "Sell" and existing_trade.trade_type == "Buy"):
        #     print("here")
        #     return Response(
        #         {"error": "You don't have enough coins to execute the trade."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )

        if beetle_coins.coins <= invested_amount:
            if existing_trade and (
                (trade_type == "Sell" and existing_trade.trade_type == "Sell")
                or (trade_type == "Buy" and existing_trade.trade_type == "Buy")
            ):
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            
            elif not existing_trade and (trade_type == "Buy" or trade_type == "Sell") :
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
             pass
            
        if prctype == "MKT":

            if existing_trade:
                print("True")
                if (
                    trade_type == "Buy"
                    and existing_trade.trade_type == "Buy"
                    and existing_trade.trade_status == "incomplete"
                ):
                    print("here")
                    
                    existing_trade.avg_price = (
                                (Decimal(existing_trade.avg_price) * Decimal(existing_trade.quantity))
                                + (Decimal(trade_price) * Decimal(quantity))
                            ) / (Decimal(existing_trade.quantity) + Decimal(quantity))

                    existing_trade.quantity += quantity
                    existing_trade.invested_coin += invested_amount
                    existing_trade.margin_required += margin_required
                    existing_trade.save()

                    invested_amount_decimal = Decimal(invested_amount)

                    beetle_coins.coins -= invested_amount_decimal
                    beetle_coins.used_coins += invested_amount_decimal
                    beetle_coins.save()

                    margin.margin += margin_required
                    margin.save()

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

                elif (
                    trade_type == "Buy"
                    and existing_trade.trade_type == "Sell"
                    and existing_trade.trade_status == "incomplete"
                ):

                    # Convert quantity to Decimal for consistency
                    quantity = Decimal(quantity)

                    # Case 1: Quantity is greater than existing_trade.quantity
                    if quantity > existing_trade.quantity:
                        # Execute the existing sell order fully
                        remaining_quantity = quantity - existing_trade.quantity
                        # profit_loss = (Decimal(existing_trade.avg_price) - Decimal(trade_price)) * existing_trade.quantity

                        profit_loss = (
                            Decimal(existing_trade.avg_price) - Decimal(trade_price)
                        ) * quantity
                        margins = margin_required / quantity
                        # Record in ClosedTrades and TradeHistory
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=existing_trade.quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Buy",
                            quantity=existing_trade.quantity,
                            trade_price=trade_price,
                        )

                        # Adjust beetle coins
                        quantity_decimal = Decimal(
                            str(existing_trade.quantity)
                        )  # Convert quantity to Decimal
                        avg_price_decimal = Decimal(
                            str(existing_trade.avg_price)
                        )  # Convert avg_price to Decimal

                        profit_loss_decimal = Decimal(
                            str(profit_loss)
                        )  

                        # Perform the calculation using Decimal values
                        beetle_coins.coins += Decimal(
                            quantity_decimal * avg_price_decimal
                        ) + profit_loss_decimal
                        beetle_coins.used_coins -= quantity_decimal * avg_price_decimal
                        beetle_coins.save()

                        # Mark existing trade as complete
                        existing_trade.quantity = 0
                        existing_trade.trade_status = "complete"
                        existing_trade.save()

                        margin.margin = 0
                        margin.save()

                        # Create a new Buy trade for the remaining quantity

                        new_trades = TradesTaken.objects.create(
                            user=user,
                            token_id=existing_trade.token_id,
                            exchange=existing_trade.exchange,
                            trading_symbol=existing_trade.trading_symbol,
                            series=existing_trade.series,
                            lot_size=existing_trade.lot_size,
                            quantity=remaining_quantity,
                            display_name=existing_trade.display_name,
                            company_name=existing_trade.company_name,
                            expiry_date=existing_trade.expiry_date,
                            segment=existing_trade.segment,
                            option_type=existing_trade.option_type,
                            trade_type="Buy",
                            avg_price=trade_price,
                            prctype="MKT",
                            invested_coin=remaining_quantity * Decimal(trade_price),
                            margin_required=0,  # Update based on your logic
                            trade_status="incomplete",
                            ticker=existing_trade.ticker,
                        )
                        TradeHistory.objects.create(
                            trade=new_trades,
                            trade_type="Buy",
                            quantity=new_trades.quantity,
                            trade_price=existing_trade.avg_price,
                        )
                        beetle_coins.coins -= new_trades.quantity * new_trades.avg_price
                        beetle_coins.used_coins += (
                            new_trades.quantity * new_trades.avg_price
                        )
                        beetle_coins.save()

                        margin.margin = new_trades.quantity * margins
                        margin.save()

                        message = "Existing sell order executed, remaining quantity placed as a new Buy order."

                    # Case 2: Quantity is equal to existing_trade.quantity
                    elif quantity == existing_trade.quantity:
                        profit_loss = (
                            Decimal(existing_trade.avg_price) - Decimal(trade_price)
                        ) * quantity

                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Buy",
                            quantity=quantity,
                            trade_price=trade_price,
                        )

                        # Adjust beetle coins
                        quantity = Decimal(quantity)  # Convert quantity to Decimal
                        avg_price_con = Decimal(
                            existing_trade.avg_price
                        )  # Convert avg_price to Decimal

                        # Perform the calculation
                        beetle_coins.coins += ((Decimal(existing_trade.quantity)*Decimal(existing_trade.avg_price)) + profit_loss)
                        beetle_coins.used_coins -= Decimal(existing_trade.quantity)*Decimal(existing_trade.avg_price)
                        beetle_coins.save()

                        # Mark existing trade as complete
                        existing_trade.quantity = 0
                        existing_trade.trade_status = "complete"
                        existing_trade.save()

                        margin.margin -= margin.margin
                        margin.save()

                        message = "Sell order fully executed."

                    # Case 3: Quantity is less than existing_trade.quantity
                    elif quantity < existing_trade.quantity:
                        margins = margin.margin / existing_trade.quantity
                        profit_loss = (
                            Decimal(existing_trade.avg_price) - Decimal(trade_price)
                        ) * quantity

                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Buy",
                            quantity=quantity,
                            trade_price=trade_price,
                        )

                        # Adjust beetle coins
                        quantity_decimal = Decimal(
                            str(quantity)
                        )  # Convert quantity to Decimal
                        avg_price_decimal = Decimal(
                            str(existing_trade.avg_price)
                        )  # Convert avg_price to Decimal
                        profit_loss_decimal = Decimal(
                            str(profit_loss)
                        )  # Convert profit_loss to Decimal if it's a float

                        # Perform calculations with Decimal values
                        beetle_coins.coins += (Decimal(existing_trade.quantity)*Decimal(existing_trade.avg_price)+profit_loss_decimal)
                        beetle_coins.used_coins -=( Decimal(existing_trade.quantity)*Decimal(existing_trade.avg_price))
                    
                        
                        existing_trade.quantity -= quantity
                        existing_trade.invested_coin = existing_trade.quantity * Decimal(
                            existing_trade.avg_price
                        )
                        existing_trade.save()
                        margins_decimal = Decimal(
                            str(margins)
                        )  # Convert margins to Decimal
                        quantity_decimal = Decimal(
                            str(quantity)
                        )  # Convert quantity to Decimal
                        existing_quantity_decimal = Decimal(
                            str(existing_trade.quantity)
                        )  # Convert existing quantity to Decimal

                        # Perform the calculation with Decimals
                        margin.margin = margins_decimal * (
                            existing_quantity_decimal - quantity_decimal
                        )
                        margin.save()

                        message = (
                            "Sell order partially executed, remaining quantity updated."
                        )

                    # Build and return response
                    return Response(
                        {
                            "message": message,
                            "trade_history": TradeHistory.objects.filter(
                                trade=existing_trade
                            ).values(),
                            "closed_trades": ClosedTrades.objects.filter(
                                trade=existing_trade
                            ).values(),
                        },
                        status=status.HTTP_200_OK,
                    )
            

                elif (
                    trade_type == "Sell"
                    and existing_trade.trade_type == "Buy"
                    and existing_trade.trade_status == "incomplete"
                ):
                    remaining_quantity = quantity - existing_trade.quantity
                    # Scenario: Sell more than the available quantity
                    if quantity > existing_trade.quantity:
                        remaining_quantity = quantity - existing_trade.quantity

                        # Sell the available quantity
                        # profit_loss = (float(trade_price) - float(existing_trade.avg_price)) * existing_trade.quantity
                        profit_loss = (
                            float(trade_price) - float(existing_trade.avg_price)
                        ) * quantity
                        print(f"Profit/Loss for the available quantity: {profit_loss}")

                        # Record the Sell in ClosedTrades
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=existing_trade.quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )

                        # Add to TradeHistory for the sold quantity
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Sell",
                            quantity=existing_trade.quantity,
                            trade_price=trade_price,
                        )
                        margin.margin -= existing_trade.margin_required
                        margin.save()
                        margins = margin_required / quantity
                        # Update the existing trade after selling the available quantity
                        existing_trade.quantity = 0  # All available quantity sold
                        existing_trade.invested_coin = (
                            existing_trade.quantity * existing_trade.avg_price
                        )  # Reset invested amount since all bought quantity is sold
                        existing_trade.trade_status = (
                            "complete"  
                        )
                        existing_trade.save()

                        # Add the profit to BeetleCoins
                        beetle_coins.coins += Decimal(
                            quantity 
                        ) * Decimal(trade_price)
                        

                        beetle_coins.used_coins += Decimal(
                            quantity
                        ) * Decimal(existing_trade.avg_price)
                        beetle_coins.save()

                        # Create a new buy trade for the remaining quantity
                        new_trade = TradesTaken.objects.create(
                            user=existing_trade.user,
                            token_id=data.get("token_id"),
                            exchange="NFO",
                            trading_symbol=data.get("trading_symbol"),
                            series="FUT",
                            lot_size=15,
                            quantity=Decimal(remaining_quantity),  # Ensure Decimal
                            display_name=data.get("display_name"),
                            company_name=data.get("company_name"),
                            expiry_date=data.get("expiry_date"),
                            segment="FUT",
                            option_type="",
                            trade_type="Sell",
                            avg_price=Decimal(trade_price),  # Ensure Decimal
                            invested_coin=Decimal(remaining_quantity)
                            * Decimal(trade_price),
                            margin_required=data.get("margin_required"),
                            trade_status="incomplete",
                            ticker=data.get("ticker"),
                        )

                        TradeHistory.objects.create(
                            trade=new_trade,
                            trade_type="Sell",
                            quantity=new_trade.quantity,
                            trade_price=new_trade.avg_price,
                        )
                        margin.margin = margins * remaining_quantity
                        margin.save()

                        message = f"Sold {existing_trade.quantity} quantities, and a new trade has been created for {remaining_quantity} quantities."

                        return Response(
                            {
                                "message": message,
                                "trade_history": TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "closed_trades": ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "new_trade": {
                                    "trade_id": new_trade.id,
                                    "quantity": new_trade.quantity,
                                    "avg_price": new_trade.avg_price,
                                    "trade_status": new_trade.trade_status,
                                },
                            },
                            status=status.HTTP_200_OK,
                        )
                    elif quantity < existing_trade.quantity:
                        # Calculate profit/loss for the sold quantity
                        profit_loss = (
                            float(trade_price) - float(existing_trade.avg_price)
                        ) * quantity
                        print(f"Profit/Loss for the sold quantity: {profit_loss}")

                        # Record the Sell in ClosedTrades
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )

                        # Add to TradeHistory for the sell transaction
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Sell",
                            quantity=quantity,
                            trade_price=trade_price,
                        )

                        # Adjust the existing trade
                        existing_trade.quantity -= Decimal(
                            quantity
                        )  # Deduct the sold quantity
                        existing_trade.invested_coin = Decimal(
                            existing_trade.quantity
                        ) * Decimal(
                            existing_trade.avg_price
                        )  # Update invested amount
                        existing_trade.save()

                        # Update BeetleCoins after the trade
                        beetle_coins.coins += Decimal(quantity) * Decimal(
                            existing_trade.avg_price
                        ) + Decimal(profit_loss)
                        beetle_coins.used_coins -= Decimal(quantity) * Decimal(
                            existing_trade.avg_price
                        )
                        beetle_coins.save()

                        # Adjust the margin if required
                        # margin.margin += (Decimal(margin_required) / existing_trade.quantity) * Decimal(quantity)
                        # margin.save()

                        message = f"Sold {quantity} quantities. Remaining quantity: {existing_trade.quantity}."

                        return Response(
                            {
                                "message": message,
                                "trade_history": TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "closed_trades": ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values(),
                            },
                            status=status.HTTP_200_OK,
                        )

                    # Scenario: Sell the same or less quantity than available (Standard Sell)
                    elif quantity == existing_trade.quantity:
                        # Calculate profit/loss for this transaction
                        profit_loss = (
                            float(trade_price) - float(existing_trade.avg_price)
                        ) * quantity
                        # profit_loss = (Decimal(trade_price) - existing_trade.avg_price) * Decimal(quantity)
                        print(f"Profit/Loss for the transaction: {profit_loss}")

                        # Record the Sell in ClosedTrades
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        remaining_quantity = quantity - existing_trade.quantity
                        # Add to TradeHistory for the sell transaction
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Sell",
                            quantity=quantity,
                            trade_price=trade_price,
                        )
                        # beetle_coins.coins += Decimal(existing_trade.invested_coin)+  Decimal(
                        #     profit_loss
                        # )
                        # beetle_coins.coins+= (Decimal(existing_trade.invested_coin)+Decimal(profit_loss))
                        beetle_coins.coins += Decimal(quantity) * Decimal(
                            existing_trade.avg_price
                        ) + Decimal(profit_loss)
                        # beetle_coins.used_coins -= Decimal(existing_trade.invested_coin)
                        beetle_coins.used_coins -= Decimal(quantity) * Decimal(
                            existing_trade.avg_price
                        )
                        beetle_coins.save()

                        # Adjust the existing trade quantity and invested coin
                        # existing_trade.quantity -= quantity
                        # existing_trade.invested_coin = existing_trade.quantity * existing_trade.avg_price
                        existing_trade.quantity -= Decimal(quantity)  # Ensure Decimal
                        existing_trade.invested_coin = Decimal(
                            existing_trade.quantity
                        ) * Decimal(existing_trade.avg_price)

                        # Add profit/loss to BeetleCoins
                        print(beetle_coins.coins, invested_amount)
                        # beetle_coins.coins += Decimal(quantity*trade_price)

                        # beetle_coins.coins += invested_amount

                        # If the trade is now fully completed, mark it as complete
                        if existing_trade.quantity == 0:
                            existing_trade.trade_status = "complete"
                            message = "Trade completed and recorded."
                        else:
                            message = "Partial trade executed and recorded."

                        # Save the updated trade state
                        existing_trade.save()

                        # Update BeetleCoins after the trade

                        

                        # margin.margin += margin_required
                        # margin.save()

                        # beetle_coins.coins += invested_amount  # invested_amount should be defined
                        # beetle_coins.used_coins -= (invested_amount - profit_loss)
                        # beetle_coins.save()

                        return Response(
                            {
                                "message": message,
                                "trade_history": TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "closed_trades": ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values(),
                            },
                            status=status.HTTP_200_OK,
                        )

                # elif trade_type == "Sell" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete":

                # # Validate the requested quantity
                #     if quantity > existing_trade.quantity:
                #         return Response(
                #             {"error": "Cannot sell more than the available buy quantity."},
                #             status=status.HTTP_400_BAD_REQUEST,
                #         )

                #     # Calculate profit/loss for this transaction (Buy + Sell Scenario)
                #     profit_loss = (float(trade_price) - float(existing_trade.avg_price)) * quantity
                #     print(profit_loss)

                #     # Record the Sell in ClosedTrades
                #     ClosedTrades.objects.create(
                #         trade=existing_trade,
                #         sell_quantity=quantity,
                #         sell_price=trade_price,
                #         profit_loss=profit_loss,
                #     )

                #     # Add to TradeHistory
                #     TradeHistory.objects.create(
                #         trade=existing_trade,
                #         trade_type="Sell",
                #         quantity=quantity,
                #         trade_price=trade_price,
                #     )

                #     # Adjust the existing trade quantity
                #     existing_trade.quantity -= quantity
                #     existing_trade.invested_coin=existing_trade.quantity*existing_trade.avg_price
                #     beetle_coins.coins+=profit_loss

                #     # If the trade is now fully completed, mark it as complete
                #     if existing_trade.quantity == 0:
                #         existing_trade.trade_status = "complete"

                #     # Save the updated trade state
                #     existing_trade.save()
                #     beetle_coins.coins+=invested_amount
                #     beetle_coins.used_coins-=(invested_amount-profit_loss)
                #     beetle_coins.save()

                #     message = (
                #         "Trade completed and recorded." if existing_trade.trade_status == "complete"
                #         else "Partial trade executed and recorded."
                #     )

                #     return Response(
                #         {
                #             "message": message,
                #             "trade_history": TradeHistory.objects.filter(trade=existing_trade).values(),
                #             "closed_trades": ClosedTrades.objects.filter(trade=existing_trade).values(),
                #         },
                #         status=status.HTTP_200_OK,
                #     )
                elif (
                    trade_type == "Sell"
                    and existing_trade.trade_type == "Sell"
                    and existing_trade.trade_status == "incomplete"
                ):
                    # Update the existing sell trade (Sell + Sell)
                    # existing_trade.avg_price = (
                    #     existing_trade.avg_price * existing_trade.quantity
                    #     + trade_price * quantity
                    # ) / (existing_trade.quantity + quantity)

                    existing_trade.avg_price = (
                        Decimal(existing_trade.avg_price) * Decimal(existing_trade.quantity)
                        + Decimal(trade_price) * Decimal(quantity)
                    ) / (Decimal(existing_trade.quantity) + Decimal(quantity))
                    existing_trade.quantity += quantity
                    existing_trade.invested_coin = (
                        existing_trade.quantity * existing_trade.avg_price
                    )
                    existing_trade.save()
                    invested_amount_decimal = Decimal(str(invested_amount))
                    beetle_coins.coins -= invested_amount_decimal
                    beetle_coins.used_coins += invested_amount_decimal
                    beetle_coins.save()

                    # Add to TradeHistory
                    TradeHistory.objects.create(
                        trade=existing_trade,
                        trade_type="Sell",
                        quantity=quantity,
                        trade_price=trade_price,
                    )
                    margin.margin += margin_required
                    margin.save()
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
                elif (
                    trade_type == "Buy"
                    or trade_type == "Sell"
                    and existing_trade.quantity == 0
                    and existing_trade.trade_status == "completed"
                ):
                    print("here")
                    # Create a new trade since the existing one is complete
                    data["user"] = user.id  # Associate the new trade with the user
                    serializer = TradesTakenSerializer(
                        data=data
                    )  # Use serializer to validate and create new trade data

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

                        invested_amount_decimal = Decimal(invested_amount)

                        beetle_coins.coins -= invested_amount_decimal
                        beetle_coins.used_coins += invested_amount_decimal
                        beetle_coins.save()
                        # beetle_coins.coins-=invested_amount
                        # beetle_coins.used_coins+=invested_amount
                        # beetle_coins.save()

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
                        return Response(
                            serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )

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
                # beetle_coins.coins-=invested_amount
                # beetle_coins.used_coins+=invested_amount
                # beetle_coins.save()

                invested_amount_decimal = Decimal(invested_amount)

                beetle_coins.coins -= invested_amount_decimal
                beetle_coins.used_coins += invested_amount_decimal
                beetle_coins.save()

                margin.margin += margin_required
                margin.save()
                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                return Response(
                    {"message": "New trade created.......", "data": serializer.data},
                    status=status.HTTP_201_CREATED ,
                )
            else:
                return Response(
                    {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        elif prctype == "LMT":
            serializer = LimitOrderSerializer(data=data)

            if serializer.is_valid():
                serializer.save()  # Associate the user with the LimitOrder
                # print(serializer,"here?>>>>>>>>>>>>>>>>>>>>",)
                return Response({"message": "Limit order created successfully", "data": serializer.data},
                                status=status.HTTP_201_CREATED)
            else:
                return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            # Handle other conditions here...
            # return Response({"message": "Order type not supported."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"error": "Invalid product type. Expected 'MKT' or 'LMT'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
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
        expiry_date = data.get("expiry_date")
        margin_required = data.get("margin_required")
        print(ticker, trade_type, trade_price, quantity, invested_amount)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trade_type not in ["Buy", "Sell"]:
            return Response(
                {"error": "Invalid trade type. Use 'Buy' or 'Sell'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if an existing trade exists for this user and ticker

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)

        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        """ this conditionn checks whtether the user has enough coin"""
        # checking whether the user has enount coins to trade
        try:
            margin = MarginLocked.objects.get(user=user)
            print(margin)

        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        print(
            margin_required + margin.margin,
            beetle_coins.coins,
            beetle_coins.coins,
            invested_amount,
        )
        if (margin_required + margin.margin > beetle_coins.coins) or (
            beetle_coins.coins <= invested_amount
        ):
            print("here")
            return Response(
                {"error": "You don't have enough coins to execute the trade."},
                status=status.HTTP_404_NOT_FOUND,
            )

        existing_trade = (
            TradesTaken.objects.filter(user=user, ticker=ticker)
            .order_by("-created_at")
            .first()
        )
        print(existing_trade)

        if existing_trade:
            print("True")
            if (
                trade_type == "Buy"
                and existing_trade.trade_type == "Buy"
                and existing_trade.trade_status == "incomplete"
                and existing_trade
            ):
                print("here")
                # Update the existing trade (Buy + Buy)
                existing_trade.avg_price = (
                    existing_trade.avg_price * existing_trade.quantity
                    + trade_price * quantity
                ) / (existing_trade.quantity + quantity)
                existing_trade.quantity += quantity
                existing_trade.invested_coin += invested_amount
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Buy",
                    quantity=quantity,
                    trade_price=trade_price,
                )
                beetle_coins.coins -= invested_amount
                beetle_coins.used_coins += invested_amount
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
            elif (
                trade_type == "Buy"
                and existing_trade.trade_type == "Sell"
                and existing_trade.trade_status == "incomplete"
            ):
                if quantity > existing_trade.quantity:
                    # Calculate and execute the available quantity in the existing trade
                    # available_quantity = existing_trade.quantity
                    profit_loss = (
                        float(existing_trade.avg_price) - float(trade_price)
                    ) * quantity
                    avg_margin = (
                        existing_trade.margin_required / existing_trade.quantity
                    )

                    print(
                        f"Executing available quantity: {quantity}, Profit/Loss: {profit_loss}"
                    )

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
                    existing_trade.invested_coin = (
                        existing_trade.quantity * existing_trade.avg_price
                    )
                    existing_trade.trade_status = (
                        "complete" if existing_trade.quantity == 0 else "incomplete"
                    )

                    existing_trade.margin_required = (
                        avg_margin * existing_trade.quantity
                    )
                    existing_trade.save()

                    # Update Beetle Coins for the available quantity
                    invested_amount = (
                        existing_trade.avg_price * quantity
                    ) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= invested_amount - profit_loss
                    beetle_coins.save()

                    # Handle the remaining quantity by creating a new trade
                    remaining_quantity = existing_trade.quantity
                    print(
                        f"Creating a new trade for remaining quantity: {remaining_quantity}"
                    )

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
                                ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values()
                            ),
                        },
                        status=status.HTTP_200_OK,
                    )

                else:
                    # Execute normally if quantity <= existing_trade.quantity
                    profit_loss = (
                        float(existing_trade.avg_price) - float(trade_price)
                    ) * quantity

                    print(
                        f"Executing trade for full quantity: {quantity}, Profit/Loss: {profit_loss}"
                    )

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
                    existing_trade.invested_coin = (
                        existing_trade.quantity * existing_trade.avg_price
                    )
                    if existing_trade.quantity == 0:
                        existing_trade.trade_status = "complete"
                    existing_trade.save()

                    # Update Beetle Coins
                    invested_amount = (
                        existing_trade.avg_price * quantity
                    ) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= invested_amount - profit_loss
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
                                TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values()
                            ),
                            "closed_trades": list(
                                ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values()
                            ),
                        },
                        status=status.HTTP_200_OK,
                    )

            elif (
                trade_type == "Sell"
                and existing_trade.trade_type == "Buy"
                and existing_trade.trade_status == "incomplete"
            ):

                # Validate the requested quantity
                if quantity > existing_trade.quantity:
                    return Response(
                        {"error": "Cannot sell more than the available buy quantity."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Calculate profit/loss for this transaction (Buy + Sell Scenario)
                profit_loss = (float(trade_price) - float(existing_trade.avg_price)) * (
                    existing_trade.quantity - quantity
                )
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
                existing_trade.invested_coin = (
                    existing_trade.quantity * existing_trade.avg_price
                )
                beetle_coins.coins += profit_loss

                # If the trade is now fully completed, mark it as complete
                if existing_trade.quantity == 0:
                    existing_trade.trade_status = "complete"

                # Save the updated trade state
                existing_trade.save()

                invested_amount = (existing_trade.avg_price * quantity) + profit_loss

                # Check and deduct Beetle Coins before proceeding
                beetle_coins.coins += invested_amount
                beetle_coins.used_coins -= invested_amount - profit_loss
                beetle_coins.save()

                # Build response message
                message = (
                    "Trade completed and recorded."
                    if existing_trade.trade_status == "complete"
                    else "Partial trade executed and recorded."
                )

                return Response(
                    {
                        "message": message,
                        "trade_history": TradeHistory.objects.filter(
                            trade=existing_trade
                        ).values(),
                        "closed_trades": ClosedTrades.objects.filter(
                            trade=existing_trade
                        ).values(),
                    },
                    status=status.HTTP_200_OK,
                )
            elif (
                trade_type == "Sell"
                and existing_trade.trade_type == "Sell"
                and existing_trade.trade_status == "incomplete"
            ):
                # Update the existing sell trade (Sell + Sell)
                existing_trade.avg_price = (
                    existing_trade.avg_price * existing_trade.quantity
                    + trade_price * quantity
                ) / (existing_trade.quantity + quantity)
                existing_trade.quantity += quantity
                existing_trade.invested_coin += invested_amount
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Sell",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                beetle_coins.coins -= invested_amount
                beetle_coins.used_coins += invested_amount
                beetle_coins.save()

                return Response(
                    {
                        "message": "Existing incomplete sell trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,
                )

            
            

            elif (
                trade_type == "Buy"
                and existing_trade.trade_type == "Sell"
                and existing_trade.trade_status == "incomplete"
            ):
                # Check if Buy quantity is greater than Sell quantity
                if quantity > existing_trade.quantity:
                    # Step 1: Execute the available Sell quantity in the existing trade
                    available_quantity = existing_trade.quantity
                    profit_loss = (
                        float(existing_trade.avg_price) - float(trade_price)
                    ) * available_quantity
                    avg_margin = (
                        existing_trade.margin_required / existing_trade.quantity
                    )

                    print(
                        f"Executing available Sell quantity: {available_quantity}, Profit/Loss: {profit_loss}"
                    )

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
                    existing_trade.invested_coin = (
                        existing_trade.quantity * existing_trade.avg_price
                    )
                    existing_trade.margin_required = (
                        avg_margin * existing_trade.quantity
                    )
                    existing_trade.trade_status = (
                        "complete" if existing_trade.quantity == 0 else "incomplete"
                    )
                    existing_trade.save()

                    # Update Beetle Coins for the executed quantity
                    invested_amount = (
                        existing_trade.avg_price * available_quantity
                    ) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= invested_amount - profit_loss
                    beetle_coins.save()

                    # Step 2: Handle the remaining Buy quantity by creating a new trade
                    remaining_quantity = quantity - available_quantity
                    print(
                        f"Creating a new trade for remaining Buy quantity: {remaining_quantity}"
                    )

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
                                ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values()
                            ),
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    # Execute normally if Buy quantity <= Sell quantity
                    profit_loss = (
                        float(existing_trade.avg_price) - float(trade_price)
                    ) * quantity
                    avg_margin = (
                        existing_trade.margin_required / existing_trade.quantity
                    )

                    print(
                        f"Executing Buy quantity: {quantity}, Profit/Loss: {profit_loss}"
                    )

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
                    existing_trade.invested_coin = (
                        existing_trade.quantity * existing_trade.avg_price
                    )
                    existing_trade.margin_required = (
                        avg_margin * existing_trade.quantity
                    )
                    existing_trade.trade_status = (
                        "complete" if existing_trade.quantity == 0 else "incomplete"
                    )
                    existing_trade.save()

                    # Update Beetle Coins for the executed quantity
                    invested_amount = (
                        existing_trade.avg_price * quantity
                    ) + profit_loss
                    beetle_coins.coins += invested_amount
                    beetle_coins.used_coins -= invested_amount - profit_loss
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
                                TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values()
                            ),
                            "closed_trades": list(
                                ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values()
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

            if option_type == "CE" or option_type == "PE" and trade_type == "Sell":

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
                margin.margin += data["margin_required"]
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
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

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


class OptionsCreateView(APIView):
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
        print(ticker, trade_type, trade_price, quantity, invested_amount)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trade_type not in ["Buy", "Sell"]:
            return Response(
                {"error": "Invalid trade type. Use 'Buy' or 'Sell'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if an existing trade exists for this user and ticker
        existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).first()
        print(existing_trade)

        # Retrieve BeetleCoins and MarginLocked records
        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
            print(beetle_coins)
        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            margin = MarginLocked.objects.get(user=user)
            print(margin)
        except MarginLocked.DoesNotExist:
            return Response(
                {"error": "User's MarginLocked record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate margin and coin availability
        if (margin_required + margin.margin > beetle_coins.coins) or (
            beetle_coins.coins <= invested_amount
        ):
            return Response(
                {"error": "You don't have enough coins to execute the trade."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if existing_trade:
            print("Existing trade found.")
            # Handle scenarios for existing trades

            if trade_type == "Sell":
                profit_losss = (
                    existing_trade.avg_price - trade_price
                ) * existing_trade.quantity

                if quantity > existing_trade.quantity:
                    return Response(
                        {"error": "Cannot sell more than available quantity."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # elif quantity == existing_trade.quantity:
                #     # Mark the trade as complete
                #     existing_trade.trade_status = "complete"
                #     existing_trade.quantity = 0
                # else:
                #     # Reduce the trade quantity
                #     existing_trade.quantity -= quantity

                # existing_trade.save()

                # profit_losss = (existing_trade.avg_price-trade_price ) * existing_trade.quantity

                # ClosedTrades.objects.create(
                #     trade=existing_trade,
                #     sell_quantity=quantity,
                #     sell_price=trade_price,
                #     profit_loss=profit_losss,
                # )

                # # Add to TradeHistory
                # TradeHistory.objects.create(
                #     trade=existing_trade,
                #     trade_type="Sell",
                #     quantity=quantity,
                #     trade_price=trade_price,
                # )

                # Update beetle coins
                # invested_amount = Decimal(invested_amount)
                # profit_loss = Decimal(profit_loss)

                # # Now perform the operations
                # beetle_coins.coins += invested_amount
                # beetle_coins.used_coins -= (invested_amount + profit_loss)
                # beetle_coins.save()

                # return Response(
                #     {"message": "Sell trade executed successfully.", "data": TradesTakenSerializer(existing_trade).data},
                #     status=status.HTTP_200_OK,
                # )

            elif trade_type == "Buy" and existing_trade.trade_status == "incomplete":
                # Update an existing incomplete Buy trade
                existing_trade.avg_price = (
                    existing_trade.avg_price * existing_trade.quantity
                    + float(trade_price) * quantity
                ) / (existing_trade.quantity + quantity)
                existing_trade.quantity += quantity
                existing_trade.invested_coin += invested_amount
                existing_trade.save()

                # Add to TradeHistory
                TradeHistory.objects.create(
                    trade=existing_trade,
                    trade_type="Buy",
                    quantity=quantity,
                    trade_price=trade_price,
                )

                # Update beetle coins
                beetle_coins.coins -= invested_amount
                beetle_coins.used_coins += invested_amount
                beetle_coins.save()

                return Response(
                    {
                        "message": "Existing incomplete buy trade updated.",
                        "data": TradesTakenSerializer(existing_trade).data,
                    },
                    status=status.HTTP_200_OK,
                )

        elif trade_type == "Buy":
            # Create a new trade for Buy
            data["user"] = user.id
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

                # Update beetle coins
                beetle_coins.coins -= invested_amount
                beetle_coins.used_coins += invested_amount
                beetle_coins.save()

                return Response(
                    {"message": "New trade created.", "data": serializer.data},
                    status=status.HTTP_201_CREATED,
                )

        # Default response for unsupported scenarios
        return Response(
            {"error": "Trade cannot be executed."},
            status=status.HTTP_400_BAD_REQUEST,
        )


"""this is the more condition being checked for MKT and LMT trades"""


class TradeCreateViews(APIView):
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
        product_type = data.get("product_type")
        prctype = data.get("prctype")

        print(ticker, trade_type, trade_price, quantity, invested_amount)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trade_type not in ["Buy", "Sell"]:
            return Response(
                {"error": "Invalid trade type. Use 'Buy' or 'Sell'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if an existing trade exists for this user and ticker
        # existing_trade = TradesTaken.objects.filter(user=user, ticker=ticker).first()
        existing_trade = (
            TradesTaken.objects.filter(
                user=user, ticker=ticker, product_type=product_type
            )
            .order_by("-created_at")
            .first()
        )
        print(existing_trade)

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
            print(beetle_coins)
        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # if beetle_coins.coins < invested_amount:
        #     return Response(
        #         {"error": "Insufficient Beetle Coins to execute the trade."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )
        """ this conditionn checks whtether the user has enough coin"""
        # checking whether the user has enount coins to trade
        try:
            margin = MarginLocked.objects.get(user=user)
            print(margin)

        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
        #     print("here")
        #     return Response(
        #         {"error": "You don't have enough coins to execute the trade."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )

        # if beetle_coins.coins <= invested_amount:
        #     print("here")
        #     return Response(
        #         {"error": "You don't have enough coins to execute the trade."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )
        if beetle_coins.coins <= invested_amount:
            if existing_trade and (
                    (trade_type == "Sell" and existing_trade.trade_type == "Sell")
                    or (trade_type == "Buy" and existing_trade.trade_type == "Buy")
            ):
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            elif not existing_trade:
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            pass
        # Check if the prctype is 'MKT' or 'LMT'
        if prctype == "MKT":
            # if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
            #     print(f"Margin required: {margin_required}, Margin: {margin.margin}, Coins: {beetle_coins.coins}, Invested amount: {invested_amount}")
            #     return Response(
            #         {"error": "You don't have enough coins to execute the trade."},
            #         status=status.HTTP_404_NOT_FOUND,
            #     )
            if existing_trade:
                print("Already")
                # Handle different conditions based on trade_type and trade_status
                print(trade_type, existing_trade.trade_type, existing_trade.trade_status)
                if (
                        trade_type == "Buy"
                        and existing_trade.trade_type == "Buy"
                        and existing_trade.trade_status == "incomplete"
                ):
                    print("here")
                    # Update the existing trade (Buy + Buy)
                    existing_trade.avg_price = (
                                                       existing_trade.avg_price * existing_trade.quantity
                                                       + float(trade_price) * quantity
                                               ) / (existing_trade.quantity + quantity)
                    existing_trade.quantity += quantity
                    existing_trade.invested_coin += invested_amount

                    existing_trade.save()

                    beetle_coins.coins -= Decimal(invested_amount)
                    beetle_coins.used_coins += Decimal(invested_amount)
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

                elif (
                        trade_type == "Buy"
                        and existing_trade.trade_type == "Sell"
                        and existing_trade.trade_status == "incomplete"
                ):
                    # Validate the requested quantity
                    if quantity > existing_trade.quantity:
                        return Response(
                            {"error": "Cannot buy more than the available sell quantity."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    profit_loss = (
                                          float(existing_trade.avg_price) - float(trade_price)
                                  ) * quantity

                    # Calculate profit/loss for this transaction (Short Selling Scenario)

                    print(profit_loss)

                    ClosedTrades.objects.create(
                        trade=existing_trade,
                        product_type=existing_trade.product_type,
                        sell_quantity=quantity,
                        avg_price=existing_trade.avg_price,
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
                    existing_trade.invested_coin -= (
                            existing_trade.quantity * existing_trade.avg_price
                    )

                    # If the trade is now fully completed, mark it as complete
                    if existing_trade.quantity == 0:
                        existing_trade.trade_status = "complete"

                    # Save the updated trade state
                    existing_trade.save()
                    invested_amount = (existing_trade.avg_price * quantity) + profit_loss
                    beetle_coins.coins += Decimal(invested_amount)
                    beetle_coins.used_coins -= Decimal(invested_amount - profit_loss)
                    beetle_coins.save()

                    # Check and deduct Beetle Coins before proceeding
                    # try:
                    #     beetle_coins.use_coins(invested_amount)
                    # except ValidationError as e:
                    #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                    # Build response message
                    message = (
                        "Trade completed and recorded."
                        if existing_trade.trade_status == "complete"
                        else "Partial trade executed and recorded."
                    )

                    return Response(
                        {
                            "message": message,
                            "trade_history": TradeHistory.objects.filter(
                                trade=existing_trade
                            ).values(),
                            "closed_trades": ClosedTrades.objects.filter(
                                trade=existing_trade
                            ).values(),
                        },
                        status=status.HTTP_200_OK,
                    )

                elif (
                        trade_type == "Sell"
                        and existing_trade.trade_type == "Buy"
                        and existing_trade.trade_status == "incomplete"
                ):

                    # Validate the requested quantity
                    if quantity > existing_trade.quantity:
                        return Response(
                            {"error": "Cannot sell more than the available buy quantity."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Calculate profit/loss for this transaction (Buy + Sell Scenario)
                    profit_loss = (
                                          float(trade_price) - float(existing_trade.avg_price)
                                  ) * quantity
                    print(profit_loss)

                    # Record the Sell in ClosedTrades
                    ClosedTrades.objects.create(
                        trade=existing_trade,
                        product_type=existing_trade.product_type,
                        sell_quantity=quantity,
                        avg_price=existing_trade.avg_price,
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
                    existing_trade.invested_coin = (
                            existing_trade.quantity * existing_trade.avg_price
                    )
                    # beetle_coins.coins+=profit_loss

                    # If the trade is now fully completed, mark it as complete
                    if existing_trade.quantity == 0:
                        existing_trade.trade_status = "complete"

                    # Save the updated trade state
                    existing_trade.save()
                    beetle_coins.coins += Decimal(invested_amount)
                    # beetle_coins.coins+=invested_amount
                    # test this scenario
                    print(beetle_coins.coins)

                    beetle_coins.used_coins -= Decimal(invested_amount - profit_loss)
                    beetle_coins.save()

                    # commented for testing the invested coin not working properly

                    # invested_amount = (existing_trade.avg_price * quantity) + profit_loss

                    # Check and deduct Beetle Coins before proceeding
                    # try:
                    #     beetle_coins.use_coins(invested_amount)
                    # except ValidationError as e:
                    #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                    # Build response message
                    message = (
                        "Trade completed and recorded."
                        if existing_trade.trade_status == "complete"
                        else "Partial trade executed and recorded."
                    )

                    return Response(
                        {
                            "message": message,
                            "trade_history": TradeHistory.objects.filter(
                                trade=existing_trade
                            ).values(),
                            "closed_trades": ClosedTrades.objects.filter(
                                trade=existing_trade
                            ).values(),
                        },
                        status=status.HTTP_200_OK,
                    )

                elif (
                        trade_type == "Sell"
                        and existing_trade.trade_type == "Sell"
                        and existing_trade.trade_status == "incomplete"
                ):
                    # Update the existing sell trade (Sell + Sell)
                    existing_trade.avg_price = (
                                                       existing_trade.avg_price * existing_trade.quantity
                                                       + trade_price * quantity
                                               ) / (existing_trade.quantity + quantity)
                    existing_trade.quantity += quantity
                    existing_trade.invested_coin += invested_amount
                    existing_trade.save()
                    # beetle_coins.coins -= invested_amount
                    # beetle_coins.used_coins += invested_amount
                    # beetle_coins.save()
                    beetle_coins.coins -= Decimal(str(invested_amount))  # Convert float to Decimal
                    beetle_coins.used_coins += Decimal(str(invested_amount))
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
                elif (
                        trade_type == "Buy"
                        or trade_type == "Sell"
                        and existing_trade.quantity == 0
                        and existing_trade.trade_status == "completed"
                ):
                    print("here")
                    # Create a new trade since the existing one is complete
                    data["user"] = user.id  # Associate the new trade with the user
                    serializer = TradesTakenSerializer(
                        data=data
                    )  # Use serializer to validate and create new trade data

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

                        beetle_coins.coins -= Decimal(invested_amount)
                        beetle_coins.used_coins += Decimal(invested_amount)
                        beetle_coins.save()

                        # beetle_coins.coins-=invested_amount
                        # beetle_coins.used_coins+=invested_amount
                        # beetle_coins.save()

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
                        return Response(
                            serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )

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
            # data["user"] = user.id  # Add user to the data
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

                beetle_coins.coins -= Decimal(invested_amount)
                beetle_coins.used_coins += Decimal(invested_amount)
                beetle_coins.save()

                # beetle_coins.coins-=invested_amount

                # beetle_coins.used_coins+=invested_amount
                # beetle_coins.save()
                # try:
                #     beetle_coins.use_coins(invested_amount)
                # except ValidationError as e:
                #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

                return Response(
                    {"message": "New trade created.......", "data": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        elif prctype == "LMT":
            serializer = LimitOrderSerializer(data=data)

            if serializer.is_valid():
                serializer.save()  # Associate the user with the LimitOrder
                # print(serializer,"here?>>>>>>>>>>>>>>>>>>>>",)
                return Response({"message": "Limit order created successfully", "data": serializer.data},
                                status=status.HTTP_201_CREATED)
            else:
                return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            # Handle other conditions here...
            # return Response({"message": "Order type not supported."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {"error": "Invalid product type. Expected 'MKT' or 'LMT'."},
                status=status.HTTP_400_BAD_REQUEST,
            )


def process_trade(data=None):
    print(f"Processing trade with data: {data}")
    # user = request.user
    # data = request.data
    user = data.get("user")

    # Extract data from request
    ticker = data.get("ticker")
    trade_type = data.get("trade_type")
    trade_price = data.get("avg_price")
    quantity = data.get("quantity")
    invested_amount = data.get("invested_coin")
    margin_required = data.get("margin_required")
    product_type = data.get("product_type")
    print(f"Processing trade withdataaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    print(ticker, trade_type, trade_price, quantity)

    # Validate required fields
    if not ticker or not trade_type or not trade_price or not quantity:
        print(f"ticker or not trade_type or not trade_price or not quantity")
        return Response(
            {"error": "Missing required fields."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if trade_type not in ["Buy", "Sell"]:
        return Response(
            {"error": "Invalid trade type. Use 'Buy' or 'Sell'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if an existing trade exists for this user and ticker
    print("Checking for existing trade")
    print(f"user: {user} and ticker: {ticker} and product_type: {product_type}")
    existing_trade = (
        TradesTaken.objects.filter(user=user, ticker=ticker, product_type=product_type).order_by("-created_at").first())
    print(existing_trade)
    # Handle BeetleCoins retrieval
    try:
        beetle_coins = BeetleCoins.objects.get(user=user)
        print(f"Beetle coins: {beetle_coins.coins}")
    except BeetleCoins.DoesNotExist:
        return Response(
            {"error": "User's Beetle Coins record not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check if the user has enough BeetleCoins to trade
    if beetle_coins.coins <= invested_amount:
        print(f"Check if the user has enough BeetleCoins to trade")
        if existing_trade and (
                (trade_type == "Sell" and existing_trade.trade_type == "Sell")
                or (trade_type == "Buy" and existing_trade.trade_type == "Buy")
        ):
            print(f"Check if the user has enough")
            return Response(
                {"error": "You don't have enough coins to execute the trade."},
                status=status.HTTP_404_NOT_FOUND,
            )
        elif not existing_trade:
            print(f"You don't have enough coins to execute the trade'")
            return Response(
                {"error": "You don't have enough coins to execute the trade."},
                status=status.HTTP_404_NOT_FOUND,
            )

    # Handle margin retrieval
    # try:
    #     margin = MarginLocked.objects.get(user=user)
    # except MarginLocked.DoesNotExist:
    #     return Response(
    #         {"error": "User's Margin record not found."},
    #         status=status.HTTP_404_NOT_FOUND,
    #     )

    # Handle different conditions based on the trade scenario
    if existing_trade:
        if trade_type == "Buy" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete":
            existing_trade.avg_price = (
                                               existing_trade.avg_price * existing_trade.quantity
                                               + float(trade_price) * quantity
                                       ) / (existing_trade.quantity + quantity)
            existing_trade.quantity += quantity
            existing_trade.invested_coin += invested_amount
            existing_trade.save()

            beetle_coins.coins -= Decimal(invested_amount)
            beetle_coins.used_coins += Decimal(invested_amount)
            beetle_coins.save()

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
            if quantity > existing_trade.quantity:
                return Response(
                    {"error": "Cannot buy more than the available sell quantity."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            profit_loss = (float(existing_trade.avg_price) - float(trade_price)) * quantity

            ClosedTrades.objects.create(
                trade=existing_trade,
                product_type=existing_trade.product_type,
                sell_quantity=quantity,
                avg_price=existing_trade.avg_price,
                sell_price=trade_price,
                profit_loss=profit_loss,
            )

            TradeHistory.objects.create(
                trade=existing_trade,
                trade_type="Buy",
                quantity=quantity,
                trade_price=trade_price,
            )

            existing_trade.quantity -= quantity
            existing_trade.invested_coin -= existing_trade.quantity * existing_trade.avg_price

            if existing_trade.quantity == 0:
                existing_trade.trade_status = "complete"

            existing_trade.save()

            beetle_coins.coins += Decimal(invested_amount)
            beetle_coins.used_coins -= Decimal(invested_amount - profit_loss)
            beetle_coins.save()

            message = "Trade completed and recorded." if existing_trade.trade_status == "complete" else "Partial trade executed and recorded."

            return Response(
                {
                    "message": message,
                    "trade_history": TradeHistory.objects.filter(trade=existing_trade).values(),
                    "closed_trades": ClosedTrades.objects.filter(trade=existing_trade).values(),
                },
                status=status.HTTP_200_OK,
            )

        elif trade_type == "Sell" and existing_trade.trade_type == "Buy" and existing_trade.trade_status == "incomplete":
            if quantity > existing_trade.quantity:
                return Response(
                    {"error": "Cannot sell more than the available buy quantity."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            profit_loss = (float(trade_price) - float(existing_trade.avg_price)) * quantity

            ClosedTrades.objects.create(
                trade=existing_trade,
                product_type=existing_trade.product_type,
                sell_quantity=quantity,
                avg_price=existing_trade.avg_price,
                sell_price=trade_price,
                profit_loss=profit_loss,
            )

            TradeHistory.objects.create(
                trade=existing_trade,
                trade_type="Sell",
                quantity=quantity,
                trade_price=trade_price,
            )

            existing_trade.quantity -= quantity
            existing_trade.invested_coin = existing_trade.quantity * existing_trade.avg_price

            if existing_trade.quantity == 0:
                existing_trade.trade_status = "complete"

            existing_trade.save()

            beetle_coins.coins += Decimal(invested_amount)
            beetle_coins.used_coins -= Decimal(invested_amount - profit_loss)
            beetle_coins.save()

            message = "Trade completed and recorded." if existing_trade.trade_status == "complete" else "Partial trade executed and recorded."

            return Response(
                {
                    "message": message,
                    "trade_history": TradeHistory.objects.filter(trade=existing_trade).values(),
                    "closed_trades": ClosedTrades.objects.filter(trade=existing_trade).values(),
                },
                status=status.HTTP_200_OK,
            )

        # Handle other trade scenarios as needed...

    # If no existing trade, create a new one
    serializer = TradesTakenSerializer(data=data)

    if serializer.is_valid():
        new_trade = serializer.save()

        TradeHistory.objects.create(
            trade=new_trade,
            trade_type=trade_type,
            quantity=quantity,
            trade_price=trade_price,
        )

        beetle_coins.coins -= Decimal(invested_amount)
        beetle_coins.used_coins += Decimal(invested_amount)
        beetle_coins.save()

        return Response(
            {
                "message": "New trade created.",
                "data": TradesTakenSerializer(new_trade).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        serializer.errors, status=status.HTTP_400_BAD_REQUEST)



def process_futures(data= None):
        user = data.get("user")

        ticker = data.get("ticker")
        trade_type = data.get("trade_type")
        trade_price = data.get("avg_price")
        quantity = data.get("quantity")
        invested_amount = data.get("invested_coin")
        expiry_date = data.get("expiry_date")
        margin_required = data.get("margin_required")
        product_type = data.get("product_type")
        prctype = data.get("prctype")
        print(ticker, trade_type, trade_price, quantity, product_type)

        # Validate required fields
        if not ticker or not trade_type or not trade_price or not quantity:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if trade_type not in ["Buy", "Sell"]:
            return Response(
                {"error": "Invalid trade type. Use 'Buy' or 'Sell'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if an existing trade exists for this user and ticker
        existing_trade = (
            TradesTaken.objects.filter(
                user=user, ticker=ticker, product_type=product_type
            )
            .order_by("-created_at")
            .first()
        )
        print(existing_trade)

        try:
            beetle_coins = BeetleCoins.objects.get(user=user)
        except BeetleCoins.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        """ this conditionn checks whtether the user has enough coin"""

        # checking whether the user has enount coins to trade
        try:
            margin = MarginLocked.objects.get(user=user)
            print(margin)

        except MarginLocked.DoesNotExist:
            return Response(
                {"error": "User's Beetle Coins record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        print(
            # margin_required + margin.margin,
            beetle_coins.coins,
            beetle_coins.coins,
            invested_amount,
        )
        # if (margin_required + margin.margin > beetle_coins.coins) or (beetle_coins.coins <= invested_amount):
        # print("here")
        # return Response(
        #     {"error": "You don't have enough coins to execute the trade."},
        #     status=status.HTTP_404_NOT_FOUND,
        # )
        """this is tested"""

        # if (beetle_coins.coins <= invested_amount) and (trade_type == "Sell" and existing_trade.trade_type == "Buy"):
        #     print("here")
        #     return Response(
        #         {"error": "You don't have enough coins to execute the trade."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )

        if beetle_coins.coins <= invested_amount:
            if existing_trade and (
                (trade_type == "Sell" and existing_trade.trade_type == "Sell")
                or (trade_type == "Buy" and existing_trade.trade_type == "Buy")
            ):
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            elif not existing_trade:
                print("here")
                return Response(
                    {"error": "You don't have enough coins to execute the trade."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        if existing_trade:
                print("True")
                if (
                    trade_type == "Buy"
                    and existing_trade.trade_type == "Buy"
                    and existing_trade.trade_status == "incomplete"
                ):
                    print("here")
                   
                    existing_trade.avg_price = (
                                (Decimal(existing_trade.avg_price) * Decimal(existing_trade.quantity))
                                + (Decimal(trade_price) * Decimal(quantity))
                            ) / (Decimal(existing_trade.quantity) + Decimal(quantity))

                    existing_trade.quantity += quantity
                    existing_trade.invested_coin += invested_amount
                    existing_trade.margin_required += margin_required
                    existing_trade.save()

                    invested_amount_decimal = Decimal(invested_amount)

                    beetle_coins.coins -= invested_amount_decimal
                    beetle_coins.used_coins += invested_amount_decimal
                    beetle_coins.save()

                    margin.margin += margin_required
                    margin.save()

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

                elif (
                    trade_type == "Buy"
                    and existing_trade.trade_type == "Sell"
                    and existing_trade.trade_status == "incomplete"
                ):

                    # Convert quantity to Decimal for consistency
                    quantity = Decimal(quantity)

                    # Case 1: Quantity is greater than existing_trade.quantity
                    if quantity > existing_trade.quantity:
                        # Execute the existing sell order fully
                        remaining_quantity = quantity - existing_trade.quantity
                        # profit_loss = (Decimal(existing_trade.avg_price) - Decimal(trade_price)) * existing_trade.quantity

                        profit_loss = (
                            Decimal(existing_trade.avg_price) - Decimal(trade_price)
                        ) * quantity
                        margins = margin_required / quantity
                        # Record in ClosedTrades and TradeHistory
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=existing_trade.quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Buy",
                            quantity=existing_trade.quantity,
                            trade_price=trade_price,
                        )

                        # Adjust beetle coins
                        quantity_decimal = Decimal(
                            str(existing_trade.quantity)
                        )  # Convert quantity to Decimal
                        avg_price_decimal = Decimal(
                            str(existing_trade.avg_price)
                        )  # Convert avg_price to Decimal

                        profit_loss_decimal = Decimal(
                            str(profit_loss)
                        )  # Convert profit_loss to Decimal if it's a float

                        # Perform the calculation using Decimal values
                        beetle_coins.coins += Decimal(
                            quantity_decimal * avg_price_decimal
                        ) + profit_loss_decimal
                        beetle_coins.used_coins -= quantity_decimal * avg_price_decimal
                        beetle_coins.save()

                        # Mark existing trade as complete
                        existing_trade.quantity = 0
                        existing_trade.trade_status = "complete"
                        existing_trade.save()

                        margin.margin = 0
                        margin.save()

                        # Create a new Buy trade for the remaining quantity

                        new_trades = TradesTaken.objects.create(
                            user=user,
                            token_id=existing_trade.token_id,
                            exchange=existing_trade.exchange,
                            trading_symbol=existing_trade.trading_symbol,
                            series=existing_trade.series,
                            lot_size=existing_trade.lot_size,
                            quantity=remaining_quantity,
                            display_name=existing_trade.display_name,
                            company_name=existing_trade.company_name,
                            expiry_date=existing_trade.expiry_date,
                            segment=existing_trade.segment,
                            option_type=existing_trade.option_type,
                            trade_type="Buy",
                            avg_price=trade_price,
                            prctype="MKT",
                            invested_coin=remaining_quantity * Decimal(trade_price),
                            margin_required=0,  # Update based on your logic
                            trade_status="incomplete",
                            ticker=existing_trade.ticker,
                        )
                        TradeHistory.objects.create(
                            trade=new_trades,
                            trade_type="Buy",
                            quantity=new_trades.quantity,
                            trade_price=existing_trade.avg_price,
                        )
                        beetle_coins.coins -= new_trades.quantity * new_trades.avg_price
                        beetle_coins.used_coins += (
                            new_trades.quantity * new_trades.avg_price
                        )
                        beetle_coins.save()

                        margin.margin = new_trades.quantity * margins
                        margin.save()

                        message = "Existing sell order executed, remaining quantity placed as a new Buy order."

                    # Case 2: Quantity is equal to existing_trade.quantity
                    elif quantity == existing_trade.quantity:
                        profit_loss = (
                            Decimal(existing_trade.avg_price) - Decimal(trade_price)
                        ) * quantity

                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Buy",
                            quantity=quantity,
                            trade_price=trade_price,
                        )

                        # Adjust beetle coins
                        quantity = Decimal(quantity)  # Convert quantity to Decimal
                        avg_price_con = Decimal(
                            existing_trade.avg_price
                        )  # Convert avg_price to Decimal

                        # Perform the calculation
                        beetle_coins.coins += (Decimal(existing_trade.invested_coin) + profit_loss)
                        beetle_coins.used_coins -= Decimal(existing_trade.invested_coin)
                        beetle_coins.save()

                        # Mark existing trade as complete
                        existing_trade.quantity = 0
                        existing_trade.trade_status = "complete"
                        existing_trade.save()

                        margin.margin -= margin.margin
                        margin.save()

                        message = "Sell order fully executed."

                    # Case 3: Quantity is less than existing_trade.quantity
                    elif quantity < existing_trade.quantity:
                        margins = margin.margin / existing_trade.quantity
                        profit_loss = (
                            Decimal(existing_trade.avg_price) - Decimal(trade_price)
                        ) * quantity

                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Buy",
                            quantity=quantity,
                            trade_price=trade_price,
                        )

                        # Adjust beetle coins
                        quantity_decimal = Decimal(
                            str(quantity)
                        )  # Convert quantity to Decimal
                        avg_price_decimal = Decimal(
                            str(existing_trade.avg_price)
                        )  # Convert avg_price to Decimal
                        profit_loss_decimal = Decimal(
                            str(profit_loss)
                        )  # Convert profit_loss to Decimal if it's a float

                        # Perform calculations with Decimal values
                        beetle_coins.coins += Decimal(invested_amount)
                        beetle_coins.used_coins -= Decimal(invested_amount)
                    
                        
                        existing_trade.quantity -= quantity
                        existing_trade.invested_coin = existing_trade.quantity * Decimal(
                            existing_trade.avg_price
                        )
                        existing_trade.save()
                        margins_decimal = Decimal(
                            str(margins)
                        )  # Convert margins to Decimal
                        quantity_decimal = Decimal(
                            str(quantity)
                        )  # Convert quantity to Decimal
                        existing_quantity_decimal = Decimal(
                            str(existing_trade.quantity)
                        )  # Convert existing quantity to Decimal

                        # Perform the calculation with Decimals
                        margin.margin = margins_decimal * (
                            existing_quantity_decimal - quantity_decimal
                        )
                        margin.save()

                        message = (
                            "Sell order partially executed, remaining quantity updated."
                        )

                    # Build and return response
                    return Response(
                        {
                            "message": message,
                            "trade_history": TradeHistory.objects.filter(
                                trade=existing_trade
                            ).values(),
                            "closed_trades": ClosedTrades.objects.filter(
                                trade=existing_trade
                            ).values(),
                        },
                        status=status.HTTP_200_OK,
                    )
            

                elif (
                    trade_type == "Sell"
                    and existing_trade.trade_type == "Buy"
                    and existing_trade.trade_status == "incomplete"
                ):
                    remaining_quantity = quantity - existing_trade.quantity
                    # Scenario: Sell more than the available quantity
                    if quantity > existing_trade.quantity:
                        remaining_quantity = quantity - existing_trade.quantity

                        # Sell the available quantity
                        # profit_loss = (float(trade_price) - float(existing_trade.avg_price)) * existing_trade.quantity
                        profit_loss = (
                            float(trade_price) - float(existing_trade.avg_price)
                        ) * quantity
                        print(f"Profit/Loss for the available quantity: {profit_loss}")

                        # Record the Sell in ClosedTrades
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=existing_trade.quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )

                        # Add to TradeHistory for the sold quantity
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Sell",
                            quantity=existing_trade.quantity,
                            trade_price=trade_price,
                        )
                        margin.margin -= existing_trade.margin_required
                        margin.save()
                        margins = margin_required / quantity
                        # Update the existing trade after selling the available quantity
                        existing_trade.quantity = 0  # All available quantity sold
                        existing_trade.invested_coin = (
                            existing_trade.quantity * existing_trade.avg_price
                        )  # Reset invested amount since all bought quantity is sold
                        existing_trade.trade_status = (
                            "complete"  # Mark the original trade as complete
                        )
                        existing_trade.save()

                        # Add the profit to BeetleCoins
                        beetle_coins.coins += Decimal(
                            quantity - remaining_quantity
                        ) * Decimal(existing_trade.avg_price)
                        # beetle_coins.coins += Decimal(
                        #     quantity - remaining_quantity
                        # ) * Decimal(existing_trade.avg_price)

                        beetle_coins.used_coins += Decimal(
                            quantity - remaining_quantity
                        ) * Decimal(trade_price)
                        beetle_coins.save()

                        # Create a new buy trade for the remaining quantity
                        new_trade = TradesTaken.objects.create(
                            user=existing_trade.user,
                            token_id=data.get("token_id"),
                            exchange="NFO",
                            trading_symbol=data.get("trading_symbol"),
                            series="FUT",
                            lot_size=15,
                            quantity=Decimal(remaining_quantity),  # Ensure Decimal
                            display_name=data.get("display_name"),
                            company_name=data.get("company_name"),
                            expiry_date=data.get("expiry_date"),
                            segment="FUT",
                            option_type="",
                            trade_type="Sell",
                            avg_price=Decimal(trade_price),  # Ensure Decimal
                            invested_coin=Decimal(remaining_quantity)
                            * Decimal(trade_price),
                            margin_required=data.get("margin_required"),
                            trade_status="incomplete",
                            ticker=data.get("ticker"),
                        )

                        TradeHistory.objects.create(
                            trade=new_trade,
                            trade_type="Sell",
                            quantity=new_trade.quantity,
                            trade_price=new_trade.avg_price,
                        )
                        margin.margin = margins * remaining_quantity
                        margin.save()

                        message = f"Sold {existing_trade.quantity} quantities, and a new trade has been created for {remaining_quantity} quantities."

                        return Response(
                            {
                                "message": message,
                                "trade_history": TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "closed_trades": ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "new_trade": {
                                    "trade_id": new_trade.id,
                                    "quantity": new_trade.quantity,
                                    "avg_price": new_trade.avg_price,
                                    "trade_status": new_trade.trade_status,
                                },
                            },
                            status=status.HTTP_200_OK,
                        )
                    elif quantity < existing_trade.quantity:
                        # Calculate profit/loss for the sold quantity
                        profit_loss = (
                            float(trade_price) - float(existing_trade.avg_price)
                        ) * quantity
                        print(f"Profit/Loss for the sold quantity: {profit_loss}")

                        # Record the Sell in ClosedTrades
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )

                        # Add to TradeHistory for the sell transaction
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Sell",
                            quantity=quantity,
                            trade_price=trade_price,
                        )

                        # Adjust the existing trade
                        existing_trade.quantity -= Decimal(
                            quantity
                        )  # Deduct the sold quantity
                        existing_trade.invested_coin = Decimal(
                            existing_trade.quantity
                        ) * Decimal(
                            existing_trade.avg_price
                        )  # Update invested amount
                        existing_trade.save()

                        # Update BeetleCoins after the trade
                        beetle_coins.coins += Decimal(quantity) * Decimal(
                            existing_trade.avg_price
                        ) + Decimal(profit_loss)
                        beetle_coins.used_coins -= Decimal(quantity) * Decimal(
                            existing_trade.avg_price
                        )
                        beetle_coins.save()

                        # Adjust the margin if required
                        # margin.margin += (Decimal(margin_required) / existing_trade.quantity) * Decimal(quantity)
                        # margin.save()

                        message = f"Sold {quantity} quantities. Remaining quantity: {existing_trade.quantity}."

                        return Response(
                            {
                                "message": message,
                                "trade_history": TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "closed_trades": ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values(),
                            },
                            status=status.HTTP_200_OK,
                        )

                    # Scenario: Sell the same or less quantity than available (Standard Sell)
                    elif quantity == existing_trade.quantity:
                        # Calculate profit/loss for this transaction
                        profit_loss = (
                            float(trade_price) - float(existing_trade.avg_price)
                        ) * quantity
                        # profit_loss = (Decimal(trade_price) - existing_trade.avg_price) * Decimal(quantity)
                        print(f"Profit/Loss for the transaction: {profit_loss}")

                        # Record the Sell in ClosedTrades
                        ClosedTrades.objects.create(
                            trade=existing_trade,
                            product_type=existing_trade.product_type,
                            avg_price=existing_trade.avg_price,
                            sell_quantity=quantity,
                            sell_price=trade_price,
                            profit_loss=profit_loss,
                        )
                        remaining_quantity = quantity - existing_trade.quantity
                        # Add to TradeHistory for the sell transaction
                        TradeHistory.objects.create(
                            trade=existing_trade,
                            trade_type="Sell",
                            quantity=quantity,
                            trade_price=trade_price,
                        )
                        beetle_coins.coins += Decimal(existing_trade.invested_coin)+ - Decimal(
                            profit_loss
                        )
                        beetle_coins.used_coins -= Decimal(existing_trade.invested_coin)
                        beetle_coins.save()

                        # Adjust the existing trade quantity and invested coin
                        # existing_trade.quantity -= quantity
                        # existing_trade.invested_coin = existing_trade.quantity * existing_trade.avg_price
                        existing_trade.quantity -= Decimal(quantity)  # Ensure Decimal
                        existing_trade.invested_coin = Decimal(
                            existing_trade.quantity
                        ) * Decimal(existing_trade.avg_price)

                        # Add profit/loss to BeetleCoins
                        print(beetle_coins.coins, invested_amount)
                        # beetle_coins.coins += Decimal(quantity*trade_price)

                        # beetle_coins.coins += invested_amount

                        # If the trade is now fully completed, mark it as complete
                        if existing_trade.quantity == 0:
                            existing_trade.trade_status = "complete"
                            message = "Trade completed and recorded."
                        else:
                            message = "Partial trade executed and recorded."

                        # Save the updated trade state
                        existing_trade.save()

                        # Update BeetleCoins after the trade

                        

                        # margin.margin += margin_required
                        # margin.save()

                        # beetle_coins.coins += invested_amount  # invested_amount should be defined
                        # beetle_coins.used_coins -= (invested_amount - profit_loss)
                        # beetle_coins.save()

                        return Response(
                            {
                                "message": message,
                                "trade_history": TradeHistory.objects.filter(
                                    trade=existing_trade
                                ).values(),
                                "closed_trades": ClosedTrades.objects.filter(
                                    trade=existing_trade
                                ).values(),
                            },
                            status=status.HTTP_200_OK,
                        )

               
                elif (
                    trade_type == "Sell"
                    and existing_trade.trade_type == "Sell"
                    and existing_trade.trade_status == "incomplete"
                ):
                    

                    existing_trade.avg_price = (
                        Decimal(existing_trade.avg_price) * Decimal(existing_trade.quantity)
                        + Decimal(trade_price) * Decimal(quantity)
                    ) / (Decimal(existing_trade.quantity) + Decimal(quantity))
                    existing_trade.quantity += quantity
                    existing_trade.invested_coin = (
                        existing_trade.quantity * existing_trade.avg_price
                    )
                    existing_trade.save()
                    invested_amount_decimal = Decimal(str(invested_amount))
                    beetle_coins.coins -= invested_amount_decimal
                    beetle_coins.used_coins += invested_amount_decimal
                    beetle_coins.save()

                    # Add to TradeHistory
                    TradeHistory.objects.create(
                        trade=existing_trade,
                        trade_type="Sell",
                        quantity=quantity,
                        trade_price=trade_price,
                    )
                    margin.margin += margin_required
                    margin.save()
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
                elif (
                    trade_type == "Buy"
                    or trade_type == "Sell"
                    and existing_trade.quantity == 0
                    and existing_trade.trade_status == "completed"
                ):
                    print("here")
                    # Create a new trade since the existing one is complete
                    data["user"] = user.id  # Associate the new trade with the user
                    serializer = TradesTakenSerializer(
                        data=data
                    )  # Use serializer to validate and create new trade data

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

                        invested_amount_decimal = Decimal(invested_amount)

                        beetle_coins.coins -= invested_amount_decimal
                        beetle_coins.used_coins += invested_amount_decimal
                        beetle_coins.save()
                       

                        return Response(
                            {
                                "message": "New trade created as the previous one was complete.",
                                "data": TradesTakenSerializer(new_trade).data,
                            },
                            status=status.HTTP_201_CREATED,
                        )
                    else:
                        return Response(
                            serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )

                else:
                    return Response(
                        {"error": "Invalid trade update scenario."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            
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
            # beetle_coins.coins-=invested_amount
            # beetle_coins.used_coins+=invested_amount
            # beetle_coins.save()

            invested_amount_decimal = Decimal(invested_amount)

            beetle_coins.coins -= invested_amount_decimal
            beetle_coins.used_coins += invested_amount_decimal
            beetle_coins.save()

           
            # try:
            #     beetle_coins.use_coins(invested_amount)
            # except ValidationError as e:
            #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {"message": "New trade created.......", "data": serializer.data},
                status=status.HTTP_201_CREATED ,
            )
        else:
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        
        

class UserLimitOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit_orders = LimitOrder.objects.filter(user=user)
        serializer = LimitOrderSerializer(limit_orders, many=True)
        return Response(serializer.data)