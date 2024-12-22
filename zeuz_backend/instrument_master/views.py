import csv
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UploadedFile, TradingInstrument


class CSVUploadView(APIView):
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        uploaded_file = UploadedFile.objects.create(file_name=file.name)

        try:
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)

            
            headers = next(reader, None)

            instruments_to_create = []

            for row in reader:
            
                if len(row) < 15:
                    continue

                try:
                    
                    instruments_to_create.append(TradingInstrument(
                        uploaded_file=uploaded_file,
                        token_id=row[0].strip(),
                        exchange=row[1].strip(),
                        trading_symbol=row[2].strip(),
                        series=row[3].strip() if row[3] else None,
                        script_name=row[4].strip() if row[4] else None,
                        ticker=row[5].strip() if row[5] else None,
                        # expiry_date=datetime.strptime(row[6].strip(), "%d-%b-%Y").date() if row[6].strip() else None,
                        expiry_date=datetime.strptime(row[6].strip(), "%d-%b-%y").date() if row[6].strip() else None,

                        option_type=row[7].strip() if row[7] else None,
                        segment=row[8].strip(),
                        lot_size=int(float(row[9].strip())) if row[9].strip() else 0,
                        tick_size=float(row[10].strip()) if row[10].strip() else 0.0,
                        strike_price=float(row[11].strip()) if row[11].strip() else None,
                        display_name=row[12].strip(),
                        company_name=row[13].strip() if row[13] else None,
                        instrument_name=row[14].strip() if row[14] else None,
                        isin_number=row[15].strip() if len(row) > 15 and row[15].strip() else None,
                    ))
                except ValueError as e:
                    return Response({
                        "error": f"Error processing row: {row}, {str(e)}"
                    }, status=status.HTTP_400_BAD_REQUEST)

    
            TradingInstrument.objects.bulk_create(instruments_to_create)

            return Response({"message": f"File processed successfully. {len(instruments_to_create)} records added."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Error processing file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TradingInstrument
from django.db.models import Q
from .serializers import TradingInstrumentSerializer
from rest_framework.permissions import AllowAny
# class TradingInstrumentSearchView(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request, *args, **kwargs):
#         exchange = request.query_params.get('exchange', None)
#         segment = request.query_params.get('segment', None)
#         script_name = request.query_params.get('script_name', None)

#         if exchange not in ['NSE', 'NFO']:
#             return Response({"detail": "Invalid exchange, please use NSE or NFO."}, status=status.HTTP_400_BAD_REQUEST)

#         # Start building the query
#         query = Q(exchange=exchange)

#         # Additional conditions for NFO
#         if exchange == 'NFO':
#             if segment == 'FUT':
#                 instruments = TradingInstrument.objects.filter(exchange='NFO', segment='FUT')
#             elif segment == 'OPT':
#                 filters = {'exchange': 'NFO', 'segment': 'OPT'}
#                 if script_name:
#                     filters['script_name'] = script_name
                
#                 instruments = TradingInstrument.objects.filter(**filters).values('script_name').distinct()



#         # Fetch and serialize the filtered results
#         instruments = TradingInstrument.objects.filter(query)
#         serializer = TradingInstrumentSerializer(instruments, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .models import TradingInstrument
# from .serializers import TradingInstrumentSerializer
# from django.db.models import Q

# class TradingInstrumentSearchView(APIView):
#     """
#     API to search for stocks based on NSE and NFO exchanges.
#     """
#     def get(self, request, *args, **kwargs):
#         exchange = request.query_params.get('exchange', None)
        
#         # Build the query
#         if exchange:
#             if exchange not in ['NSE', 'NFO']:
#                 return Response(
#                     {"detail": "Invalid exchange. Please use 'NSE' or 'NFO'."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             query = Q(exchange=exchange)
#         else:
#             query = Q(exchange__in=['NSE', 'NFO'])  # Default to both exchanges if no filter is provided
        
#         # Retrieve the filtered data
#         instruments = TradingInstrument.objects.filter(query)
        
#         # Serialize the data
#         serializer = TradingInstrumentSerializer(instruments, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


    



from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TradingInstrument
from collections import defaultdict
from datetime import date

class GroupedOptionsView(APIView):
    def get(self, request, *args, **kwargs):
        script_name = request.query_params.get('script_name', None)
        expiry_date = request.query_params.get('expiry_date', None)
        
        if not script_name:
            return Response({"error": "script_name is required"}, status=400)

        include_all = request.query_params.get('include_all', 'false').lower() == 'true'
        grouped_data = self.get_grouped_data(script_name, expiry_date, include_all)
        return Response(grouped_data)

    def get_grouped_data(self, script_name, expiry_date, include_all):
        options = TradingInstrument.objects.filter(script_name=script_name, segment='OPT').values()

        # Group data by expiry date
        grouped_by_expiry = defaultdict(lambda: {'expiry_date': None, 'options': []})
        unique_expiry_dates = set()  # Collect all unique expiry dates

        for option in options:
            expiry_date_option = option['expiry_date']
            unique_expiry_dates.add(expiry_date_option)  # Track all unique expiry dates

            strike_price = option['strike_price']
            option_type = option.get('option_type', '').upper()

            if not grouped_by_expiry[expiry_date_option]['expiry_date']:
                grouped_by_expiry[expiry_date_option]['expiry_date'] = expiry_date_option

            # Group by strike price and option type
            if option_type == 'CE':
                grouped_by_expiry[expiry_date_option]['options'].append({
                    'strike_price': strike_price,
                    'call': option,
                    'put': {}
                })
            elif option_type == 'PE':
                for entry in grouped_by_expiry[expiry_date_option]['options']:
                    if entry['strike_price'] == strike_price:
                        entry['put'] = option
                        break
                else:
                    grouped_by_expiry[expiry_date_option]['options'].append({
                        'strike_price': strike_price,
                        'call': {},
                        'put': option
                    })

        # Sort expiry dates
        sorted_expiries = sorted(unique_expiry_dates)

        # Handle filtering by expiry_date
        if expiry_date:
            if expiry_date not in grouped_by_expiry:
                return {
                    'unique_expiry_dates': sorted_expiries,
                    'grouped_data': []
                }
            return {
                'unique_expiry_dates': sorted_expiries,
                'grouped_data': [grouped_by_expiry[expiry_date]]
            }

        nearest_expiry = sorted_expiries[0] if sorted_expiries else None

        if not include_all:  # Return only the nearest expiry date data
            return {
                'unique_expiry_dates': sorted_expiries,
                'grouped_data': [grouped_by_expiry[nearest_expiry]] if nearest_expiry else []
            }

        # Prepare full grouped data
        grouped_data = [
            grouped_by_expiry[expiry_date]
            for expiry_date in sorted_expiries
        ]

        data = {
            'unique_expiry_dates': sorted_expiries,  # All unique expiry dates
            'grouped_data': grouped_data  # Full grouped data
        }

        

        # Final response structure
#         return Response(
#     {
#         'unique_expiry_dates': sorted_expiries,  # All unique expiry dates
#         'grouped_data': grouped_data  # Full grouped data
#     },
#     status=status.HTTP_200_OK
# # )
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .models import TradingInstrument

# class InstrumentSearchOptions(APIView):
#     def get(self, request, *args, **kwargs):
#         exchange = request.query_params.get('exchange')
#         segment = request.query_params.get('segment')

#         if not exchange or not segment:
#             return Response(
#                 {"error": "Both 'exchange' and 'segment' query parameters are required."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         # Filter instruments based on query params
#         instruments = TradingInstrument.objects.filter(exchange=exchange, segment=segment)

#         # Extract unique script names and remove None or blank values
#         unique_script_names = set(
#             instruments.values_list('script_name', flat=True)
#         )
#         unique_script_names = [name for name in unique_script_names if name]

#         # Structure the response
#         data = [{"script_name": name} for name in unique_script_names]

#         return Response(data, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TradingInstrument
from django.db.models import Q
from .serializers import TradingInstrumentSerializer
from rest_framework.permissions import AllowAny

class TradingInstrumentSearchView(APIView):

    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):

        exchange = request.query_params.get('exchange', None)
        segment = request.query_params.get('segment', None)
        print(exchange,segment)
        
        if exchange not in ['NSE', 'NFO']:
            
            return Response({"detail": "Invalid exchange, please use NSE or NFO."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        query = Q(exchange=exchange)
        
        
        if exchange == 'NFO' and segment:
            if segment not in ['FUT', 'OPT']:
                return Response({"detail": "Invalid segment for NFO, please use FUT or OPT."}, status=status.HTTP_400_BAD_REQUEST)
            query &= Q(segment=segment)
        
        instruments = TradingInstrument.objects.filter(query)


        # return Response(instrument_data, status=status.HTTP_200_OK)

        serializer = TradingInstrumentSerializer(instruments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)



