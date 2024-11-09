# -*- coding: utf-8 -*-
from django.forms import ModelForm
from .models import Import


class ImportForm(ModelForm):
    class Meta:
        model = Import
        fields = ('csv_file',)
