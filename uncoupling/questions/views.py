from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Question


@login_required
def questions_list(request):
    questions = Question.objects.filter(
        meli_user=request.user.meliuser,
    )
    return render(request, 'questions/questions_list.html', {
        'questions': questions
    })
