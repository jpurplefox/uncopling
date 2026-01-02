from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dependency_injector.wiring import inject, Provide

from questions.containers import QuestionContainer
from questions.services import QuestionRepository


@login_required
@inject
def questions_list(
    request,
    question_repository: QuestionRepository = Provide[QuestionContainer.question_repository]
):
    """Display list of questions for the authenticated user"""
    questions = question_repository.get_by_user(request.user.meliuser)
    return render(request, 'questions/questions_list.html', {
        'questions': questions
    })
