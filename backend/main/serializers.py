from rest_framework import serializers

from main.models import *
from main.fields import *


class PrimitiveSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        return obj


class UserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    wants_emails = serializers.BooleanField(required=True)


class UserRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long"
            )
        return value


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    token = serializers.CharField(read_only=True)


class UpdateUserEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UpdateUserPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)
    old_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "New password must be at least 8 characters long"
            )
        return value


class UpdateUserWantsEmailsSerializer(serializers.Serializer):
    wants_emails = serializers.BooleanField(required=True)


class AskResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "New password must be at least 8 characters long"
            )
        return value


class CreateReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        exclude = ("user", "patent_ids")
        read_only_fields = (
            "datetime_analysis_started",
            "datetime_analysis_ended",
            "results",
            "status",
        )

    patent_application_filed_date = DateRangeField(required=False)
    patent_granted_date = DateRangeField(required=False)
    patent_figures_count = IntegerRangeField(required=False)
    patent_claims_count = IntegerRangeField(required=False)
    patent_sheets_count = IntegerRangeField(required=False)
    pct_application_date = DateRangeField(required=False)
    results = serializers.JSONField(required=False)
    filters = serializers.JSONField(required=False)


class ViewReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            "id",
            "datetime_created",
            "datetime_analysis_started",
            "datetime_analysis_ended",
            "executed_successfully",
            "status",
            "filters",
            "results",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        setattr(self.Meta, "read_only_fields", [*self.fields])


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


class TopicAnalysisSerializer(serializers.Serializer):
    method = serializers.ChoiceField(default="LDA", choices=["LDA", "NMF"])
    n_topics = serializers.IntegerField(default=10)
    n_words = serializers.IntegerField(default=10)
    start_date = serializers.DateField(default=None)
    end_date = serializers.DateField(default=None)
