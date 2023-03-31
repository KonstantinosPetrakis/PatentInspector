from datetime import datetime
from django import forms


# ----------------- Fields -----------------
class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)
        self.choices.insert(0, (None, '---'))
        self.widget.attrs.update({"class": "form-select"})


class RangeField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (
            forms.IntegerField(),
            forms.IntegerField(),
        )
        kwargs.setdefault('widget', RangeWidget(attrs={"min": kwargs.pop("min"), "max": kwargs.pop("max")}))
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
            return {'min': data_list[0], 'max': data_list[1]} if data_list else None
    

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


# ----------------- Widgets -----------------
class RangeWidget(forms.MultiWidget):
    template_name = "widgets/range.html"

    def __init__(self, attrs=None):
        widgets = [
            forms.NumberInput(attrs={"type": "range", "min": attrs["min"], "max": attrs["max"], "value": 0}),
            forms.NumberInput(attrs={"type": "range", "min": attrs["min"], "max": attrs["max"], "value": attrs["max"]}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        return [value.get('min'), value.get('max')] if value else [None, None]


class RangeDateWidget(forms.MultiWidget):
    template_name = "widgets/range_date.html"

    def __init__(self, attrs=None):
        widgets = [
            forms.DateInput(),
            forms.DateInput()
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        return [value.get('min'), value.get('max')] if value else [None, None]