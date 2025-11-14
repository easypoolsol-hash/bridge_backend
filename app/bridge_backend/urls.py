"""
URL configuration for bridge_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from bridge_backend.auth_viewsets import AuthViewSet
from bridge_backend.health import health_check, liveness_check, readiness_check
from leads.viewsets import ClientViewSet, FormTemplateViewSet, LeadViewSet, PublicFormViewSet
from products.viewsets import MainCategoryViewSet, ProductViewSet, SubCategoryViewSet

# API Router
router = DefaultRouter()
# Google Cloud API pattern: Resource-oriented design
router.register(r"users", AuthViewSet, basename="users")
router.register(r"products/main-categories", MainCategoryViewSet, basename="main-category")
router.register(r"products/sub-categories", SubCategoryViewSet, basename="sub-category")
router.register(r"products/products", ProductViewSet, basename="product")
router.register(r"clients", ClientViewSet, basename="client")
router.register(r"leads", LeadViewSet, basename="lead")
router.register(r"forms", FormTemplateViewSet, basename="form-template")

urlpatterns = [
    # Health checks (no auth required)
    path("", health_check, name="health_check"),
    path("health/", health_check, name="health"),
    path("health/live/", liveness_check, name="liveness_check"),
    path("health/ready/", readiness_check, name="readiness_check"),
    # Admin
    path("admin/", admin.site.urls),
    # API
    path("api/", include(router.urls)),
    # Public form endpoints (no auth required)
    path(
        "api/public/forms/<str:share_token>/",
        PublicFormViewSet.as_view({"get": "retrieve"}),
        name="public-form-detail",
    ),
    path(
        "api/public/forms/<str:share_token>/submit/",
        PublicFormViewSet.as_view({"post": "create"}),
        name="public-form-submit",
    ),
    # OpenAPI schema (for Flutter code generation)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI (for API testing)
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
