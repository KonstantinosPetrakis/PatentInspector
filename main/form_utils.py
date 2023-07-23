"""
In this file, we define custom form fields. To define the fields we either use
some existing field (e.g MultiValueField or the ChoiceField) or just a hidden input
and a lot of javascript in the frontend. 

We also define utilities functions used in forms, either in frontend or in admin.
"""


from typing import Type

from django.utils.safestring import mark_safe, SafeString
from django.conf import settings
from django import forms


def id_and_default_field(model: Type) -> tuple | None:
    """
    This function will return the id and default field of the given model.
    It is used to build the exact url for the ChoiceKeywordsField.
    It is useful when no model_field is given to the ChoiceKeywordsField.

    Args:
        model (Type): The model to get the id and default field of.

    Returns:
        tuple | None: The id and default field of the given model or None if the model is not supported.
    """
    
    map = {
        "CPCSection": ("section", "title"),
        "CPCClass": ("_class", "title"),
        "CPCSubclass": ("subclass", "title"),
        "CPCGroup": ("group", "title"),
    }
    return map[model] if model in map else None


def get_help_text(field: str) -> SafeString:
    """
    This function will return the help text of the given field from the help_texts directory.

    Args:
        field (str): The field to get the help text of.

    Returns:
        SafeString: The HTML help text ready to be rendered.
    """

    with open(f"{settings.BASE_DIR}/main/help_texts/patent/{field}.html", "r") as f:
        return mark_safe(f.read())


class EmptyChoiceField(forms.ChoiceField):
    """
    This field is a choice field that has an empty choice (---) at the top of the list.
    It returns None if the user selects the empty choice or the value of the selected choice.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)
        self.choices.insert(0, (None, "---"))
        self.widget.attrs.update({"class": "form-select"})


class RangeField(forms.MultiValueField):
    """
    This field is a range field that has two number inputs, one for the minimum and one for the maximum.
    It returns a dictionary with the minimum and maximum numbers.
    """

    class RangeWidget(forms.MultiWidget):
        template_name = "main/widgets/range.html"

        def __init__(self, attrs=None):
            attrs = {"type": "range", "min": attrs["min"], "max": attrs["max"]}
            widgets = [
                forms.NumberInput(attrs=attrs),
                forms.NumberInput(attrs=attrs),
            ]
            super().__init__(widgets, attrs)

        def decompress(self, value):
            return [value.get("min"), value.get("max")] if value else [None, None]

    def __init__(self, *args, **kwargs):
        self.min = kwargs.pop("min")
        self.max = kwargs.pop("max")
        fields = (
            forms.IntegerField(),
            forms.IntegerField(),
        )
        kwargs.setdefault("widget", self.RangeWidget(attrs={"min": self.min, "max": self.max}))
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list is None or data_list == [self.min, self.max]: return None
        return {"min": data_list[0], "max": data_list[1]}
    

class RangeDateField(forms.MultiValueField):
    """
    This field is a range field that has two date inputs, one for the minimum and one for the maximum.
    It returns a dictionary with the minimum and maximum dates.
    """

    class RangeDateWidget(forms.MultiWidget):
        template_name = "main/widgets/range_date.html"

        def __init__(self, attrs=None):
            widgets = [
                forms.DateInput(),
                forms.DateInput()
            ]
            super().__init__(widgets, attrs)

        def decompress(self, value):
            return [value.get("min"), value.get("max")] if value else [None, None]

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(),
            forms.DateField(),
        )
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", self.RangeDateWidget())
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return {"min": data_list[0], "max": data_list[1]} if data_list else None


class KeywordField(forms.CharField):
    """
    This fields is a keywords field. It returns a list of keywords entered by the user.
    """
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", forms.TextInput(attrs={"class": "keyword-input"}))
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        return value.split(",") if value else []


class TriStateField(forms.CharField):
    """
    This field is a tri-state field. It returns True, False, or None depending if the user checked or unchecked the checkbox.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.HiddenInput(attrs={"class": "tri-state-checkbox"}))
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)
        
    def to_python(self, value):
        if value == "": return None
        return value == "True"


class ChoiceKeywordsField(forms.CharField):
    """
    This field is a choice keywords field. It returns a list of keywords entered by the user.
    The difference between this field and the KeywordField is that this field has a dropdown menu
    that allows the user to select from a list of keywords.
    
    The list of keywords is retrieved from the API using the model and wanted_fields arguments,
    the URL is automatically generated for the supported models and fields. The first field in
    the wanted_fields is the field that the filtering will be done on. If not wanted_fields
    specified, the id and a default field will be used.
    """

    def __init__(self, *args, **kwargs):
        model = kwargs.pop("model")
        wanted_fields = kwargs.pop("wanted_fields", None)
        # If not wanted_fields specified, we will use the id and default field.
        if wanted_fields is None: wanted_fields = id_and_default_field(model)
        filter_field = wanted_fields[0]
        wanted_fields = ",".join(wanted_fields)

        exact_url = self.build_exact_url(model, wanted_fields, filter_field)
        query_url = self.build_query_url(model, wanted_fields, filter_field)

        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", forms.HiddenInput(attrs={"class": "choice-keywords-input",
            "data-exact-url": exact_url, "data-query-url": query_url}))
        
        super().__init__(*args, **kwargs)
    

    def build_exact_url(self, model: str, wanted_fields: str, exact_field: str) -> str:
        """
        This function will build the exact url for the ChoiceKeywordsField.

        Args:
            model (str): The model to build the url for.
            wanted_fields (str): The fields to retrieve from the API (comma separated).
            exact_field (str): The field to filter on.

        Returns:
            str: The exact url for the ChoiceKeywordsField.
        """

        base_url = "api/records-field-from-exact-list"
        return f"{base_url}?model={model}&wanted-fields={wanted_fields}&exact-field={exact_field}"

    
    def build_query_url(self, model: str, wanted_fields: str, query_field: str) -> str:
        """
        This function will build the query url for the ChoiceKeywordsField.

        Args:
            model (str): The model to build the url for.
            wanted_fields (list[str]): The fields to retrieve from the API (comma separated).
            query_field (str): The field to filter on.

        Returns:
            str: The query url for the ChoiceKeywordsField.
        """

        base_url = "api/records-field-from-query"
        return f"{base_url}?model={model}&wanted-fields={wanted_fields}&query-field={query_field}"


    def to_python(self, value):
        # ~# is used as separator instead of ',' can be included in the keywords.
        return value.split("~#") if value else []


class RadiusField(forms.CharField):
    """
    This field is a radius field. It returns a dictionary with the latitude, longitude, and radius.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", forms.HiddenInput(attrs={"class": "radius-input"}))
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        if not value: return None
        lat, lng, radius = value.split(",")
        return {"lat": float(lat), "lng": float(lng), "radius": float(radius)} 
    

class SwitchInputValuesField(forms.BooleanField):
    """
    This field is a switch input values field. It returns the value of the selected choice.
    It is used when the user has to choose between two values (e.g 'blue' or 'red').
    """

    def __init__(self, *args, **kwargs):  
        self.choices = kwargs.pop("choices")
        kwargs.setdefault("required", False)
        self.widget = forms.CheckboxInput(attrs={"class": "switch-input"})
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return self.choices[bool(value)]
    