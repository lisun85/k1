# 📄 K-1 Tax Document Reader

An intelligent document processing system that automatically extracts structured data from Schedule K-1 tax forms using OCR, pattern matching, and machine learning techniques.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🚀 What This App Does

The **K-1 Reader** transforms messy PDF tax documents into clean, structured data. Simply upload a K-1 form and get:

- **Automatic data extraction** from both digital and scanned PDFs
- **Smart field recognition** for all standard K-1 boxes and fields
- **Confidence scoring** to show extraction reliability
- **Multiple export formats** (JSON, CSV) for integration with tax software
- **Professional web interface** built with Streamlit

## 📸 Screenshots

### Upload Interface
Upload your K-1 PDF with drag & drop functionality and real-time processing status.

### Extraction Results
View extracted data organized by categories with confidence indicators and validation checks.

### Data Analysis
Comprehensive analysis with income breakdowns, field completeness metrics, and quality assessments.

## 📋 Features

### 🔍 **Intelligent Extraction**
- **Dual-method processing**: PDF text extraction + OCR fallback
- **Pattern matching**: 50+ regex patterns for K-1 fields
- **Quality assessment**: Automatic confidence scoring
- **Form type detection**: Identifies different K-1 variations - 1065, 1120S (coming soon), 1041 (coming soon)

### 📊 **Data Extracted**
- **Entity Information**: Partnership/Corporation name, EIN, address
- **Partner Details**: Name, SSN/EIN, ownership percentages
- **Income Items**: All K-1 boxes (1-20+) including:
  - Box 1: Ordinary business income/loss
  - Box 2: Net rental real estate income/loss
  - Box 3: Other net rental income/loss
  - Box 4: Guaranteed payments
  - Box 5: Interest income
  - Box 6: Dividends (ordinary & qualified)
  - Box 7: Royalties
  - Boxes 8-11: Capital gains and other income
  - **Capital Account**: Beginning/ending balances, contributions, distributions

### 🎯 **User Experience**
- **Streamlit Interface**: Clean, professional web application
- **Real-time Progress**: Live extraction status with emoji indicators
- **Field Validation**: Highlights successfully extracted vs. missing data
- **Export Options**: Download as JSON or CSV
- **Confidence Indicators**: Visual quality scores for reliability
- **Processing History**: Track all uploaded documents and results

### 🔧 **Technical Features**
- **Multi-library PDF processing**: PyPDF2 for maximum compatibility
- **Advanced OCR**: Tesseract with optimized settings for tax documents (300 DPI, PSM 6)
- **Robust error handling**: Graceful fallbacks and detailed logging
- **Type-safe data models**: Pydantic validation for all extracted fields


## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit** for the beautiful web interface framework
- **Tesseract OCR** for optical character recognition
- **pdfplumber & PyPDF2** for PDF processing capabilities
- **Pydantic** for data validation and type safety



**Built with ❤️ for tax professionals and individuals who need to process K-1 forms efficiently.**
