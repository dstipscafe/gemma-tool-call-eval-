"""
Mock handlers that return plausible fake responses for each tool.
These are used to provide tool results back to the model during evaluation,
but their content doesn't affect scoring — only the model's tool call is evaluated.
"""

import json

MOCK_RESPONSES = {
    "get_current_weather": lambda args: json.dumps({
        "city": args.get("city", "Unknown"),
        "temperature": 22,
        "unit": "celsius",
        "condition": "partly cloudy",
        "humidity": 65,
    }),
    "get_exchange_rate": lambda args: json.dumps({
        "from": args.get("from_currency", "USD"),
        "to": args.get("to_currency", "EUR"),
        "rate": 0.92,
        "timestamp": "2025-01-15T12:00:00Z",
    }),
    "get_time_in_timezone": lambda args: json.dumps({
        "timezone": args.get("timezone", "UTC"),
        "current_time": "2025-01-15T14:30:00",
        "utc_offset": "+09:00",
    }),
    "search_products": lambda args: json.dumps({
        "query": args.get("query", ""),
        "results": [
            {"name": "Sample Product", "price": 29.99, "rating": 4.5},
            {"name": "Another Product", "price": 49.99, "rating": 4.2},
        ],
        "total_results": 42,
    }),
    "send_email": lambda args: json.dumps({
        "status": "sent",
        "message_id": "msg-abc123",
        "to": args.get("to", ""),
    }),
    "book_restaurant": lambda args: json.dumps({
        "status": "confirmed",
        "confirmation_id": "RES-2025-0042",
        "restaurant": args.get("restaurant_name", ""),
        "date": args.get("date", ""),
        "party_size": args.get("party_size", 0),
    }),
    "calculate_loan": lambda args: json.dumps({
        "monthly_payment": 1073.64,
        "total_payment": 386510.40,
        "total_interest": 186510.40,
        "principal": args.get("principal", 0),
    }),
    "create_calendar_event": lambda args: json.dumps({
        "status": "created",
        "event_id": "evt-xyz789",
        "title": args.get("title", ""),
    }),
    "search_flights": lambda args: json.dumps({
        "flights": [
            {
                "airline": "Sample Air",
                "flight_no": "SA-101",
                "departure": "08:00",
                "arrival": "12:00",
                "price": 350.00,
                "stops": 0,
            }
        ],
        "total_results": 5,
    }),
    "create_order": lambda args: json.dumps({
        "status": "created",
        "order_id": "ORD-2025-1234",
        "total": 129.99,
        "estimated_delivery": "2025-01-20",
    }),
}


def get_mock_response(function_name: str, arguments: dict) -> str:
    handler = MOCK_RESPONSES.get(function_name)
    if handler:
        return handler(arguments)
    return json.dumps({"error": f"Unknown function: {function_name}"})
