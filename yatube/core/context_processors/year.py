from django.utils import timezone


def year(request) -> int:
    """Добавляет переменную с текущим годом."""
    today = timezone.localtime(timezone.now())
    return {
        'year': today.year
    }
