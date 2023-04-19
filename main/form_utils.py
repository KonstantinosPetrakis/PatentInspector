"""
In this file, we define custom form fields. To define the fields we either us
some existing field (e.g MultiValueField or the ChoiceField) or just a hidden input
and a lot of javascript in the frontend. 
"""


from django import forms


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
    THis field is a choice keywords field. It returns a list of keywords entered by the user.
    The difference between this field and the KeywordField is that this field has a dropdown menu
    that allows the user to select from a list of keywords, the list of keywords is fetched from the
    URL specified in the "url" keyword argument.
    """

    def __init__(self, *args, **kwargs):
        url = kwargs.pop("url")
        min_query_length = kwargs.pop("min_query_length", 0)

        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", forms.HiddenInput(attrs={"class": "choice-keywords-input",
            "data-url": url, "data-minQueryLength": min_query_length}))
        
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        return value.split(",") if value else []


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
    def __init__(self, *args, **kwargs):  
        self.choices = kwargs.pop("choices")
        kwargs.setdefault("required", False)
        self.widget = forms.CheckboxInput(attrs={"class": "switch-input"})
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return self.choices[bool(value)]