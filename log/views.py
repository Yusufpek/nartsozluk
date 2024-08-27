from django.shortcuts import render

# Create your views here.
from .models import Log
from app.views import AuthMixin, BaseView


class MonitorTasks(AuthMixin, BaseView):
    def get(self, request):
        super().get(request)
        logs = Log.objects.all().order_by('-start_time')
        print(logs)
        self.context['logs'] = logs
        return render(request, 'monitor_tasks_page.html', self.context)