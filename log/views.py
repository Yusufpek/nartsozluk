from django.shortcuts import render

# Create your views here.
from .models import Log
from dictionary.views import AuthMixin, BaseView


class MonitorTasks(AuthMixin, BaseView):
    def get(self, request):
        super().get(request)
        logs = Log.objects.all().order_by('-start_time')
        self.set_pagination(logs, request, 50)
        return render(request, 'monitor_tasks_page.html', self.context)
