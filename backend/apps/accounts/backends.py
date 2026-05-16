"""ParkiPay — Custom Auth Backend: employee_id + password"""

from django.contrib.auth.backends import ModelBackend

from apps.accounts.models import Officer


class EmployeeIDBackend(ModelBackend):
    """
    Authenticates using employee_id instead of Django's default username.
    Used by SimpleJWT's token obtain view via AUTHENTICATION_BACKENDS.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # SimpleJWT passes username= but we treat it as employee_id
        employee_id = username or kwargs.get("employee_id")
        if not employee_id or not password:
            return None

        try:
            officer = Officer.objects.get(employee_id=employee_id)
        except Officer.DoesNotExist:
            return None

        if officer.check_password(password) and self.user_can_authenticate(officer):
            return officer
        return None

    def get_user(self, user_id):
        try:
            return Officer.objects.get(pk=user_id)
        except Officer.DoesNotExist:
            return None
