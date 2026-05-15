"""
Initial migration: accounts app
Creates Officer (custom user) and AuditLog tables.
Depends on vehicles migration for the ParkingLocation FK.
"""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # Officer has FK → ParkingLocation
        ("vehicles", "0001_initial"),
        # Required by SimpleJWT token blacklist
        ("token_blacklist", "0001_initial"),
    ]

    operations = [
        # ── Officer ───────────────────────────────────────────────────────────
        migrations.CreateModel(
            name="Officer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(
                    default=False,
                    help_text="Designates that this user has all permissions without explicitly assigning them.",
                    verbose_name="superuser status",
                )),
                ("employee_id", models.CharField(
                    db_index=True,
                    help_text="Government-issued employee ID. Used for login.",
                    max_length=20,
                    unique=True,
                )),
                ("full_name", models.CharField(max_length=120)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True)),
                ("role", models.CharField(
                    choices=[
                        ("FIELD_OFFICER", "Field Officer"),
                        ("SUPERVISOR", "Supervisor"),
                        ("ADMIN", "Administrator"),
                    ],
                    default="FIELD_OFFICER",
                    max_length=20,
                )),
                ("location", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="officers",
                    to="vehicles.parkinglocation",
                )),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("failed_login_attempts", models.PositiveSmallIntegerField(default=0)),
                ("locked_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Officer",
                "verbose_name_plural": "Officers",
                "ordering": ["full_name"],
            },
        ),
        # Groups / permissions M2M (required by PermissionsMixin)
        migrations.AddField(
            model_name="officer",
            name="groups",
            field=models.ManyToManyField(
                blank=True,
                help_text="The groups this user belongs to.",
                related_name="officer_set",
                related_query_name="officer",
                to="auth.group",
                verbose_name="groups",
            ),
        ),
        migrations.AddField(
            model_name="officer",
            name="user_permissions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Specific permissions for this user.",
                related_name="officer_set",
                related_query_name="officer",
                to="auth.permission",
                verbose_name="user permissions",
            ),
        ),

        # ── AuditLog ─────────────────────────────────────────────────────────
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("officer", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="audit_logs",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("action", models.CharField(
                    choices=[
                        ("LOGIN_SUCCESS", "Login Success"),
                        ("LOGIN_FAILURE", "Login Failure"),
                        ("LOGIN_LOCKED", "Login Attempt — Account Locked"),
                        ("LOGOUT", "Logout"),
                        ("TOKEN_REFRESH", "Token Refresh"),
                        ("BILL_GENERATED", "Bill Generated"),
                        ("BILL_DUPLICATE_BLOCKED", "Duplicate Bill Blocked"),
                        ("VEHICLE_LOOKUP", "Vehicle Lookup"),
                        ("PLATE_NOT_FOUND", "Plate Not Found"),
                    ],
                    db_index=True,
                    max_length=40,
                )),
                ("plate_number", models.CharField(blank=True, db_index=True, max_length=20)),
                ("control_number", models.CharField(blank=True, max_length=30)),
                ("result", models.CharField(blank=True, max_length=40)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, max_length=300)),
                ("extra", models.JSONField(blank=True, default=dict)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "verbose_name": "Audit Log",
                "verbose_name_plural": "Audit Logs",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["officer", "timestamp"], name="auditlog_officer_ts_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["action", "timestamp"], name="auditlog_action_ts_idx"),
        ),
    ]
