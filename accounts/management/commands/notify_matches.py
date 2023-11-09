from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
import logging

from accounts.models import Match
from game.models import GameSession, Player

# Configure a logger for the command
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sends notifications to users about new matches at midnight."

    def handle(self, *args, **options):
        yesterday = timezone.now() - timedelta(days=1)
        new_matches = Match.objects.filter(
            matched_at__gte=yesterday, notification_sent=False
        )

        for match in new_matches:
            try:
                # Create the GameSession and Players within a transaction
                with transaction.atomic():
                    # Create a new GameSession instance
                    game_session = GameSession(is_active=True)
                    game_session.save()

                    # Get or create the Player instances, associating them with the new GameSession
                    playerA, _ = Player.objects.get_or_create(user=match.user1, defaults={'game_session': game_session})
                    playerB, _ = Player.objects.get_or_create(user=match.user2, defaults={'game_session': game_session})

                    # Link the GameSession with the Players
                    game_session.playerA = playerA
                    game_session.playerB = playerB
                    game_session.save()

                    # Initialize the game session if it's newly created
                    if not game_session.current_game_turn_id:
                        game_session.initialize_game()

                    # Generate the URL for the game session
                    game_session_url = self.get_full_url_with_domain(game_session.get_absolute_url())

                # Send email notifications
                self.send_email(match.user1, game_session_url, 'You have a new match!')
                self.send_email(match.user2, game_session_url, 'You have a new match!')

                # Mark the match as notified
                match.notification_sent = True
                match.save()

                success_message = f"Notification sent for match between {match.user1.username} and {match.user2.username}. Game session link included: {game_session_url}"
                self.stdout.write(self.style.SUCCESS(success_message))

            except Exception as e:
                error_message = f"Failed to send notification for match between {match.user1.username} and {match.user2.username}: {e}"
                logger.error(error_message)
                self.stderr.write(self.style.ERROR(error_message))

    def send_email(self, user, url, subject):
        message = f"Hello {user.username},\n\nYou have been matched with someone on our platform. Please log in to see more details about your match.\n\nClick here to join the game: {url}"
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    
    def get_full_url_with_domain(self, relative_url):
        site_url = settings.SITE_URL.rstrip('/') + '/'
        return f"{site_url}{relative_url.lstrip('/')}"

