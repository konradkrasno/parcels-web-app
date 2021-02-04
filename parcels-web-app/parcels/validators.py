from django.core.exceptions import ValidationError


def validate_positive(value: int) -> None:
    if isinstance(value, int) and value <= 0:
        raise ValidationError("Wartość musi być większa od zera!")
