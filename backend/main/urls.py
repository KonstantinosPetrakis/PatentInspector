from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from main import views


schema_view = get_schema_view(
   openapi.Info(
      title="PatentAnalyzer API",
      default_version='v1',
      description="The API for the PatentAnalyzer app",
      contact=openapi.Contact(email="petrakki@csd.auth.gr"),
      license=openapi.License(name="GNU General Public License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


router = DefaultRouter(trailing_slash=False)
router.register(r"user/?", views.UserViewSet, basename="user")
router.register(r"report/?", views.ReportViewSet, basename="report")

urlpatterns = [
   path("api/", include(router.urls)),
   path("api/cpc/sections/", views.CPCSectionListView.as_view(), name="cpc-section-list"),
   path("api/cpc/classes/", views.CPCClassListView.as_view(), name="cpc-class-list"),
   path("api/cpc/subclasses/", views.CPCSubclassListView.as_view(), name="cpc-subclass-list"),
   path("api/cpc/groups/", views.CPCGroupListView.as_view(), name="cpc-group-list"),
   path("api/inventors/", views.InventorFieldView.as_view(), name="inventor-field-list"),
   path("api/assignees/", views.AssigneeFieldView.as_view(), name="assignee-field-list"),
   path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
