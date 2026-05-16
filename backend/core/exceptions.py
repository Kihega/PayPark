"""ParkiPay — Custom DRF Exception Handler"""
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):


    """
    Wraps all DRF error responses in a consistent envelope:
    { "error": "<code>", "detail": "<message>" }
    """
    response = exception_handler(exc, context)

    if response is not None:
        original_data = response.data
        # If the response data is already in our format, leave it
        if isinstance(original_data, dict) and "error" in original_data:
            return response

        # Normalise to {"error": "...", "detail": "..."}
        if isinstance(original_data, dict):
            detail = original_data.get("detail", str(original_data))
        elif isinstance(original_data, list):
            detail = original_data[0] if original_data else "Unknown error"
        else:
            detail = str(original_data)

        # Map status codes to error codes
        code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            429: "too_many_requests",
            500: "server_error",
        }
        error_code = code_map.get(response.status_code, "error")

        response.data = {
            "error": error_code,
            "detail": str(detail),
        }

    return response
