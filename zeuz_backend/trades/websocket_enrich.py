# multiple users are allowed to
import asyncio
import websockets
import logging
import json
from .models import LimitOrder
from .serializers import LimitOrderSerializer
from .views import process_trade,process_futures
from asgiref.sync import sync_to_async

from datetime import datetime,time

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def is_within_trading_hours():
    """
    Check if the current time is between 9:15 AM and 3:15 PM.
    """
    current_time = datetime.now().time()
    start_time = time(9, 15)  # 9:15 AM
    end_time = time(21, 00)   # 3:30 PM
    return start_time <= current_time <= end_time

async def connect_and_send_websocket(uri, auth_payload, token_id, exchange, avg_price, instance_id,ssl_context,trade_type):
    """
    Function to establish a WebSocket connection and monitor price updates,
    while sending heartbeats to keep the connection alive.
    """
    print(f"Connecting to WebSocket for Instance ID: {instance_id}, Token ID: {token_id}")
    try:
        # Open WebSocket connection
        async with websockets.connect(uri,ssl=ssl_context) as websocket:
            # Authenticate
            await websocket.send(json.dumps(auth_payload))
            logger.info("Authentication sent: %s", auth_payload)

            # Subscribe to token_id and exchange
            subscription_payload = {
                "t": "t",
                "k": f"{exchange}|{token_id}",
            }
            await websocket.send(json.dumps(subscription_payload))
            logger.info("Subscription sent: %s", subscription_payload)

            # Heartbeat task to keep the WebSocket alive
            async def send_heartbeat():
                while True:
                    await asyncio.sleep(15)  # Send heartbeat every 60 seconds
                    heartbeat_payload = {"t": "h"}
                    try:
                        await websocket.send(json.dumps(heartbeat_payload))
                        logger.info("Heartbeat sent")
                    except Exception as e:
                        logger.error(f"Error sending heartbeat: {e}")
                        break

            # Run heartbeat and price monitoring concurrently
            heartbeat_task = asyncio.create_task(send_heartbeat())
            try:
                while True:
                    print("################################hitttttttttty################################")

                    # current_time = datetime.now().time()

                    # start_time = time(9, 15)  # 9:15 AM
                    # end_time = time(20, 00)  # 3:15 PM
                    response = await websocket.recv()
                    data = json.loads(response)
                    logger.info("WebSocket response: %s", data)
                    if not is_within_trading_hours():
                        print("################################")
                        await sync_to_async(LimitOrder.objects.filter(id=instance_id).update)(executed=True,status="COULD NOT HIT THE TARGET")
                        logger.info("Trading hours have ended. Stopping WebSocket monitoring.")
                        break

                    if "lp" in data :  # lp = last price
                        print("**************")
                        current_price = float(data["lp"])
                        logger.info(f"Current Price for {token_id}: {current_price}")

                        if (current_price <= avg_price and trade_type == "Buy") or (current_price >= avg_price and trade_type == "Sell"):


                            # Close WebSocket and update order as executed
                            await websocket.close()
                            logger.info(
                                f"Target price reached for {token_id}: {current_price} >= {avg_price}. Closing WebSocket."
                            )

                            # Cancel heartbeat task
                            heartbeat_task.cancel()

                            # Update the order as executed in the database
                            await sync_to_async(LimitOrder.objects.filter(id=instance_id).update)(executed=True)
                            instance = await sync_to_async(LimitOrder.objects.get)(id=instance_id)

                            serializer = LimitOrderSerializer(instance)
                            serialized_data = serializer.data
                            logger.info(f"Serialized Data: {serialized_data}")

                            # Process the trade (synchronously in a separate thread) this is working 
                            # response = await asyncio.to_thread(process_trade, data=serialized_data)
                            # logger.info(f"Process Trade Response: {response}")
                            if serialized_data.get('segment') == 'EQUITY':
                                # For 'EQUITY', process the trade
                                print("Processing equity lmts")                          
                                response = await asyncio.to_thread(process_trade, data=serialized_data)
                                logger.info(f"Process Trade Response: {response}")
                            elif serialized_data.get('segment') == 'FUT':
                                # For 'Futures', process futures
                                print("Processing futures lmts")
                                response = await asyncio.to_thread(process_futures, data=serialized_data)
                                logger.info(f"Process Futures Response: {response}")
                            else:
                                logger.info("Unknown segment type. No action taken.")
                            break


                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in WebSocket connection for Instance ID {instance_id}: {e}")
                heartbeat_task.cancel()  # Ensure heartbeat is stopped on error
    except Exception as e:
        logger.error(f"Failed to connect WebSocket for Instance ID {instance_id}: {e}")

async def manage_websockets(uri, auth_payload, token_data):
    """
    Manage multiple WebSocket connections concurrently for different token IDs.
    :param uri: WebSocket URI
    :param auth_payload: Authentication payload
    :param token_data: List of dictionaries with token_id, exchange, avg_price, and instance_id
    """
    tasks = []
    for data in token_data:
        token_id = data['token_id']
        exchange = data['exchange']
        avg_price = data['avg_price']
        instance_id = data['instance_id']
        trade_type = data['trade_type']

        # Create a task for each WebSocket connection
        task = asyncio.create_task(
            connect_and_send_websocket(uri, auth_payload, token_id, exchange, avg_price, instance_id, trade_type)
        )
        tasks.append(task)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)


def trigger_multiple_websockets(uri, auth_payload, token_data,ssl_context):
    """
    Runs WebSocket logic for multiple tokens in parallel.
    :param uri: WebSocket URI
    :param auth_payload: Authentication payload
    :param token_data: List of token details (token_id, exchange, avg_price, instance_id)
    """
    async def manage_websockets():
        tasks = []
        for token in token_data:    
            task = connect_and_send_websocket(
                uri=uri,
                auth_payload=auth_payload,
                token_id=token["token_id"],
                exchange=token["exchange"],
                avg_price=token["avg_price"],
                instance_id=token["instance_id"],
                trade_type=token["trade_type"],
                ssl_context=ssl_context,
            )
            tasks.append(task)
        await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(manage_websockets())