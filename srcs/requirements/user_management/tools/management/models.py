import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, UserManager
import string
import random
import logging

logger = logging.getLogger('management')


def generate_short_id(prefix, length=4):
	characters = string.ascii_letters + string.digits
	suffix = ''.join(random.choice(characters) for _ in range(length))
	return f"{prefix}{suffix}"


def generate_user_id():
	return generate_short_id('U-')


def generate_tournament_id():
	return generate_short_id('T-')


def generate_game_id():
	return generate_short_id('G-')


# Create your models here.
class Game(models.Model):
	id = models.CharField(max_length=8, primary_key=True, default=generate_game_id, editable=False)
	name = models.CharField(max_length=100, null=True, blank=True, default='Game')
	start_date = models.DateTimeField(auto_now_add=True)
	end_date = models.DateTimeField(null=True, blank=True)
	duration = models.DurationField(null=True, blank=True)
	winner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='game_winner')
	player1 = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='game_player1', null=True)
	player2 = models.ForeignKey('User', on_delete=models.SET_NULL, related_name='game_player2', null=True)
	scores = models.JSONField(default=dict)
	can_join = models.BooleanField(default=False)
	closed = models.BooleanField(default=False)
	tournament = models.ForeignKey('Tournament', on_delete=models.SET_NULL, null=True, related_name='game_tournament')
	round = models.IntegerField(default=0)
	speed = models.CharField(max_length=100, null=True, blank=True, default='1')
	power_ups = models.BooleanField(default=True)

	def __str__(self):
		return str(self.game_id)


class UserStats(models.Model):
	user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='stats_user')
	games_played = models.ManyToManyField(Game, related_name='stats_games')
	tournaments_played = models.ManyToManyField('Tournament', related_name='stats_tournaments')
	wins = models.IntegerField()
	losses = models.IntegerField()
	avg_duration = models.IntegerField()

	def __str__(self):
		return str(self.user)


class UserManager(BaseUserManager):

	def create_user(self, username, password=None, **extra_fields):
		if not username:
			raise ValueError('The Username field is required')
		# Create User object (but do not assign stats yet)
		user = self.model(username=username, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)  # Save the User first
		# Create and save the UserStats object after the User has been saved
		user_stats = UserStats.objects.create(user=user, wins=0, losses=0, avg_duration=0)
		# Assign stats to the user and save the user again
		user.stats = user_stats
		user.save(using=self._db)

		return user


class User(AbstractBaseUser):
	id = models.CharField(max_length=8, primary_key=True, default=generate_user_id, editable=False)
	username = models.CharField(max_length=100, unique=True)
	create_date = models.DateTimeField(auto_now_add=True)
	friends = models.ManyToManyField('self', symmetrical=False, related_name='friend_set')
	blocked = models.ManyToManyField('self', symmetrical=False, related_name='blocked_set')
	stats = models.OneToOneField(UserStats, on_delete=models.CASCADE, related_name='stats', null=True)
	avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default='static/avatar.png')

	objects = UserManager()

	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = []

	def save(self, *args, **kwargs):
		# Ensure the avatars directory exists
		avatar_dir = os.path.join(settings.BASE_DIR, 'data/avatars/')
		if self.avatar and not os.path.exists(avatar_dir):
			os.makedirs(avatar_dir)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.username


class TournamentPlayer(models.Model):
	tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE)
	player = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tournament_player')
	wins = models.IntegerField(default=0)
	rank_position = models.IntegerField(default=0)

	class Meta:
		unique_together = ('tournament', 'player')


class Tournament(models.Model):
	id = models.CharField(max_length=8, primary_key=True, default=generate_tournament_id, editable=False)
	name = models.CharField(max_length=100)
	n_players = models.IntegerField(default=4)
	start_date = models.DateTimeField(auto_now_add=True, null=True)
	end_date = models.DateTimeField(null=True, blank=True)
	duration = models.DurationField(null=True, blank=True)
	winner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
	matches = models.ManyToManyField(Game, related_name='matches')
	players = models.ManyToManyField('User', through='TournamentPlayer', related_name='tournament_players')
	rounds = models.IntegerField(default=0, null=True)
	owner = models.ForeignKey('User', on_delete=models.CASCADE, related_name='tournament_owner')
	ready = models.IntegerField(default=0, null=True)
	speed = models.CharField(max_length=100, null=True, blank=True, default='1')
	power_ups = models.BooleanField(default=True)

	#Probably not keeping this function
	def calculate_rankings(self):
		# Reset ranks
		TournamentPlayer.objects.filter(tournament=self).update(wins=0)
		# Calculate ranks based on matches won
		for match in self.matches.all():
			if match.winner:
				tournament_player = TournamentPlayer.objects.get(
					tournament=self, player=match.winner)
				tournament_player.wins += 1
				tournament_player.save()
		# Sort players by wins
		players = TournamentPlayer.objects.filter(
			tournament=self).order_by('-wins')
		# Assign ranks
		rank_position = 1
		for player in players:
			player.rank_position = rank_position
			player.save()
			rank_position += 1

	def getRanking(self):
		return TournamentPlayer.objects.filter(
			tournament=self).order_by('rank_position')

	def getUserRanking(self, user):
		return TournamentPlayer.objects.get(tournament=self, player=user).rank_position

	def addPlayer(self, player):
		TournamentPlayer.objects.create(tournament=self, player=player)
		self.ready += 1
		self.save()

	def removePlayer(self, player):
		TournamentPlayer.objects.get(tournament=self, player=player).delete()
		self.ready -= 1
		self.save()

	def __str__(self):
		return str(self.id)
