from django.db import models

class Tokens(models.Model):
    broadcast_token = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name="Broadcast Token",
        help_text="Token used for broadcasting."
    )
    broadcast_userid = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default=None,
        verbose_name="Broadcast User ID",
        help_text="User ID associated with the broadcast token."
    )

    def __str__(self):
        return f"Token ID: {self.id}"

    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"
