from django.shortcuts import render, redirect

from app.views import AuthMixin, BaseView
from .models import EntryLog, Summary


class EntryLogView(AuthMixin, BaseView):
    def get(self, request):
        if not (request.user.is_staff or request.user.username == 'bot'):
            return redirect('authentication:login')
        logs = EntryLog.objects.all().order_by('-created_at')
        self.context['logs'] = logs
        self.set_pagination(logs, request, count=50)
        return render(request, 'entry_log_page.html', self.context)


class SummaryView(AuthMixin, BaseView):
    def get(self, request):
        if not (request.user.is_staff or request.user.username == 'bot'):
            return redirect('authentication:login')
        logs = Summary.objects.all().order_by('-interval')
        self.context['logs'] = logs
        return render(request, 'log_summary_page.html', self.context)
