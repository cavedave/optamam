# Fair Division Calculator

A web application for calculating fair divisions of items among people, supporting both divisible and indivisible items.

## Features

- Support for both divisible and indivisible items
- Interactive web interface
- Real-time calculations
- CSV export of results
- Maximin optimization strategy

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Open your browser and navigate to `http://localhost:8000`

## Usage

1. Enter the names of people and items (comma-separated)
2. For each item:
   - Mark whether it's divisible or not
   - Enter each person's valuation of the item
3. Click "Calculate Fair Division" to see the results
4. Download the results as CSV if needed

## API

The application provides a REST API endpoint for fair division calculations:

- POST `/api/calculate`
  - Input: JSON with people names, item names, valuations, and divisible flags
  - Output: JSON with allocation results and worst satisfaction value

## Development

The project structure is as follows:

```
optamam/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   └── routes/         # API endpoints
│   ├── core/
│   │   └── fair_division.py # Core logic
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
└── requirements.txt
``` 