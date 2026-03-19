from django.core.management.base import BaseCommand

from apps.customer_comm.tasks import cleanup_expired_inquiries


class Command(BaseCommand):
    help = "Apply retention policy to expired inquiries."

    def handle(self, *args, **options):
        processed = cleanup_expired_inquiries()
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} expired inquiries"))
