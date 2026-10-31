from django.contrib import admin
from .models import Plan, Product, ProductVariant, TaxRule
admin.site.register((Product, ProductVariant, Plan, TaxRule))
