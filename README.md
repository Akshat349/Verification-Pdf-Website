# Change Declaration & Verification System 📄✅

A Django-based web application that uses **Computer Vision (OpenCV)** and **OCR (Tesseract)** to automatically verify physical declaration forms. The system ensures that uploaded PDFs contain specific keywords and have been physically signed and stamped in the designated areas.

## 🚀 Features

- **Automated Document Verification**: Checks for the "CHANGE DECLARATION FORM" header.
- **Signature & Stamp Detection**: Uses pixel density analysis to confirm the presence of ink in the "Verification Area".
- **Dynamic PDF Preview**: Real-time preview of the uploaded document before submission.
- **Verification History**: A logged report of all successful and failed attempts with specific error reasons.
- **Glassmorphism UI**: A modern, professional interface built with Tailwind CSS.

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Computer Vision**: OpenCV, NumPy
- **OCR**: PyTesseract
- **PDF Processing**: PyMuPDF (fitz)
- **Frontend**: Tailwind CSS, JavaScript (Fetch API)
- **Database**: SQLite (Default)

## 📋 Prerequisites

Before running this project, ensure you have the following installed:
- Python 3.8+
- [Tesseract OCR Engine](https://github.com/UB-Mannheim/tesseract/wiki)
  - *Note: Remember to update the Tesseract path in `views.py` to match your installation.*

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/Akshat349/Verification-Pdf-Website.git](https://github.com/Akshat349/Verification-Pdf-Website.git)
   cd Verification-Pdf-Website
