# Currency Conversion API – Azure Functions (Python)

An Azure Functions v2 HTTP API written in Python that converts monetary amounts between currencies.

## Endpoints

### `GET /api/convert`

Convert an amount from one currency to another using query parameters.

| Parameter | Type   | Required | Description                    |
|-----------|--------|----------|--------------------------------|
| `amount`  | number | ✅       | Amount to convert              |
| `from`    | string | ✅       | Source currency code (e.g. USD)|
| `to`      | string | ✅       | Target currency code (e.g. EUR)|

**Example request:**
```
GET /api/convert?amount=100&from=USD&to=EUR
```

**Example response:**
```json
{
  "from": "USD",
  "to": "EUR",
  "amount": 100.0,
  "converted_amount": 92.0,
  "rate": 0.92,
  "source": "live"
}
```

### `POST /api/convert`

Same conversion but accepts a JSON body.

**Example request body:**
```json
{ "amount": 250, "from": "GBP", "to": "MAD" }
```

### `GET /api/currencies`

Returns the list of supported currency codes.

**Example response:**
```json
{
  "supported_currencies": ["AUD", "BRL", "CAD", "CHF", "CNY", "DKK", "EUR", "GBP", "HKD", "INR", "JPY", "KRW", "MAD", "MXN", "NOK", "NZD", "SEK", "SGD", "USD", "ZAR"],
  "count": 20
}
```

## Supported Currencies

| Code | Currency              |
|------|-----------------------|
| USD  | US Dollar             |
| EUR  | Euro                  |
| GBP  | British Pound         |
| JPY  | Japanese Yen          |
| CAD  | Canadian Dollar       |
| AUD  | Australian Dollar     |
| CHF  | Swiss Franc           |
| CNY  | Chinese Yuan          |
| INR  | Indian Rupee          |
| MXN  | Mexican Peso          |
| BRL  | Brazilian Real        |
| KRW  | South Korean Won      |
| SGD  | Singapore Dollar      |
| HKD  | Hong Kong Dollar      |
| NOK  | Norwegian Krone       |
| SEK  | Swedish Krona         |
| DKK  | Danish Krone          |
| NZD  | New Zealand Dollar    |
| ZAR  | South African Rand    |
| MAD  | Moroccan Dirham       |

## How it works

1. The API first attempts to fetch **live exchange rates** from [open.er-api.com](https://open.er-api.com) (free, no API key required).
2. If the live API is unavailable, it falls back to **static reference rates** bundled in the application.

## Local Development

### Prerequisites

- Python 3.11+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- `pip install -r requirements.txt`

### Run locally

```bash
cp local.settings.json.example local.settings.json
func start
```

Then test:
```bash
curl "http://localhost:7071/api/convert?amount=100&from=USD&to=EUR"
```

## Deploy to Azure

```bash
az login
az functionapp create --resource-group <rg> --consumption-plan-location <region> \
  --runtime python --runtime-version 3.11 --functions-version 4 \
  --name <app-name> --storage-account <storage>
func azure functionapp publish <app-name>
```