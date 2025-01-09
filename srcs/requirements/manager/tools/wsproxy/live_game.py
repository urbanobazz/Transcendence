import json
from django.core.cache import cache

class LivePlayer:
	"""Represents an individual player in a live game session with scoring."""

	def __init__(self, player_id):
		"""
		Initialize a LivePlayer instance with a unique player identifier.

		:param player_id: Unique identifier for the player.
		"""
		self.id = player_id
		self.score = 0

	def to_dict(self):
		"""Return player data as a dictionary for JSON serialization."""
		return {"id": self.id, "score": self.score}

	def __str__(self):
		"""Return a readable string representation of the player instance."""
		return f"Player {self.id}"

class LiveGame:
	"""Represents an active game session, managing players, game state, and inputs."""

	def __init__(self, game_id):
		"""
		Initialize a LiveGame instance with a unique game identifier.

		:param game_id: Unique identifier for the game session.
		"""
		self.id = game_id
		self.message = ""
		self.state = {}
		self.inputs = {}
		self.p1 = None
		self.p2 = None
		self.cancelled = False

	@classmethod
	def from_cache_or_create(cls, game_id):
		"""
		Retrieve an existing game instance from the cache or create a new one if it doesn't exist.

		:param game_id: Unique identifier for the game session.
		:return: LiveGame instance, either retrieved from cache or newly created.
		"""
		cached_game = cache.get(f"game_{game_id}")
		if cached_game:
			return cached_game
		# Create and cache a new game instance if not found in cache
		new_game = cls(game_id)
		new_game.save_to_cache()
		return new_game

	def save_to_cache(self):
		"""Store the current game instance in the cache with no expiration."""
		cache.set(f"game_{self.id}", self, timeout=None)

	def refresh_from_cache(self):
		"""Update the current instance with data from the cached version, if available."""
		cached_game = cache.get(f"game_{self.id}")
		if cached_game:
			# Copy attributes from the cached game to the current instance
			self.state = cached_game.state
			self.inputs = cached_game.inputs
			self.p1 = cached_game.p1
			self.p2 = cached_game.p2
			self.cancelled = cached_game.cancelled
			self.message = cached_game.message

	def add_player(self, player_id):
		"""
		Add a player to the game. Assign to 'p1' if vacant, otherwise to 'p2' if 'p1' is occupied.

		:param player_id: Unique identifier for the player.
		:return: True if player was added successfully, False if both slots are filled.
		"""
		self.refresh_from_cache()
		if not self.p1:
			self.p1 = LivePlayer(player_id)
		elif not self.p2:
			self.p2 = LivePlayer(player_id)
		else:
			return False
		self.save_to_cache()
		return True

	def to_dict(self):
		"""
		Convert game information into a dictionary format suitable for JSON serialization.

		:return: Dictionary containing game details, including state, inputs, and players.
		"""
		return {
			"id": self.id,
			"state": self.state,
			"inputs": self.inputs,
			"p1": self.p1.to_dict() if self.p1 else None,
			"p2": self.p2.to_dict() if self.p2 else None
		}

	def check_ready(self):
		"""
		Check if both player slots (p1 and p2) are occupied.

		:return: True if both players are present, otherwise False.
		"""
		self.refresh_from_cache()
		return self.p1 is not None and self.p2 is not None
