from datetime import timedelta

from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, generics, viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db.models import QuerySet
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django_q.tasks import async_task
from django.utils import timezone

from main.helpers import remove_redundant_cpc_entities
from main.tasks import process_report, topic_analysis, execution_hook
from main import serializers
from main import schema
from main.models import *


def django_filter_warning(get_queryset_func):
    """
    This decorator is used to fix a warning in django-filter.
    See: https://github.com/carltongibson/django-filter/issues/966
    """

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return QuerySet()
        return get_queryset_func(self)

    return get_queryset


class BasicPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 50


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user creation, login and data retrieval.
    """

    http_method_names = ["post", "get"]

    def get_serializer_class(self, *args, **kwargs):
        return {
            "get_data": serializers.UserSerializer,
            "create": serializers.UserRegisterSerializer,
            "login": serializers.UserLoginSerializer,
            "update_email": serializers.UpdateUserEmailSerializer,
            "update_password": serializers.UpdateUserPasswordSerializer,
            "update_wants_emails": serializers.UpdateUserWantsEmailsSerializer,
            "ask_reset_password": serializers.AskResetPasswordSerializer,
            "reset_password": serializers.ResetPasswordSerializer,
        }.get(self.action)

    @django_filter_warning
    def get_queryset(self):
        return User.objects.filter(email=self.request.user.email).first()

    @swagger_auto_schema(auto_schema=None)
    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @swagger_auto_schema(auto_schema=None)
    def retrieve(self, request):
        raise MethodNotAllowed(request.method)

    def perform_create(self, serializer):
        """
        Creates a new user and generates a unique token for it.
        """

        data = serializer.validated_data

        user = User(email=data["email"])
        user.set_password(data["password"])
        user.save()
        Token.objects.create(user=user)

    @action(detail=False, methods=["post"])
    def login(self, request):
        """
        Verifies the user's credentials and returns a token if they are valid.
        """

        data = request.data
        user = User.objects.filter(email=data["email"]).first()
        if user is None:
            return Response({"error": "Invalid email"}, status=400)
        if not user.check_password(data["password"]):
            return Response({"error": "Invalid password"}, status=400)
        return Response(
            {"token": Token.objects.get(user=user).key, "email": user.email}
        )

    @swagger_auto_schema(**schema.update_email)
    @action(detail=False, methods=["post"])
    def update_email(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.validated_data

        if not request.user.check_password(data["password"]):
            return Response({"error": "Invalid password"}, status=400)

        request.user.email = data["new_email"]
        request.user.save()
        return Response(status=200)

    @swagger_auto_schema(**schema.update_password)
    @action(detail=False, methods=["post"])
    def update_password(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors["new_password"][0]}, status=400)
        data = serializer.validated_data

        if not request.user.check_password(data["old_password"]):
            return Response({"error": "Invalid old password"}, status=400)

        request.user.set_password(data["new_password"])
        request.user.save()
        return Response(status=200)

    @swagger_auto_schema(**schema.update_wants_emails)
    @action(detail=False, methods=["post"])
    def update_wants_emails(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.validated_data

        request.user.wants_emails = data["wants_emails"]
        request.user.save()
        return Response(status=200)

    @action(detail=False, methods=["get"])
    def get_data(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(**schema.ask_reset_password)
    @action(detail=False, methods=["post"])
    def ask_reset_password(self, request):
        data = request.data
        user = User.objects.filter(email=data["email"]).first()
        if user is None:
            return Response({"error": "Invalid email"}, status=400)

        ResetPasswordToken.objects.create(user=user)
        return Response(status=200)

    @swagger_auto_schema(**schema.reset_password)
    @action(detail=False, methods=["post"])
    def reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors["new_password"][0]}, status=400)
        data = serializer.validated_data

        token = ResetPasswordToken.objects.filter(
            token=data["token"],
            is_used=False,
            created__gte=timezone.now() - timedelta(minutes=5),
        ).first()

        if token is None:
            return Response({"error": "Invalid token"}, status=400)

        token.user.set_password(data["new_password"])
        token.user.save()
        token.is_used = True
        token.save()

        return Response(status=200)


class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reports to be viewed or edited.
    Users can only view and edit their own reports.
    """

    pagination_class = BasicPagination
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    @django_filter_warning
    def get_queryset(self):
        """
        Returns reports that belong to the current user.
        """

        return self.request.user.reports.all().order_by("-id")

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.ListReportSerializer
        if self.action == "topic_analysis":
            return serializers.TopicAnalysisSerializer
        if self.action == "retrieve":
            return serializers.ViewReportSerializer
        return serializers.CreateReportSerializer

    def perform_create(self, serializer):
        """
        Sets the current user as the owner of the report.
        """

        remove_redundant_cpc_entities(serializer.validated_data)
        report = serializer.save(user=self.request.user)
        async_task(process_report, report, hook=execution_hook)

    @swagger_auto_schema(**schema.topic_analysis)
    @action(detail=True, methods=["post"])
    def topic_analysis(self, request, pk):
        report = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.data
        report.status = "waiting_for_topic_analysis"
        report.save()
        async_task(
            topic_analysis,
            report,
            data["method"],
            data["n_topics"],
            data["n_words"],
            data["start_date"],
            data["end_date"],
            hook=execution_hook,
        )
        return Response(status=201)

    @swagger_auto_schema(**schema.patents_excel)
    @action(detail=True, methods=["get"])
    def download_patents_excel(self, request, pk):
        """
        Downloads the excel file containing the patents of the report.
        """

        with open(self.get_object().excel_file, "rb") as f:
            return HttpResponse(
                f.read(),
                headers={
                    "Content-Type": "application/vnd.ms-excel",
                    "Content-Disposition": "attachment; filename=Patents.xlsx",
                },
            )

    @swagger_auto_schema(**schema.get_patents)
    @action(detail=True, methods=["get"])
    def get_patents(self, request, pk):
        """
        Returns the patents of the report in a tabular format.
        """

        paginator = BasicPagination()
        patents = self.get_object().get_patents()
        field_names = [
            [
                field.name.replace("_", " ").title()
                for field in patents.first()._meta.local_fields
            ]
        ]

        tabular_data = paginator.paginate_queryset(patents.values_list(), request)
        tabular_data = serializers.PrimitiveSerializer(tabular_data, many=True).data
        tabular_data = field_names + tabular_data
        return paginator.get_paginated_response(tabular_data)


class CPCSectionListView(generics.ListAPIView):
    """
    API endpoint that allows CPC sections to be viewed.
    """

    queryset = CPCSection.objects.all().order_by("section")
    serializer_class = serializers.CPCSectionSerializer
    permission_classes = [permissions.IsAuthenticated]


class CPCClassListView(generics.ListAPIView):
    """
    API endpoint that allows CPC classes to be viewed.
    """

    queryset = CPCClass.objects.all().order_by("_class")
    serializer_class = serializers.CPCClassSerializer
    permission_classes = [permissions.IsAuthenticated]


class CPCSubclassListView(generics.ListAPIView):
    """
    API endpoint that allows CPC subclasses to be viewed.
    Pagination and query filtering are supported.
    Pagination is limited to 50 items per page.
    """

    class filterset_class(filters.FilterSet):
        q = filters.CharFilter(
            field_name="subclass",
            lookup_expr="istartswith",
            label="The beginning of the subclass code",
        )

    queryset = CPCSubclass.objects.all().order_by("subclass")
    serializer_class = serializers.CPCSubclassSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BasicPagination
    filter_backends = [DjangoFilterBackend]


class CPCGroupListView(generics.ListAPIView):
    """
    API endpoint that allows CPC groups to be viewed.
    Pagination and query filtering are supported.
    Pagination is limited to 50 items per page.
    """

    class filterset_class(filters.FilterSet):
        q = filters.CharFilter(
            field_name="group",
            lookup_expr="istartswith",
            label="The beginning of the group code",
        )

    queryset = CPCGroup.objects.all().order_by("group")
    serializer_class = serializers.CPCGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BasicPagination
    filter_backends = [DjangoFilterBackend]


class InventorFieldView(generics.ListAPIView):
    """
    API endpoint that allows inventor first names or last names to be viewed
    based on a query parameter.
    Pagination is limited to 50 items per page.
    You can filter by first name or last name, but not both and not neither.
    """

    class filterset_class(filters.FilterSet):
        first_name = filters.CharFilter(
            field_name="first_name",
            lookup_expr="istartswith",
            label="The beginning of the inventor's first name",
        )
        last_name = filters.CharFilter(
            field_name="last_name",
            lookup_expr="istartswith",
            label="The beginning of the inventor's last name",
        )

    serializer_class = serializers.PrimitiveSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BasicPagination
    filter_backends = [DjangoFilterBackend]

    @django_filter_warning
    def get_queryset(self):
        filter = list(self.request.query_params.keys())[0]
        return (
            Inventor.objects.order_by(filter).values_list(filter, flat=True).distinct()
        )

    def list(self, request, *args, **kwargs):
        if len(self.request.query_params) != 1:
            return Response(
                {"error": "You must provide exactly one query parameter"}, status=400
            )
        return super().list(request, *args, **kwargs)


class AssigneeFieldView(generics.ListAPIView):
    """
    API endpoint that allows assignee first names or last names or organization
    names to be viewed based on a query parameter.
    Pagination is limited to 50 items per page.
    You can filter by first name, last name and organization, you can use only one filter at a time.
    """

    class filterset_class(filters.FilterSet):
        first_name = filters.CharFilter(
            field_name="first_name",
            lookup_expr="istartswith",
            label="The beginning of the assignee's first name",
        )
        last_name = filters.CharFilter(
            field_name="last_name",
            lookup_expr="istartswith",
            label="The beginning of the assignee's last name",
        )
        organization = filters.CharFilter(
            field_name="organization",
            lookup_expr="istartswith",
            label="The beginning of the assignee's organization name",
        )

    serializer_class = serializers.PrimitiveSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BasicPagination
    filter_backends = [DjangoFilterBackend]

    @django_filter_warning
    def get_queryset(self):
        filter = list(self.request.query_params.keys())[0]
        return (
            Assignee.objects.order_by(filter).values_list(filter, flat=True).distinct()
        )

    def list(self, request, *args, **kwargs):
        if len(self.request.query_params) != 1:
            return Response(
                {"error": "You must provide exactly one query parameter"}, status=400
            )
        return super().list(request, *args, **kwargs)
