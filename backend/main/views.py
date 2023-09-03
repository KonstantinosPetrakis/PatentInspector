from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework import viewsets
from main import serializers
from main.models import User


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
        return Response({"token": Token.objects.get(user=user).key, "email": user.email})


class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reports to be viewed or edited.
    Users can only view and edit their own reports.
    """

    serializer_class = serializers.ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        """
        Returns reports that belong to the current user.
        """

        return self.request.user.reports.all()

    def perform_create(self, serializer):
        """
        Sets the current user as the owner of the report.
        """

        serializer.save(user=self.request.user)
    
    # Dynamic report operations can be appended as actions.
    