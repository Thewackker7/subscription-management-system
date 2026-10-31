from django.contrib import admin
from .models import DiscountApplication, DiscountRule

admin.site.register((DiscountRule, DiscountApplication))
