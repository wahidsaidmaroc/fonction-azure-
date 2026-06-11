import json
import logging
import os

import azure.functions as func
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Fallback exchange rates relative to USD (used when external API is unavailable)
FALLBACK_RATES_USD = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.50,
    "CAD": 1.36,
    "AUD": 1.53,
    "CHF": 0.89,
    "CNY": 7.24,
    "INR": 83.12,
    "MXN": 17.15,
    "BRL": 4.97,
    "KRW": 1325.0,
    "SGD": 1.34,
    "HKD": 7.82,
    "NOK": 10.55,
    "SEK": 10.42,
    "DKK": 6.88,
    "NZD": 1.63,
    "ZAR": 18.63,
    "MAD": 10.06,
}

EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/{base}"


def get_exchange_rates(base_currency: str) -> dict:
    """Fetch live exchange rates from open.er-api.com, falling back to static rates."""
    try:
        url = EXCHANGE_RATE_API_URL.format(base=base_currency.upper())
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("result") == "success":
                return {"source": "live", "rates": data["rates"]}
    except requests.RequestException as exc:
        logging.warning("Could not fetch live rates: %s", exc)

    # Convert fallback rates to the requested base currency
    base = base_currency.upper()
    if base not in FALLBACK_RATES_USD:
        return {}
    base_rate = FALLBACK_RATES_USD[base]
    rates = {currency: rate / base_rate for currency, rate in FALLBACK_RATES_USD.items()}
    return {"source": "fallback", "rates": rates}


@app.route(route="convert", methods=["GET", "POST"])
def convert_currency(req: func.HttpRequest) -> func.HttpResponse:
    """
    Convert an amount from one currency to another.

    Query parameters (GET) or JSON body (POST):
      - amount      : numeric amount to convert (required)
      - from        : source currency code, e.g. USD (required)
      - to          : target currency code, e.g. EUR (required)

    Returns JSON:
      {
        "from": "USD",
        "to": "EUR",
        "amount": 100,
        "converted_amount": 92.0,
        "rate": 0.92,
        "source": "live" | "fallback"
      }
    """
    try:
        # Support both GET query params and POST JSON body
        if req.method == "POST":
            try:
                body = req.get_json()
            except ValueError:
                return func.HttpResponse(
                    json.dumps({"error": "Invalid JSON body"}),
                    status_code=400,
                    mimetype="application/json",
                )
            amount_str = str(body.get("amount", ""))
            from_currency = str(body.get("from", "")).strip().upper()
            to_currency = str(body.get("to", "")).strip().upper()
        else:
            amount_str = req.params.get("amount", "")
            from_currency = req.params.get("from", "").strip().upper()
            to_currency = req.params.get("to", "").strip().upper()

        # Validate inputs
        if not amount_str or not from_currency or not to_currency:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Missing required parameters: 'amount', 'from', 'to'",
                        "example": "/api/convert?amount=100&from=USD&to=EUR",
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        try:
            amount = float(amount_str)
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "'amount' must be a valid number"}),
                status_code=400,
                mimetype="application/json",
            )

        if amount < 0:
            return func.HttpResponse(
                json.dumps({"error": "'amount' must be non-negative"}),
                status_code=400,
                mimetype="application/json",
            )

        # Fetch rates for the source currency
        rates_data = get_exchange_rates(from_currency)
        if not rates_data:
            return func.HttpResponse(
                json.dumps({"error": f"Currency '{from_currency}' is not supported"}),
                status_code=400,
                mimetype="application/json",
            )

        rates = rates_data["rates"]
        if to_currency not in rates:
            return func.HttpResponse(
                json.dumps({"error": f"Currency '{to_currency}' is not supported"}),
                status_code=400,
                mimetype="application/json",
            )

        rate = rates[to_currency]
        converted_amount = round(amount * rate, 6)

        result = {
            "from": from_currency,
            "to": to_currency,
            "amount": amount,
            "converted_amount": converted_amount,
            "rate": rate,
            "source": rates_data["source"],
        }
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as exc:
        logging.exception("Unexpected error in convert_currency")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="currencies", methods=["GET"])
def list_currencies(req: func.HttpRequest) -> func.HttpResponse:
    """
    Return the list of supported currency codes.
    Uses the fallback static list for a fast, dependency-free response.
    """
    supported = sorted(FALLBACK_RATES_USD.keys())
    return func.HttpResponse(
        json.dumps({"supported_currencies": supported, "count": len(supported)}),
        status_code=200,
        mimetype="application/json",
    )
