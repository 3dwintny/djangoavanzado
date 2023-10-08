"""Ratings serializers."""

# Django
from django.db.models import Avg

# Django REST Framework
from rest_framework import serializers

# Models
from cride.rides.models import Rating


class CreateRideRatingSerializer(serializers.ModelSerializer):
    """Create ride serializer."""

    rating = serializers.IntegerField(min_value=1, max_value=5)
    comments = serializers.CharField(required=False)

    class Meta:
        """Meta class."""

        model = Rating
        fields = ('rating', 'comments')

    def validate(self, data):
        """Verify rating hasn't been emitted before."""
        user = self.context['request'].user
        ride = self.context['ride']
        if not ride.passengers.filter(pk=user.pk).exists():
            raise serializers.ValidationError('User is not a passenger')

        q = Rating.objects.filter(
            circle=self.context['circle'],
            ride=ride,
            rating_user=user,
        )
        if q.exists():
            raise serializers.ValidationError('Rating have already been emitted!')
        return data

    def create(self, data):
        """Create rating."""
        offered_by = self.context['ride'].offered_by

        Rating.objects.create(
            circle=self.context['circle'],
            ride=self.context['ride'],
            rating_user=self.context['request'].user,
            rated_user=offered_by,
            **data
        )

        ride_avg = round(
            Rating.objects.filter(
                circle=self.context['circle'],
                ride=self.context['ride']
            ).aggregate(Avg('rating'))['rating__avg'],
            1
        )
        self.context['ride'].rating = ride_avg
        self.context['ride'].save()

        user_avg = round(
            Rating.objects.filter(
                rated_user=offered_by
            ).aggregate(Avg('rating'))['rating__avg'],
            1
        )
        offered_by.profile.reputation = user_avg
        offered_by.profile.save()

        return self.context['ride']
