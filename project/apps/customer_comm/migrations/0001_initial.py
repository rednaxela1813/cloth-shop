import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Inquiry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("source", models.CharField(choices=[("website_contact", "Website contact form")], default="website_contact", max_length=40)),
                ("status", models.CharField(choices=[("received", "Received"), ("anonymized", "Anonymized"), ("deleted", "Deleted")], default="received", max_length=20)),
                ("full_name_ciphertext", models.TextField(blank=True)),
                ("email_ciphertext", models.TextField(blank=True)),
                ("phone_ciphertext", models.TextField(blank=True)),
                ("messenger_type", models.CharField(blank=True, choices=[("whatsapp", "WhatsApp"), ("telegram", "Telegram"), ("viber", "Viber"), ("signal", "Signal"), ("other", "Other")], max_length=40)),
                ("messenger_handle_ciphertext", models.TextField(blank=True)),
                ("message_ciphertext", models.TextField(blank=True)),
                ("email_hash", models.CharField(db_index=True, max_length=64)),
                ("phone_hash", models.CharField(blank=True, db_index=True, max_length=64)),
                ("consent_given_at", models.DateTimeField()),
                ("consent_ip_hash", models.CharField(blank=True, max_length=64)),
                ("consent_notice_version", models.CharField(max_length=32)),
                ("consent_text_version", models.CharField(max_length=32)),
                ("retention_expires_at", models.DateTimeField(db_index=True)),
                ("anonymized_at", models.DateTimeField(blank=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("last_exported_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at", "-id"],
                "indexes": [
                    models.Index(fields=["status", "retention_expires_at"], name="customer_co_status_2b70bc_idx"),
                    models.Index(fields=["source", "created_at"], name="customer_co_source_49a2ec_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="InquiryEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("event_type", models.CharField(choices=[("submitted", "Submitted"), ("consent_recorded", "Consent recorded"), ("delivery_queued", "Delivery queued"), ("delivery_sent", "Delivery sent"), ("delivery_failed", "Delivery failed"), ("retention_anonymized", "Retention anonymized"), ("retention_deleted", "Retention deleted"), ("privacy_export_requested", "Privacy export requested"), ("privacy_export_completed", "Privacy export completed"), ("privacy_erasure_requested", "Privacy erasure requested"), ("privacy_erasure_completed", "Privacy erasure completed")], max_length=50)),
                ("actor", models.CharField(default="system", max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("inquiry", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="events", to="customer_comm.inquiry")),
            ],
            options={
                "ordering": ["-created_at", "-id"],
                "indexes": [
                    models.Index(fields=["event_type", "created_at"], name="customer_co_event_t_f1d8b9_idx"),
                    models.Index(fields=["inquiry", "created_at"], name="customer_co_inquiry_e8d40d_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="InquiryChannelDelivery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("channel", models.CharField(choices=[("email", "Email"), ("telegram", "Telegram")], max_length=20)),
                ("provider", models.CharField(max_length=64)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("in_progress", "In progress"), ("sent", "Sent"), ("failed", "Failed"), ("exhausted", "Exhausted"), ("canceled", "Canceled")], default="pending", max_length=20)),
                ("destination_summary", models.CharField(blank=True, max_length=255)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("max_attempts", models.PositiveSmallIntegerField(default=5)),
                ("next_attempt_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("last_attempt_at", models.DateTimeField(blank=True, null=True)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("provider_message_id", models.CharField(blank=True, max_length=255)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("inquiry", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deliveries", to="customer_comm.inquiry")),
            ],
            options={
                "ordering": ["status", "next_attempt_at", "id"],
                "indexes": [
                    models.Index(fields=["channel", "status", "next_attempt_at"], name="customer_co_channel_b0d9de_idx"),
                    models.Index(fields=["inquiry", "channel"], name="customer_co_inquiry_6ecb54_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ConsentRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("consent_type", models.CharField(choices=[("contact_inquiry", "Contact inquiry")], default="contact_inquiry", max_length=40)),
                ("granted", models.BooleanField(default=True)),
                ("granted_at", models.DateTimeField()),
                ("privacy_notice_version", models.CharField(max_length=32)),
                ("consent_text_version", models.CharField(max_length=32)),
                ("ip_hash", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("inquiry", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="consent_records", to="customer_comm.inquiry")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="PrivacyRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("request_type", models.CharField(choices=[("export", "Export"), ("erasure", "Erasure")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("requester_email_hash", models.CharField(db_index=True, max_length=64)),
                ("export_file", models.FileField(blank=True, null=True, upload_to="customer-comm/privacy-exports/")),
                ("failure_reason", models.TextField(blank=True)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("inquiry", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="privacy_requests", to="customer_comm.inquiry")),
            ],
            options={
                "ordering": ["-requested_at", "-id"],
                "indexes": [
                    models.Index(fields=["request_type", "status"], name="customer_co_request_56d8a8_idx"),
                    models.Index(fields=["requester_email_hash", "status"], name="customer_co_request_5f7a7f_idx"),
                ],
            },
        ),
    ]
