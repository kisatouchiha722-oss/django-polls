from django.db import models
from django.contrib.auth import models as auth_models
from django.contrib.auth.models import User  # Для работы нашей новой модели

# --- ТВОИ ОРИГИНАЛЬНЫЕ МОДЕЛИ (БЕЗ ДУБЛИКАТОВ) ---

class Poll(models.Model):
    title = models.CharField(max_length=255, verbose_name="Вопрос опроса")
    description = models.TextField(verbose_name="Описание опроса", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    author = models.ForeignKey(auth_models.User, on_delete=models.CASCADE, verbose_name="Автор")

    def __str__(self):
        return self.title

class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choices', verbose_name="Опрос")
    choice_text = models.CharField(max_length=255, verbose_name="Текст ответа")
    votes_count = models.IntegerField(default=0, verbose_name="Голосов собрано")

    def __str__(self):
        return self.choice_text


# --- НОВАЯ МОДЕЛЬ ДЛЯ ОБРАТНОЙ СВЯЗИ (В ОДНОМ ЭКЗЕМПЛЯРЕ) ---

class Feedback(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='feedbacks', verbose_name="Опрос")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор отзыва")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Отзыв от {self.user.username} к опросу {self.poll.title}"