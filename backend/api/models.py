from django.db import models


class Place(models.Model):
    created_by = models.ForeignKey(
        "users.TelegramUser",
        on_delete=models.PROTECT,
        related_name="places",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    country = models.CharField(max_length=128)
    region = models.CharField(max_length=128)
    city = models.CharField(max_length=128)
    address = models.CharField(max_length=255, blank=True, default="")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "country", "region", "city", "address"],
                name="unique_place_per_location_address",
            )
        ]
        indexes = [
            models.Index(fields=["country", "region", "city"]),
            models.Index(fields=["is_active", "city"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.city}, {self.region}, {self.country})"


class Review(models.Model):
    user = models.ForeignKey(
        "users.TelegramUser",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    text = models.TextField()
    rating = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "place"],
                name="unique_review_per_user_place",
            ),
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_between_1_and_5",
            ),
        ]

    def __str__(self) -> str:
        return f"Review #{self.pk} by {self.user_id} for {self.place_id}"


class Favorite(models.Model):
    user = models.ForeignKey(
        "users.TelegramUser",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "place"],
                name="unique_favorite_per_user_place",
            )
        ]

    def __str__(self) -> str:
        return f"Favorite #{self.pk} by {self.user_id} for {self.place_id}"
