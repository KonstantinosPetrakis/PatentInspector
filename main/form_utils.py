from datetime import datetime
from django import forms


class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)
        self.choices.insert(0, (None, '---'))
        self.widget.attrs.update({"class": "form-select"})


class RangeField(forms.MultiValueField):
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
            return [value.get('min'), value.get('max')] if value else [None, None]

    def __init__(self, *args, **kwargs):
        self.min = kwargs.pop("min")
        self.max = kwargs.pop("max")
        fields = (
            forms.IntegerField(),
            forms.IntegerField(),
        )
        kwargs.setdefault('widget', self.RangeWidget(attrs={"min": self.min, "max": self.max}))
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list is None or data_list == [self.min, self.max]: return None
        return {'min': data_list[0], 'max': data_list[1]}
    

class RangeDateField(forms.MultiValueField):
    class RangeDateWidget(forms.MultiWidget):
        template_name = "main/widgets/range_date.html"

        def __init__(self, attrs=None):
            widgets = [
                forms.DateInput(),
                forms.DateInput()
            ]
            super().__init__(widgets, attrs)

        def decompress(self, value):
            return [value.get('min'), value.get('max')] if value else [None, None]

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(),
            forms.DateField(),
        )
        kwargs.setdefault('required', False)
        kwargs.setdefault('widget', self.RangeDateWidget())
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return {'min': data_list[0], 'max': data_list[1]} if data_list else None


class KeywordField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('widget', forms.TextInput(attrs={"class": "keyword-input"}))
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        return value.split(",") if value else []


class TriStateField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.HiddenInput(attrs={"class": "tri-state-checkbox"}))
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)
        
    def to_python(self, value):
        if value == "": return None
        return value == "True"


class ChoiceKeywordsField(forms.CharField):
    def __init__(self, *args, **kwargs):
        url = kwargs.pop("url")
        min_query_length = kwargs.pop("min_query_length", 0)

        kwargs.setdefault('required', False)
        kwargs.setdefault('widget', forms.HiddenInput(attrs={"class": "choice-keywords-input",
            "data-url": url, "data-minQueryLength": min_query_length}))
        
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        return value.split(",") if value else []