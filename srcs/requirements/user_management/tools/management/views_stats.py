from .models import Game, User
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .utils import create_game, getUserFromId
import logging, json

# @csrf_exempt
# def updateStats()
