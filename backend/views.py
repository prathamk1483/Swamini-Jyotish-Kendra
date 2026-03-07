import json
import os
import uuid
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# --- 1. HELPER: CONNECT TO GOOGLE SHEETS SAFELY ---
def get_worksheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Build the credential dictionary from environment variables
    # We use .replace('\\n', '\n') because some env parsers escape the newline characters
    google_creds = {
        "type": "service_account",
        "project_id": os.environ.get("GOOGLE_PROJECT_ID"),
        "private_key": os.environ.get("GOOGLE_PRIVATE_KEY", "").replace('\\n', '\n'),
        "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    # Use from_service_account_info instead of from_service_account_file
    creds = Credentials.from_service_account_info(google_creds, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("SwaminiJyotishKaryalayBackendData").sheet1


# --- 2. PAGE VIEW: DASHBOARD ---
def index(request):
    # We no longer load data here because the frontend JavaScript fetches it via /api/loadAll/
    # This makes the page load instantly!
    return render(request, 'dashboard.html')


# --- 3. PAGE VIEW: KUNDALI EDITOR ---
def kundali_editor(request, record_id=None):
    # Renders the editor page. If record_id exists, JS will fetch the data.
    return render(request, 'index.html', {'record_id': record_id})


# --- 4. API VIEW: SAVE / UPDATE DATA ---
@csrf_exempt
def api_save_kundali(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            record_id = data.get('record_id')
            client_name = data.get('client_name', 'नवीन ग्राहक (New Client)')
            status = data.get('status', 'Draft')
            last_updated = datetime.now().strftime("%d-%m-%Y %I:%M %p")
            
            form_json = json.dumps(data.get('form_data', {}))
            ws = get_worksheet()

            if record_id:
                # Update existing record
                try:
                    cell = ws.find(record_id, in_column=1)
                    # Use standard gspread update syntax
                    ws.update(f'B{cell.row}:E{cell.row}', [[client_name, status, last_updated, form_json]])
                except gspread.exceptions.CellNotFound:
                    ws.append_row([record_id, client_name, status, last_updated, form_json])
            else:
                # Create new record
                record_id = str(uuid.uuid4())[:8]
                ws.append_row([record_id, client_name, status, last_updated, form_json])

            return JsonResponse({'status': 'success', 'record_id': record_id})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)


# --- 5. API VIEW: LOAD DATA ---
def api_load_kundali(request, record_id):
    if request.method == 'GET':
        try:
            ws = get_worksheet()
            cell = ws.find(record_id, in_column=1)
            row_values = ws.row_values(cell.row)
            
            # Index 4 is Column E (Form_JSON_Data)
            if len(row_values) >= 5:
                form_data = json.loads(row_values[4])
                return JsonResponse({'status': 'success', 'form_data': form_data})
            else:
                return JsonResponse({'status': 'error', 'message': 'Data empty'}, status=500)
                
        except gspread.exceptions.CellNotFound:
            return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# --- 6. API VIEW: DELETE DATA ---
@csrf_exempt
def api_delete_kundali(request, record_id):
    try:
        ws = get_worksheet()
        cell = ws.find(record_id, in_column=1)
        ws.delete_rows(cell.row)
        # Redirect back to dashboard after deleting
        return redirect('/') 
    except gspread.exceptions.CellNotFound:
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# --- 7. API VIEW: LOAD ALL (BULLETPROOF METHOD) ---
def api_load_all(request):
    if request.method == 'GET':
        try:
            ws = get_worksheet()
            
            # get_all_values() returns a raw List of Lists. 
            # This completely ignores headers, so typos in row 1 won't break the app!
            all_rows = ws.get_all_values() 
            
            records = []
            for index, row in enumerate(all_rows):
                # Skip empty rows
                if not row or str(row[0]).strip() == '':
                    continue
                
                # Check if this row looks like a Header row (contains the word "Record") and skip it
                if index == 0 and "record" in str(row[0]).lower():
                    continue
                
                # Pad the row with empty strings just in case some columns are blank
                padded_row = row + [''] * (4 - len(row))
                
                # Manually map the columns to the dictionary keys the frontend expects
                records.append({
                    'Record_ID': padded_row[0],
                    'Client_Name': padded_row[1] if padded_row[1] else "Unknown",
                    'Status': padded_row[2] if padded_row[2] else "Draft",
                    'Last_Updated': padded_row[3] if padded_row[3] else ""
                })
            
            # Sort records so newest are at the top
            records.sort(key=lambda x: str(x.get('Last_Updated', '')), reverse=True)
            
            return JsonResponse({'status': 'success', 'records': records})
        except Exception as e:
            print(f"API Load All Error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)