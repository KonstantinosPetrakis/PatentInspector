from rest_framework import serializers

from main.models import *
from main.fields import *


class PrimitiveSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        return obj


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "password")
        write_only_fields = ("password",)

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long"
            )
        return value


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = (
            "datetime_analysis_started",
            "datetime_analysis_ended",
            "user",
            "results",
        )

    patent_application_filed_date = DateRangeField(required=False)
    patent_granted_date = DateRangeField(required=False)
    patent_figures_count = IntegerRangeField(required=False)
    patent_claims_count = IntegerRangeField(required=False)
    patent_sheets_count = IntegerRangeField(required=False)
    pct_application_date = DateRangeField(required=False)
    results = serializers.JSONField(required=False)


class ListReportSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    datetime_created = serializers.DateTimeField(read_only=True)
    datetime_analysis_started = serializers.DateTimeField(read_only=True)
    datetime_analysis_ended = serializers.DateTimeField(read_only=True)


class CPCSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPCSection
        fields = "__all__"


class CPCClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPCClass
        fields = "__all__"


class CPCSubclassSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPCSubclass
        fields = "__all__"


class CPCGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPCGroup
        fields = "__all__"
