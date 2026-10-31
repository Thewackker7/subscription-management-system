from django.contrib import admin
from .models import Quotation, QuotationLine, QuotationTemplate, QuotationTemplateLine, Subscription, SubscriptionLine

admin.site.register((Subscription, SubscriptionLine, Quotation, QuotationLine, QuotationTemplate, QuotationTemplateLine))
