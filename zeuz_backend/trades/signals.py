# import threading
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import LimitOrder
# from .websocket_enrich import trigger_multiple_websockets
# from adminlogin.models import Tokens


# @receiver(post_save, sender=LimitOrder)
# def limit_order_created(sender, instance, created, **kwargs):
#     """
#     Signal to trigger WebSocket connection when a new LimitOrder is created.
#     """
#     try:
#         token_instance = Tokens.objects.first()  # Fetch the first token in the database
#         if not token_instance or not token_instance.broadcast_token or not token_instance.broadcast_userid:
#             raise ValueError("Broadcast token or user ID is missing in the Tokens model.")
#     except Tokens.DoesNotExist:
#         raise ValueError("No valid Tokens instance found in the database.")
#     if created and not instance.executed:
#         # Only trigger for new instances with executed=False
#         uri = "wss://orca-uatwss.enrichmoney.in/ws"
#         auth_payload = {
#             "t": "c",
#             "uid": token_instance.broadcast_userid,
#             "actid": token_instance.broadcast_userid,
#             "susertoken": token_instance.broadcast_token, # Replace with actual token
#             "source": "API",
#         }

#         # Construct token_data as a list of dictionaries
#         token_data = [{
#             "token_id": instance.token_id,
#             "exchange": instance.exchange,
#             "avg_price": instance.avg_price,
#             "instance_id": instance.id,
#         }]

#         # Start WebSocket connections in a separate thread
#         thread = threading.Thread(
#             target=trigger_multiple_websockets,
#             args=(uri, auth_payload, token_data),
#         )
#         thread.start()

import threading
import ssl
import json
import websockets
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LimitOrder
from .websocket_enrich import trigger_multiple_websockets
from adminlogin.models import Tokens


def get_ssl_context():
    """Create an SSL context with SSL verification disabled."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


@receiver(post_save, sender=LimitOrder)
def limit_order_created(sender, instance, created, **kwargs):
    """
    Signal to trigger WebSocket connection when a new LimitOrder is created.
    """
    try:
        # Fetch the first token in the database
        token_instance = Tokens.objects.first()
        if not token_instance or not token_instance.broadcast_token or not token_instance.broadcast_userid:
            raise ValueError("Broadcast token or user ID is missing in the Tokens model.")
    except Tokens.DoesNotExist:
        raise ValueError("No valid Tokens instance found in the database.")

    if created and not instance.executed:
        # Only trigger for new instances with executed=False
        uri = "wss://orca-uatwss.enrichmoney.in/ws"
        auth_payload = {
            "t": "c",
            "uid": token_instance.broadcast_userid,
            "actid": token_instance.broadcast_userid,
            "susertoken": token_instance.broadcast_token,  # Replace with actual token
            "source": "API",
        }

        # Construct token_data as a list of dictionaries
        token_data = [{
            "token_id": instance.token_id,
            "exchange": instance.exchange,
            "avg_price": instance.avg_price,
            "instance_id": instance.id,
        }]

        # Get the SSL context
        ssl_context = get_ssl_context()

        # Start WebSocket connections in a separate thread
        thread = threading.Thread(
            target=trigger_multiple_websockets,
            args=(uri, auth_payload, token_data, ssl_context),  # Pass SSL context
        )
        thread.start()