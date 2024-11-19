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
                        expiry_date=datetime.strptime(row[6].strip(), "%d-%b-%Y").date() if row[6].strip() else None,
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

        

        # instrument_data = [
        #     {
        #         "token_id": instrument.token_id,
        #         "exchange": instrument.exchange,
        #         "trading_symbol": instrument.trading_symbol,
        #         "series": instrument.series,
        #         "expiry_date": instrument.expiry_date,
        #         "option_type": instrument.option_type,
        #         "segment": instrument.segment,
        #         "lot_size": instrument.lot_size,
        #         "tick_size": instrument.tick_size,
        #         "strike_price": instrument.strike_price,
        #         "display_name": instrument.display_name,
        #         "company_name": instrument.company_name,
        #         "instrument_name": instrument.instrument_name,
        #         "isin_number": instrument.isin_number
        #     }
        #     for instrument in instruments
        # ]

        # return Response(instrument_data, status=status.HTTP_200_OK)

        serializer = TradingInstrumentSerializer(instruments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TradingInstrument
from .serializers import ScriptGroupedDataSerializer

class GroupedOptionsView(APIView):
    def get(self, request, *args, **kwargs):
        script_name = request.query_params.get('script_name', None)
        if not script_name:
            return Response({"error": "script_name is required"}, status=400)

        queryset = TradingInstrument.objects.filter(script_name=script_name, segment='OPT')
        serialized_data = ScriptGroupedDataSerializer({'script_name': script_name}).data
        return Response(serialized_data)
