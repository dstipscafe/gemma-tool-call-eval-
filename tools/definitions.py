"""
10 tool definitions across 3 complexity levels for evaluating LLM tool calling.

Complexity levels:
- Simple (1-2 params, no nesting)
- Medium (3-5 params, optional params, enums)
- Complex (nested objects, arrays of objects, multi-layer structures)
"""

# ---------------------------------------------------------------------------
# Simple tools
# ---------------------------------------------------------------------------

GET_CURRENT_WEATHER = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather for a given city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'Tokyo', 'New York', 'Taipei'.",
                },
            },
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}

GET_EXCHANGE_RATE = {
    "type": "function",
    "function": {
        "name": "get_exchange_rate",
        "description": "Get the exchange rate between two currencies.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_currency": {
                    "type": "string",
                    "description": "The source currency code, e.g. 'USD', 'EUR', 'TWD'.",
                },
                "to_currency": {
                    "type": "string",
                    "description": "The target currency code, e.g. 'JPY', 'GBP', 'CNY'.",
                },
            },
            "required": ["from_currency", "to_currency"],
            "additionalProperties": False,
        },
    },
}

GET_TIME_IN_TIMEZONE = {
    "type": "function",
    "function": {
        "name": "get_time_in_timezone",
        "description": "Get the current time in a specific timezone.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "The IANA timezone name, e.g. 'Asia/Tokyo', 'America/New_York', 'Europe/London'.",
                },
            },
            "required": ["timezone"],
            "additionalProperties": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Medium tools
# ---------------------------------------------------------------------------

SEARCH_PRODUCTS = {
    "type": "function",
    "function": {
        "name": "search_products",
        "description": "Search for products in an online store.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword or phrase.",
                },
                "category": {
                    "type": "string",
                    "enum": ["electronics", "clothing", "food", "books"],
                    "description": "Product category to filter by.",
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter.",
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["price", "rating", "relevance"],
                    "description": "Sort order for results.",
                },
            },
            "required": ["query", "category"],
            "additionalProperties": False,
        },
    },
}

SEND_EMAIL = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Send an email to one or more recipients.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address.",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line.",
                },
                "body": {
                    "type": "string",
                    "description": "Email body content.",
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of CC email addresses.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "description": "Email priority level.",
                },
            },
            "required": ["to", "subject", "body"],
            "additionalProperties": False,
        },
    },
}

BOOK_RESTAURANT = {
    "type": "function",
    "function": {
        "name": "book_restaurant",
        "description": "Make a restaurant reservation.",
        "parameters": {
            "type": "object",
            "properties": {
                "restaurant_name": {
                    "type": "string",
                    "description": "Name of the restaurant.",
                },
                "date": {
                    "type": "string",
                    "description": "Reservation date in YYYY-MM-DD format.",
                },
                "time": {
                    "type": "string",
                    "description": "Reservation time in HH:MM format (24-hour).",
                },
                "party_size": {
                    "type": "integer",
                    "description": "Number of guests.",
                },
                "special_requests": {
                    "type": "string",
                    "description": "Any special requests or dietary requirements.",
                },
            },
            "required": ["restaurant_name", "date", "time", "party_size"],
            "additionalProperties": False,
        },
    },
}

CALCULATE_LOAN = {
    "type": "function",
    "function": {
        "name": "calculate_loan",
        "description": "Calculate monthly payment and total cost for a loan.",
        "parameters": {
            "type": "object",
            "properties": {
                "principal": {
                    "type": "number",
                    "description": "Loan principal amount.",
                },
                "annual_rate": {
                    "type": "number",
                    "description": "Annual interest rate as a percentage (e.g. 5.5 for 5.5%).",
                },
                "term_months": {
                    "type": "integer",
                    "description": "Loan term in months.",
                },
                "extra_monthly_payment": {
                    "type": "number",
                    "description": "Additional monthly payment amount.",
                },
            },
            "required": ["principal", "annual_rate", "term_months"],
            "additionalProperties": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Complex tools
# ---------------------------------------------------------------------------

CREATE_CALENDAR_EVENT = {
    "type": "function",
    "function": {
        "name": "create_calendar_event",
        "description": "Create a new calendar event with optional recurrence.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title.",
                },
                "start_time": {
                    "type": "string",
                    "description": "Event start time in ISO 8601 format (e.g. '2025-01-15T09:00:00').",
                },
                "end_time": {
                    "type": "string",
                    "description": "Event end time in ISO 8601 format (e.g. '2025-01-15T10:00:00').",
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email addresses.",
                },
                "location": {
                    "type": "string",
                    "description": "Event location.",
                },
                "recurrence": {
                    "type": "object",
                    "properties": {
                        "frequency": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly", "yearly"],
                            "description": "Recurrence frequency.",
                        },
                        "interval": {
                            "type": "integer",
                            "description": "Interval between recurrences (e.g. 2 for every 2 weeks).",
                        },
                        "until": {
                            "type": "string",
                            "description": "End date for recurrence in YYYY-MM-DD format.",
                        },
                    },
                    "required": ["frequency"],
                    "additionalProperties": False,
                    "description": "Recurrence settings.",
                },
            },
            "required": ["title", "start_time", "end_time", "attendees"],
            "additionalProperties": False,
        },
    },
}

SEARCH_FLIGHTS = {
    "type": "function",
    "function": {
        "name": "search_flights",
        "description": "Search for available flights between two airports.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "Departure airport IATA code (e.g. 'TPE', 'NRT', 'LAX').",
                },
                "destination": {
                    "type": "string",
                    "description": "Arrival airport IATA code (e.g. 'HND', 'SFO', 'CDG').",
                },
                "departure_date": {
                    "type": "string",
                    "description": "Departure date in YYYY-MM-DD format.",
                },
                "return_date": {
                    "type": "string",
                    "description": "Return date in YYYY-MM-DD format (omit for one-way).",
                },
                "passengers": {
                    "type": "object",
                    "properties": {
                        "adults": {
                            "type": "integer",
                            "description": "Number of adult passengers.",
                        },
                        "children": {
                            "type": "integer",
                            "description": "Number of child passengers (2-11 years).",
                        },
                        "infants": {
                            "type": "integer",
                            "description": "Number of infant passengers (under 2 years).",
                        },
                    },
                    "required": ["adults"],
                    "additionalProperties": False,
                    "description": "Passenger counts by type.",
                },
                "cabin_class": {
                    "type": "string",
                    "enum": ["economy", "premium_economy", "business", "first"],
                    "description": "Preferred cabin class.",
                },
                "max_stops": {
                    "type": "integer",
                    "description": "Maximum number of stops (0 for direct only).",
                },
            },
            "required": ["origin", "destination", "departure_date", "passengers", "cabin_class"],
            "additionalProperties": False,
        },
    },
}

CREATE_ORDER = {
    "type": "function",
    "function": {
        "name": "create_order",
        "description": "Create a new purchase order with items and shipping details.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "Product identifier.",
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity to order.",
                            },
                            "options": {
                                "type": "object",
                                "properties": {
                                    "color": {
                                        "type": "string",
                                        "description": "Product color.",
                                    },
                                    "size": {
                                        "type": "string",
                                        "description": "Product size.",
                                    },
                                },
                                "additionalProperties": False,
                                "description": "Product options like color, size.",
                            },
                        },
                        "required": ["product_id", "quantity"],
                        "additionalProperties": False,
                    },
                    "description": "List of items to order.",
                },
                "shipping_address": {
                    "type": "object",
                    "properties": {
                        "street": {
                            "type": "string",
                            "description": "Street address.",
                        },
                        "city": {
                            "type": "string",
                            "description": "City name.",
                        },
                        "state": {
                            "type": "string",
                            "description": "State or province.",
                        },
                        "zip": {
                            "type": "string",
                            "description": "ZIP or postal code.",
                        },
                        "country": {
                            "type": "string",
                            "description": "Country name or code.",
                        },
                    },
                    "required": ["street", "city", "zip", "country"],
                    "additionalProperties": False,
                    "description": "Shipping address.",
                },
                "payment_method": {
                    "type": "string",
                    "enum": ["credit_card", "debit_card", "paypal", "bank_transfer"],
                    "description": "Payment method.",
                },
                "coupon_code": {
                    "type": "string",
                    "description": "Optional coupon or discount code.",
                },
            },
            "required": ["items", "shipping_address", "payment_method"],
            "additionalProperties": False,
        },
    },
}

# ---------------------------------------------------------------------------
# All tools grouped by complexity
# ---------------------------------------------------------------------------

SIMPLE_TOOLS = [GET_CURRENT_WEATHER, GET_EXCHANGE_RATE, GET_TIME_IN_TIMEZONE]
MEDIUM_TOOLS = [SEARCH_PRODUCTS, SEND_EMAIL, BOOK_RESTAURANT, CALCULATE_LOAN]
COMPLEX_TOOLS = [CREATE_CALENDAR_EVENT, SEARCH_FLIGHTS, CREATE_ORDER]

ALL_TOOLS = SIMPLE_TOOLS + MEDIUM_TOOLS + COMPLEX_TOOLS

TOOL_COMPLEXITY = {
    "get_current_weather": "simple",
    "get_exchange_rate": "simple",
    "get_time_in_timezone": "simple",
    "search_products": "medium",
    "send_email": "medium",
    "book_restaurant": "medium",
    "calculate_loan": "medium",
    "create_calendar_event": "complex",
    "search_flights": "complex",
    "create_order": "complex",
}
