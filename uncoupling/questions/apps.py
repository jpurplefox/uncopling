from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'questions'

    def ready(self):
        import questions.signals  # noqa: F401
        from questions.containers import question_container

        question_container.wire(modules=['questions.views', 'questions.signals'])
