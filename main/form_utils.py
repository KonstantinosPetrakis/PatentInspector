from datetime import datetime
from django import forms


# ----------------- Widgets -----------------
class RangeWidget(forms.MultiWidget):
    template_name = "main/widgets/range.html"

    def __init__(self, attrs=None):
        widgets = [
            forms.NumberInput(attrs={"type": "range", "min": attrs["min"], "max": attrs["max"]}),
            forms.NumberInput(attrs={"type": "range", "min": attrs["min"], "max": attrs["max"]}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        return [value.get('min'), value.get('max')] if value else [None, None]


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


class TriStateCheckboxInput(forms.HiddenInput):
    def __init__(self, attrs={}):
        attrs.update({"class": "tri-state-checkbox"})
        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        return value == "True" if len(value) != 0 else None


class KeywordWidget(forms.TextInput):
    def __init__(self, attrs={}):
        attrs.update({"class": "d-none keyword-input"})
        super().__init__(attrs)
    
    def value_from_datadict(self, data, files, name):
        values = super().value_from_datadict(data, files, name)
        return values.split(",") if values else []
    
    def format_value(self, value):
        if isinstance(value, list):
            return ','.join(str(v) for v in value)
        return super().format_value(value)
    

class ChoiceKeywordsWidget(forms.SelectMultiple):
    def __init__(self, attrs={}):
        attrs.update({"class": "form-select"})
        super().__init__(attrs)
    
    def value_from_datadict(self, data, files, name):
        values = super().value_from_datadict(data, files, name)
        return values.split(",") if values else []
    

# ----------------- Fields -----------------
class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)
        self.choices.insert(0, (None, '---'))
        self.widget.attrs.update({"class": "form-select"})


class RangeField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        self.min = kwargs.pop("min")
        self.max = kwargs.pop("max")
        fields = (
            forms.IntegerField(),
            forms.IntegerField(),
        )
        kwargs.setdefault('widget', RangeWidget(attrs={"min": self.min, "max": self.max}))
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list is None or data_list == [self.min, self.max]: return None
        return {'min': data_list[0], 'max': data_list[1]}
    

class RangeDateField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(),
            forms.DateField(),
        )
        kwargs.setdefault('required', False)
        kwargs.setdefault('widget', RangeDateWidget())
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        return {'min': data_list[0], 'max': data_list[1]} if data_list else None


class KeywordField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('widget', KeywordWidget())
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        return list(value) # without this, the value is a string, e.g 


class TriStateField(forms.BooleanField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", TriStateCheckboxInput())
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)
        
    def to_python(self, value):
        return None if value is None else super().to_python(value) 


# Use just a comma sep charfield in backend and a multiple choice in frontend 
# Generally clean this mess (try to use less widgets)
class ChoiceKeywordsInputField(forms.MultipleChoiceField):
    def __init__(self, *args, **kwargs):
        url = kwargs.pop("url")
        min_query_length = kwargs.pop("min_query_length", 0)

        kwargs.setdefault('required', False)
        kwargs.setdefault('widget', forms.SelectMultiple(attrs={"class": "choice-keywords-input", "data-url": url, 
            "data-minQueryLength": min_query_length}))
        
        super().__init__(*args, **kwargs)
    
    

