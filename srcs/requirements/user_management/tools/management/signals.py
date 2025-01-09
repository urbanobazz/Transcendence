from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import User

@receiver(post_migrate)
def create_ai_user(sender, **kwargs):
	if sender.name == 'management':
		if not User.objects.filter(username='AI').exists():  # Ensure this runs only for the 'management' app
			User.objects.create_user(
				username='AI',
				password='ai',
				id='AI-1'
			)
			print("User: AI created.")
