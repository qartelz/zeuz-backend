# # import csv
# # from datetime import datetime
# # from celery import shared_task
# # from .models import UploadedFile, TradingInstrument

# # @shared_task
# # def process_csv_file(uploaded_file_id,file):
# #     try:
# #         uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        
# #         # with open(uploaded_file.file.path, 'r', encoding='utf-8') as file:
# #         decoded_file = file.read().decode('utf-8').splitlines()
# #         reader = csv.reader(file)
# #         headers = next(reader, None)

# #         instruments_to_create = []
# #         for row in reader:
# #             if len(row) < 15:
# #                 continue

# #             instruments_to_create.append(TradingInstrument(
# #                 uploaded_file=uploaded_file,
# #                 token_id=row[0].strip(),
# #                 exchange=row[1].strip(),
# #                 trading_symbol=row[2].strip(),
# #                 series=row[3].strip() if row[3] else None,
# #                 script_name=row[4].strip() if row[4] else None,
# #                 ticker=row[5].strip() if row[5] else None,
# #                 expiry_date=datetime.strptime(row[6].strip(), "%d-%b-%Y").date() if row[6].strip() else None,
# #                 option_type=row[7].strip() if row[7] else None,
# #                 segment=row[8].strip(),
# #                 lot_size=int(float(row[9].strip())) if row[9].strip() else 0,
# #                 tick_size=float(row[10].strip()) if row[10].strip() else 0.0,
# #                 strike_price=float(row[11].strip()) if row[11].strip() else None,
# #                 display_name=row[12].strip(),
# #                 company_name=row[13].strip() if row[13] else None,
# #                 instrument_name=row[14].strip() if row[14] else None,
# #                 isin_number=row[15].strip() if len(row) > 15 and row[15].strip() else None,
# #             ))

# #         # Bulk create all instruments
# #         TradingInstrument.objects.bulk_create(instruments_to_create)

# #         uploaded_file.status = "processed"
# #         uploaded_file.save()

# #     except Exception as e:
# #         uploaded_file.status = "error"
# #         uploaded_file.error_message = str(e)
# #         uploaded_file.save()


# # from celery import shared_task
# # @shared_task
# # def test_task():
# #     print("Celery is working!")

# from celery import shared_task
# import csv
# from .models import UploadedFile, TradingInstrument
# from datetime import datetime

# @shared_task
# def process_csv_file(uploaded_file_id, file_content):
#     try:
#         # Retrieve the uploaded file record from the database
#         uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
#         print(file_content)
#         # Process the CSV content
#         decoded_file = file_content.splitlines()
#         reader = csv.reader(decoded_file)
#         headers = next(reader, None)

#         instruments_to_create = []
#         for row in reader:
#             if len(row) < 15:
#                 continue

#             instruments_to_create.append(TradingInstrument(
#                 uploaded_file=uploaded_file,
#                 token_id=row[0].strip(),
#                 exchange=row[1].strip(),
#                 trading_symbol=row[2].strip(),
#                 series=row[3].strip() if row[3] else None,
#                 script_name=row[4].strip() if row[4] else None,
#                 ticker=row[5].strip() if row[5] else None,
#                 expiry_date=datetime.strptime(row[6].strip(), "%d-%b-%Y").date() if row[6].strip() else None,
#                 option_type=row[7].strip() if row[7] else None,
#                 segment=row[8].strip(),
#                 lot_size=int(float(row[9].strip())) if row[9].strip() else 0,
#                 tick_size=float(row[10].strip()) if row[10].strip() else 0.0,
#                 strike_price=float(row[11].strip()) if row[11].strip() else None,
#                 display_name=row[12].strip(),
#                 company_name=row[13].strip() if row[13] else None,
#                 instrument_name=row[14].strip() if row[14] else None,
#                 isin_number=row[15].strip() if len(row) > 15 and row[15].strip() else None,
#             ))

#         # Bulk create all instruments
#         TradingInstrument.objects.bulk_create(instruments_to_create)

#         uploaded_file.status = "processed"
#         uploaded_file.save()


#     except Exception as e:
#         uploaded_file.status = "error"
#         uploaded_file.error_message = str(e)
#         uploaded_file.save()


import logging
from celery import shared_task
import csv
from datetime import datetime
from .models import UploadedFile, TradingInstrument  # Adjust import paths

logger = logging.getLogger(__name__)

@shared_task
def process_csv_file(uploaded_file_id, file_content):
    try:
        # Retrieve the uploaded file record from the database
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
        logger.info(f"Started processing uploaded file: {uploaded_file_id}")
        print(file_content)

        # Process the CSV content
        decoded_file = file_content.splitlines()
        reader = csv.reader(decoded_file)
        headers = next(reader, None)
        logger.info(f"CSV headers: {headers}")

        instruments_to_create = []
        row_count = 0

        for row in reader:
            row_count += 1
            if len(row) < 15:
                logger.warning(f"Skipping incomplete row {row_count}: {row}")
                continue

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

            if row_count % 100 == 0:  # Log every 100 rows
                logger.info(f"Processed {row_count} rows.")

        # Bulk create all instruments
        TradingInstrument.objects.bulk_create(instruments_to_create)
        logger.info(f"Successfully created {len(instruments_to_create)} instruments.")

        uploaded_file.status = "processed"
        uploaded_file.save()
        logger.info(f"File processing completed for file ID: {uploaded_file_id}")

    except Exception as e:
        logger.error(f"Error processing file ID {uploaded_file_id}: {e}")
        uploaded_file.status = "error"
        uploaded_file.error_message = str(e)
        uploaded_file.save()
