from django.contrib import admin
from .models import *

admin.site.register(Task)

admin.site.register(DepartmentAnnouncement)
admin.site.register(ChatMessage)
admin.site.register(InAppEmail)
admin.site.register(InAppChat)