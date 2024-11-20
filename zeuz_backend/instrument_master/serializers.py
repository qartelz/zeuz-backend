from rest_framework import serializers
from .models import UploadedFile, TradingInstrument

class TradingInstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingInstrument
        fields = "__all__"


# from rest_framework import serializers
# from collections import defaultdict
# from .models import TradingInstrument  # Replace with your actual model name

# class GroupedOptionsSerializer(serializers.Serializer):
#     expiry_date = serializers.DateField()
#     strike_price = serializers.DecimalField(max_digits=10, decimal_places=2)
#     call = serializers.DictField()
#     put = serializers.DictField()

# class OptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TradingInstrument
#         fields = '__all__'

# from collections import defaultdict
# from rest_framework import serializers
# from datetime import date

# class ScriptGroupedDataSerializer(serializers.Serializer):
#     script_name = serializers.CharField()
#     grouped_data = serializers.SerializerMethodField()

#     def get_grouped_data(self, obj):
#         # Fetch options with the given script_name and segment='OPT'
#         options = TradingInstrument.objects.filter(script_name=obj['script_name'], segment='OPT').values()
        
#         # Group data based on unique expiry_date
#         grouped_by_expiry = defaultdict(lambda: {'expiry_date': None, 'options': []})
#         today = date.today()  # Current date for reference

#         for option in options:
#             expiry_date = option['expiry_date']
#             strike_price = option['strike_price']
#             option_type = option.get('option_type', '').upper()

#             # Initialize expiry date grouping if not already set
#             if not grouped_by_expiry[expiry_date]['expiry_date']:
#                 grouped_by_expiry[expiry_date]['expiry_date'] = expiry_date

#             # Group by call or put
#             if option_type == 'CE':
#                 grouped_by_expiry[expiry_date]['options'].append({
#                     'strike_price': strike_price,
#                     'call': option,
#                     'put': {}
#                 })
#             elif option_type == 'PE':
#                 # Match an existing call with the same strike price
#                 for entry in grouped_by_expiry[expiry_date]['options']:
#                     if entry['strike_price'] == strike_price:
#                         entry['put'] = option
#                         break
#                 else:
#                     grouped_by_expiry[expiry_date]['options'].append({
#                         'strike_price': strike_price,
#                         'call': {},
#                         'put': option
#                     })

#         # Separate data for the earliest expiry date (e.g., "2024-11-27") and others
#         earliest_expiry = sorted(grouped_by_expiry.keys())[0] if grouped_by_expiry else None
#         grouped_data = {
#             'earliest_expiry': grouped_by_expiry.pop(earliest_expiry) if earliest_expiry else None,
#             'other_expiries': sorted(grouped_by_expiry.values(), key=lambda x: x['expiry_date'])
#         }

#         return grouped_data

class TradingInstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingInstrument
        fields = ['script_name']
