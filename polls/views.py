import json
import g4f
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Poll, Choice, Feedback  # Добавили импорт Feedback


# 1. Главная страница со списком опросов
def index(request):
    latest_polls = Poll.objects.all().order_by('-created_at')
    return render(request, 'polls/index.html', {'latest_polls': latest_polls})


# 2. Страница самого опроса (где выбирают радио-кнопку)
def detail(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    return render(request, 'polls/detail.html', {'poll': poll})


# 3. Обработка отправки голоса в базу данных
def vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    try:
        try:
            selected_choice = poll.choice_set.get(pk=request.POST['choice'])
        except AttributeError:
            selected_choice = poll.choices.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {
            'poll': poll,
            'error_message': "Вы не выбрали вариант ответа!",
        })
    else:
        selected_choice.votes_count += 1
        selected_choice.save()
        return redirect('polls:results', poll_id=poll.id)


# 4. Страница результатов голосования
def results(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    return render(request, 'polls/results.html', {'poll': poll})


# 5. Страница ИИ-помощника (чат-бота)
def ai_assistant(request):
    return render(request, 'polls/ai_assistant.html')


# 6. API для обработки вопросов пользователя нейросетью
def ai_chat_api(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')

        polls = Poll.objects.all()
        site_data = "Текущие опросы на нашем сайте:\n"
        for p in polls:
            p_text = getattr(p, 'text', getattr(p, 'title', getattr(p, 'question_text', str(p))))

            if hasattr(p, 'choices'):
                choices_list = p.choices.all()
            else:
                choices_list = p.choice_set.all()

            choice_text = ", ".join([f"{c.choice_text} (голосов: {c.votes_count})" for c in choices_list])
            site_data += f"- ID {p.id}: {p_text}. Варианты: {choice_text}.\n"

        system_instruction = f"""
        Ты — продвинутый ИИ-ассистент "Системы опросов".

        {site_data}

        У тебя есть ЧЕТЫРЕ функции:
        1. АНАЛИЗ САЙТА: Отвечай на вопросы по текущим опросам, используя локальные данные выше.
        2. ОТВЕТ ИЗВНЕ: Если вопрос общего характера, ответь на основе своих знаний.
        3. СОЗДАНИЕ ОПРОСА: Если просят создать опрос, верни СТРОГО JSON:
        {{"action": "create_poll", "question": "Текст вопроса", "choices": ["В1", "В2"]}}
        4. УДАЛЕНИЕ ОПРОСА: Если пользователь просит удалить опрос, найди этот опрос в списке выше, узнай его ID и верни СТРОГО JSON:
        {{"action": "delete_poll", "poll_id": ID_опроса}}

        Внимательно слушай пользователя: {user_message}
        """

        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
            )
        except Exception:
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
            )

        clean_response = response.strip()
        json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)

        if json_match:
            try:
                command = json.loads(json_match.group(0))

                if command.get("action") == "create_poll":
                    q_text = command.get("question")
                    choices = command.get("choices", [])

                    if q_text and choices:
                        from django.contrib.auth.models import User
                        current_author = request.user if request.user.is_authenticated else User.objects.first()

                        try:
                            new_poll = Poll.objects.create(text=q_text, author=current_author,
                                                           created_at=timezone.now())
                        except TypeError:
                            try:
                                new_poll = Poll.objects.create(title=q_text, author=current_author,
                                                               created_at=timezone.now())
                            except TypeError:
                                new_poll = Poll.objects.create(question_text=q_text, author=current_author,
                                                               created_at=timezone.now())

                        for choice_text in choices:
                            Choice.objects.create(poll=new_poll, choice_text=choice_text, votes_count=0)

                        return JsonResponse({
                            'reply': f"✨ **Успешно создано!** Я добавил на сайт новый опрос: «{q_text}»."
                        })

                elif command.get("action") == "delete_poll":
                    target_id = command.get("poll_id")
                    if target_id:
                        poll_to_delete = Poll.objects.get(pk=target_id)
                        poll_title = getattr(poll_to_delete, 'text', getattr(poll_to_delete, 'title',
                                                                             getattr(poll_to_delete, 'question_text',
                                                                                     str(poll_to_delete))))
                        poll_to_delete.delete()

                        return JsonResponse({
                            'reply': f"🗑️ **Успешно удалено!** Опрос «{poll_title}» (ID: {target_id}) был полностью удален с сайта."
                        })

            except Poll.DoesNotExist:
                return JsonResponse({'reply': "⚠️ Опрос с таким ID не найден в базе данных."})
            except Exception as db_err:
                return JsonResponse({'reply': f"⚙️ Ошибка Django ORM при обработке: {str(db_err)}"})

        return JsonResponse({'reply': response})

    except Exception as e:
        return JsonResponse({'reply': f"Ошибка ИИ-ассистента: {str(e)}"}, status=500)


# --- ТРЕБОВАНИЕ ПРЕПОДАВАТЕЛЯ: АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ ---

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('polls:index')  # Перенаправление на главную страницу опросов
    else:
        form = UserCreationForm()
    return render(request, 'polls/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('polls:index')
    else:
        form = AuthenticationForm()
    return render(request, 'polls/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('polls:index')


# --- ТРЕБОВАНИЕ ПРЕПОДАВАТЕЛЯ: ОБРАТНАЯ СВЯЗЬ (ОТЗЫВЫ) ---

@login_required(login_url='polls:login')  # Защита: оставлять отзывы могут только залогиненные
def add_feedback(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if request.method == 'POST':
        text = request.POST.get('feedback_text')
        if text:
            Feedback.objects.create(
                poll=poll,
                user=request.user,
                text=text
            )
    return redirect('polls:detail', poll_id=poll.id)  # Возвращаем на страницу этого же опроса