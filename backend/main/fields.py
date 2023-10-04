import datetime

from rest_framework import serializers
from drf_yasg import openapi
from django.db.backends.postgresql.psycopg_any import DateRange, NumericRange


class DateRangeField(serializers.Field):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Date Range",
            "properties": {
                "lower": openapi.Schema(
                    title="The lower bound of the date range",
                    type=openapi.TYPE_STRING,
                ),
                "upper": openapi.Schema(
                    title="The upper bound of the date range",
                    type=openapi.TYPE_STRING,
                ),
            },
            "example": {
                "lower": "2020-01-01",
                "upper": "2020-12-31",
            },
        }

    def validate_date(self, value):
        try:
            datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise serializers.ValidationError("Date must be in the format YYYY-MM-DD")
        return value

    def to_representation(self, value):
        return {"lower": value.lower, "upper": value.upper}

    def to_internal_value(self, data):
        if not data or (not data["lower"] and not data["upper"]):
            return None

        if data["lower"]:
            self.validate_date(data["lower"])
        if data["upper"]:
            self.validate_date(data["upper"])

        return DateRange(data["lower"], data["upper"])


class IntegerRangeField(serializers.Field):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Integer Range",
            "properties": {
                "lower": openapi.Schema(
                    title="The lower bound of the range",
                    type=openapi.TYPE_INTEGER,
                ),
                "upper": openapi.Schema(
                    title="The upper bound of the range",
                    type=openapi.TYPE_INTEGER,
                ),
            },
        }

    def to_representation(self, value):
        return {"lower": value.lower, "upper": value.upper}

    def to_internal_value(self, data):
        if not data or (not data["lower"] and not data["upper"]):
            return None
        return NumericRange(data["lower"], data["upper"])
