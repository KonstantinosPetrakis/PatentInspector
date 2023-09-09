from rest_framework import permissions
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db.models import QuerySet
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django_q.tasks import async_task

from main.helpers import remove_redundant_cpc_entities
from main.tasks import process_report, execution_hook
from main import serializers
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
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 100


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user creation and login.
    """

    serializer_class = serializers.UserSerializer
    http_method_names = ["post"]

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
        
        return serializers.ReportSerializer

    def perform_create(self, serializer):
        """
        Sets the current user as the owner of the report.
        """

        remove_redundant_cpc_entities(serializer.validated_data)
        report = serializer.save(user=self.request.user)
        async_task(process_report, report, hook=execution_hook)

    @action(detail=True, methods=["post"])
    def new_topic_modeling(self, request, pk):
        pass

    @action(detail=True, methods=["get"])
    def download_patents_excel(self, request, pk):
        """
        Downloads the excel file containing the patents of the report.
        """
        
        with open(self.get_object().patents_excel, "rb") as f:
            return HttpResponse(
                f.read(),
                headers={
                    "Content-Type": "application/vnd.ms-excel",
                    "Content-Disposition": "attachment; filename=Patents.xlsx",
                },
            )


class CPCSectionListView(generics.ListAPIView):
    """
    API endpoint that allows CPC sections to be viewed.
    """

    queryset = CPCSection.objects.all()
    serializer_class = serializers.CPCSectionSerializer
    permission_classes = [permissions.IsAuthenticated]


class CPCClassListView(generics.ListAPIView):
    """
    API endpoint that allows CPC classes to be viewed.
    """

    queryset = CPCClass.objects.all()
    serializer_class = serializers.CPCClassSerializer
    permission_classes = [permissions.IsAuthenticated]


class CPCSubclassListView(generics.ListAPIView):
    """
    API endpoint that allows CPC subclasses to be viewed.
    Pagination and query filtering are supported.
    Pagination is limited to 100 items per page.
    """

    class filterset_class(filters.FilterSet):
        q = filters.CharFilter(
            field_name="subclass",
            lookup_expr="istartswith",
            label="The beginning of the subclass code",
        )

    queryset = CPCSubclass.objects.all()
    serializer_class = serializers.CPCSubclassSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BasicPagination
    filter_backends = [DjangoFilterBackend]


class CPCGroupListView(generics.ListAPIView):
    """
    API endpoint that allows CPC groups to be viewed.
    Pagination and query filtering are supported.
    Pagination is limited to 100 items per page.
    """

    class filterset_class(filters.FilterSet):
        q = filters.CharFilter(
            field_name="group",
            lookup_expr="istartswith",
            label="The beginning of the group code",
        )

    queryset = CPCGroup.objects.all()
    serializer_class = serializers.CPCGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = BasicPagination
    filter_backends = [DjangoFilterBackend]


class InventorFieldView(generics.ListAPIView):
    """
    API endpoint that allows inventor first names or last names to be viewed
    based on a query parameter.
    Pagination is limited to 100 items per page.
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
    Pagination is limited to 100 items per page.
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
