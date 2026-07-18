from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers


User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        supplied_username = attrs["username"].strip()

        user_match = (
            User.objects
            .filter(username__iexact=supplied_username)
            .first()
        )

        if user_match is None:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        user = authenticate(
            request=self.context.get("request"),
            username=user_match.username,
            password=attrs["password"],
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This user account is inactive."
            )

        if not hasattr(user, "profile"):
            raise serializers.ValidationError(
                "This user is not associated with an organization."
            )

        attrs["user"] = user
        return attrs
