from collections import OrderedDict

from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import no_body
import drf_yasg.openapi as openapi


# DRF-YASG doesn't support write_only fields in schema generation, and that's a fix.
# Code from https://github.com/axnsan12/drf-yasg/issues/70#issuecomment-698288806


class ReadOnly:
    def get_fields(self):
        new_fields = OrderedDict()
        for fieldName, field in super().get_fields().items():
            if not field.write_only:
                new_fields[fieldName] = field
        return new_fields


class WriteOnly:
    def get_fields(self):
        new_fields = OrderedDict()
        for fieldName, field in super().get_fields().items():
            if not field.read_only:
                new_fields[fieldName] = field
        return new_fields


class BlankMeta:
    pass


class ReadWriteAutoSchema(SwaggerAutoSchema):
    def get_view_serializer(self):
        return self._convert_serializer(WriteOnly)

    def get_default_response_serializer(self):
        body_override = self._get_request_body_override()
        if body_override and body_override is not no_body:
            return body_override

        return self._convert_serializer(ReadOnly)

    def _convert_serializer(self, new_class):
        serializer = super().get_view_serializer()
        if not serializer:
            return serializer

        class CustomSerializer(new_class, serializer.__class__):
            class Meta(getattr(serializer.__class__, "Meta", BlankMeta)):
                ref_name = new_class.__name__ + serializer.__class__.__name__

        new_serializer = CustomSerializer(data=serializer.data)
        return new_serializer


# Docs of the API
update_email = {
    "responses": {
        200: openapi.Response(
            description="The user's email was successfully updated",
        ),
        400: openapi.Response(
            description="The request body was invalid or the password was incorrect",
        ),
    }
}

update_password = {
    "responses": {
        200: openapi.Response(
            description="The user's password was successfully updated",
        ),
        400: openapi.Response(
            description="The request body was invalid or the old password was incorrect",
        ),
    }
}

update_wants_emails = {
    "responses": {
        200: openapi.Response(
            description="The user's wants_emails field was successfully updated",
        ),
        400: openapi.Response(
            description="The request body was invalid",
        ),
    }
}

topic_analysis = {
    "responses": {
        201: openapi.Response(
            description="The topic analysis task was successfully put in the queue",
        ),
        400: openapi.Response(
            description="The request body was invalid",
        ),
    }
}

get_patents = {
    "responses": {
        200: openapi.Response(
            description="The patents were successfully retrieved",
            schema=openapi.Schema(
                title="Patents tabular data",
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    title="Patent row",
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        title="Patent column",
                        type=openapi.TYPE_STRING
                    )
                )
            )
        ),
    }
}

patents_excel = {
    "responses": {
        200: openapi.Response(
            description="The patents excel file was successfully retrieved",
            schema=openapi.Schema(
                title="Patents excel file",
                type=openapi.TYPE_FILE,
            )
        ),
    }
}