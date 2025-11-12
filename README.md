# Firecrawl Web Scraper

A simple web scraping tool built with Streamlit that allows you to extract information from any website.

## Features

- Extract page title, status code, and number of links
- Preview website text content
- View raw HTML
- Simple and intuitive interface

## Installation

1. Clone this repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Activate your virtual environment if not already activated:
   ```bash
   .venv\Scripts\activate  # On Windows
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
3. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)
4. Enter a website URL and click "Scrape Website"

## Requirements

- Python 3.7+
- See requirements.txt for Python package dependencies

## Note

This tool is for educational purposes only. Please respect website terms of service and robots.txt files when scraping.
