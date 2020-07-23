# -*- coding: utf-8 -*-
import os
import telebot
from django.conf import settings

from covid.questions import QUESTIONS
from .models import Respondent

bot = telebot.TeleBot(settings.TOKEN, num_threads=5)
number_of_questions = len(QUESTIONS)
start_command = "/start"
restart_command = "Qaytadan testdan o'tish"

files = ['resources/lecheniya.pdf', 'resources/profilaktika.pdf']


def markup_choices(choices):
    if not choices:
        return telebot.types.ReplyKeyboardRemove(selective=False)

    markup = telebot.types.ReplyKeyboardMarkup(True, False)
    for choice in choices:
        markup.add(telebot.types.KeyboardButton(choice))

    return markup


@bot.message_handler()
def handler(message):
    registrant, _ = Respondent.objects.get_or_create(
        user_id=message.from_user.id,
        defaults={
            "first_name": message.from_user.first_name or "",
            "last_name": message.from_user.last_name or "",
            "username": message.from_user.username or "",
        }
    )

    response = registrant.responses.filter(completed=False).last()
    if not response or message.text in [start_command, restart_command]:
        response = registrant.responses.create()

    if number_of_questions >= response.step >= 1:
        prev_question = QUESTIONS[response.step - 1]["text"]
        response.details[prev_question] = message.text
        response.save(update_fields=["details"])

    if response.step >= number_of_questions:
        response.completed = True
        response.save(update_fields=["completed"])
        bot.send_message(
            registrant.user_id,
            "Sizda Covid-19 bo'lishi mumkin!",
            reply_markup=markup_choices([restart_command])
        )

        for filename in files:
            with open(os.path.join(settings.BASE_DIR, filename), 'rb') as file:
                bot.send_document(registrant.user_id, file)
        return

    question = QUESTIONS[response.step]
    text = question["text"]
    choices = question.get("choices") or []

    bot.send_message(registrant.user_id, text, reply_markup=markup_choices(choices))

    response.step += 1
    response.save(update_fields=["step"])
