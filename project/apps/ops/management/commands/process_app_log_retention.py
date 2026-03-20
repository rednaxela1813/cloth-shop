from django.core.management.base import BaseCommand

from apps.ops.tasks import cleanup_expired_app_logs


class Command(BaseCommand):
    help = "Delete expired application logs according to retention policy."

    def handle(self, *args, **options):
        deleted = cleanup_expired_app_logs()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired application logs"))
