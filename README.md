# SFP ISIR and NSLDS Automator

An automated processing tool built with Python and Streamlit to parse, validate, and manage **Institutional Student Information Record (ISIR)** and **National Student Loan Data System (NSLDS)** data.

## 🚀 Overview
This application streamlines the handling of student data by breaking down complex records into manageable sections. It is designed for efficiency, ensuring that financial aid data is categorized accurately and is ready for reporting or integration.

## 📁 Project Structure
```text
sfp-isir-and-nslds-automator/
├── main2.py                 # Primary Streamlit Application
├── requirements.txt         # Project Dependencies
└── sections/                # Logic Modules
    ├── __init__.py
    ├── student_demographics.py
    ├── student_financials.py
    ├── student_identity.py
    ├── student_non_financial.py
    └── transaction_id.py
