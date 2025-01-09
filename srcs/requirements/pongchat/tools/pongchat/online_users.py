from django.core.cache import cache

def add_online_user(user):
	cache.add(f"user:{user}", True, timeout=None)

def remove_online_user(user):
	cache.delete(f"user:{user}")

def get_online_users(blocklist):
	keys = cache.iter_keys("user:*")
	return [key.split(":", 1)[1] for key in keys if key.split(":", 1)[1] not in blocklist]
