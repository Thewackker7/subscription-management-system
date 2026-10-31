from django.core.exceptions import ValidationError


class ChallengePasswordValidator:
    """Minimum 9 chars, uppercase, lowercase, and special character."""
    def validate(self, password, user=None):
        valid = (len(password) >= 9 and any(c.isupper() for c in password)
                 and any(c.islower() for c in password) and any(not c.isalnum() for c in password))
        if not valid:
            raise ValidationError("Password must be at least 9 characters and include uppercase, lowercase, and special characters.")

    def get_help_text(self):
        return "Use at least 9 characters, including uppercase, lowercase, and a special character."
