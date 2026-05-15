"""Initial migration: billing app — ControlNumber table."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ControlNumber",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("control_number", models.CharField(blank=True, db_index=True, max_length=30, unique=True)),
                ("plate_number", models.CharField(db_index=True, max_length=20)),
                ("vehicle", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="control_numbers",
                    to="vehicles.vehicle",
                )),
                ("officer", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="bills_generated",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("location", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="control_numbers",
                    to="vehicles.parkinglocation",
                )),
                ("amount_due", models.DecimalField(decimal_places=2, max_digits=10)),
                ("generated_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("status", models.CharField(
                    choices=[
                        ("ACTIVE", "Active"),
                        ("EXPIRED", "Expired"),
                        ("PAID", "Paid"),
                    ],
                    db_index=True,
                    default="ACTIVE",
                    max_length=10,
                )),
                ("sms_sent", models.BooleanField(default=False)),
                ("email_sent", models.BooleanField(default=False)),
                ("sms_error", models.CharField(blank=True, max_length=300)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Control Number",
                "verbose_name_plural": "Control Numbers",
                "ordering": ["-generated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="controlnumber",
            index=models.Index(
                fields=["plate_number", "status", "expires_at"],
                name="billing_plate_status_exp_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="controlnumber",
            index=models.Index(
                fields=["officer", "generated_at"],
                name="billing_officer_date_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="controlnumber",
            index=models.Index(
                fields=["status", "expires_at"],
                name="billing_status_exp_idx",
            ),
        ),
    ]
