import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import pytesseract
from django.shortcuts import render
from django.http import JsonResponse
from .forms import PDFUploadForm
from .models import VerificationHistory
from django.views.decorators.http import require_POST
# Set Tesseract Path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def home(request):
    return render(request, 'home.html')

def success_page(request):
    return render(request, 'pdf_veri/success.html')

def declaration_view(request):
    return render(request, 'pdf_veri/declaration.html')

def report_view(request):
    # Fetch history from database to show in the template
    history = VerificationHistory.objects.all().order_by('-timestamp')
    return render(request, 'pdf_veri/report_details.html', {'history': history})
@require_POST
def clear_history(request):
    password = request.POST.get('password')
    if password == "123456":
        VerificationHistory.objects.all().delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'message': 'Incorrect Password!'})

def verify_pdf_no_change(request):
    return handle_pdf_verification(request, change_type="NO-CHANGE")

def verify_pdf_change(request):
    return handle_pdf_verification(request, change_type="CHANGE")

def handle_pdf_verification(request, change_type):
    result = None
    errors = []

    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data['pdf_file']

            # Basic Validation
            if not pdf_file.name.lower().endswith('.pdf'):
                errors.append("❌ File must be a PDF.")
            elif pdf_file.size > 10 * 1024 * 1024:
                errors.append("❌ PDF must be under 10 MB.")
            else:
                try:
                    # Run the OCR Pipeline
                    pdf_file.seek(0)
                    pipeline_results = verify_pdf_full_pipeline(pdf_file)
                    
                    if pipeline_results['final_result']:
                        result = pipeline_results['reason'][0]
                    else:
                        errors.extend(pipeline_results['reason'])
                    
                    # --- DATABASE SAVING LOGIC ---
                    status_text = "Success" if pipeline_results['final_result'] else "Error"
                    detail_text = result if pipeline_results['final_result'] else " | ".join(errors)
                    
                    VerificationHistory.objects.create(
                        filename=pdf_file.name,
                        change_type=change_type.upper(),
                        status=status_text,
                        details=detail_text
                    )
                    # -----------------------------

                except Exception as e:
                    errors.append(f"❌ Error while verifying PDF: {str(e)}")
        else:
            errors.append("❌ Invalid form.")

        # AJAX response for the frontend
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': not errors,
                'errors': errors,
                'result': result,
                'change_type': change_type
            })

    else:
        form = PDFUploadForm()

    return render(request, 'pdf_veri/verify_pdf.html', {
        'form': form,
        'result': result,
        'errors': errors,
        'change_type': change_type
    })

def verify_pdf_full_pipeline(pdf_file):
    results = {
        "text_found": False,
        "blank_box_found": False,
        "signature_found": False,
        "stamp_found": False,
        "final_result": False,
        "reason": []
    }

    # Load PDF
    pdf_content = pdf_file.read()
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    image = cv2.cvtColor(
        np.array(Image.frombytes("RGB", [pix.width, pix.height], pix.samples)),
        cv2.COLOR_RGB2BGR
    )
    doc.close()

    # Step 1: Find Main Frame
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV) # Adjusted threshold
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        cnt = max(contours, key=cv2.contourArea)
        x, y, box_w, box_h = cv2.boundingRect(cnt)
        outer_box = image[y:y + box_h, x:x + box_w]
    else:
        results['reason'].append("❌ Main Frame (outer box) not found.")
        return results

    # Step 2: Detect Header (Improved Fuzzy Search)
    top_roi = outer_box[0:int(box_h * 0.4), :] # Increased scan area
    header_text = pytesseract.image_to_string(top_roi).upper()
    
    # Check for keywords even if OCR makes minor mistakes
    keywords = ["CHANGE", "CHNAGE", "DECLARATION", "FORM"]
    if any(k in header_text for k in keywords):
        results["text_found"] = True
    else:
        results['reason'].append("❌ Keyword 'CHANGE DECLARATION FORM' not found in header.")

    # Step 3 & 4: Signature & Stamp (Fixed Area and Logic)
    # Scan the entire bottom section for better detection of the "Blank Box"
    bottom_section = outer_box[int(box_h * 0.7):, :]
    gray_b = cv2.cvtColor(bottom_section, cv2.COLOR_BGR2GRAY)
    _, thresh_b = cv2.threshold(gray_b, 180, 255, cv2.THRESH_BINARY_INV)
    
    contours_b, _ = cv2.findContours(thresh_b, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours_b:
        area = cv2.contourArea(cnt)
        if area < 500: continue # Ignore small noise
        
        bx, by, bw, bh = cv2.boundingRect(cnt)
        roi_segment = thresh_b[by:by + bh, bx:bx + bw]
        
        density = cv2.countNonZero(roi_segment) / (bw * bh)

        # A 'Blank Box' is a large rectangle with very little ink (the empty borders)
        if 0.01 < density < 0.15 and bw > 100:
            results['blank_box_found'] = True
            
        # Signature/Stamp: High density (>20% to be safer) in the bottom right
        elif density > 0.20 and bx > (bottom_section.shape[1] // 2):
            # Check if it's in the left or right part of the verification area
            if bx < (bottom_section.shape[1] * 0.75):
                results['signature_found'] = True
            else:
                results['stamp_found'] = True

    # Reporting Errors
    if not results['blank_box_found']: results['reason'].append("❌ Structural blank box not detected.")
    if not results['signature_found']: results['reason'].append("❌ Signature not detected.")
    if not results['stamp_found']:     results['reason'].append("❌ Stamp not detected.")

    if all([results['text_found'], results['blank_box_found'], results['signature_found'], results['stamp_found']]):
        results['final_result'] = True
        results['reason'] = ["✅ PDF verified successfully."]

    return results