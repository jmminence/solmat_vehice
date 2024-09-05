from django.contrib.auth.hashers import check_password
from django.contrib.auth.backends import ModelBackend

from accounts.models import User


class EmailCheckBackend(object):
    """
    Authentication backend that allows the user to log in with his/her
    email address as username.
    """

    def authenticate(self, username=None, password=None):
        """
        *username* is actually the email address.
        """
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'email': username}
        try:
            user = User.objects.get(**kwargs)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try: return User.objects.get(pk=user_id)
        except User.DoesNotExist: return None


class ProxiedModelBackend(ModelBackend):

    def get_user(self, user_id):
        try: return User.objects.get(pk=user_id)
        except User.DoesNotExist: return None
