from social_core.exceptions import AuthForbidden
from social_core.pipeline.user import USER_FIELDS
from django.contrib.auth import authenticate


def check_password(strategy, backend, user, is_new=False, *args, **kwargs):
    if backend.name != 'email':
        return

    password = strategy.request_data()['password']

    if is_new:
        user.set_password(password)
        user.save()
    elif not authenticate(email=user.email, password=password):
        raise AuthForbidden(backend)


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    print(user)
    if user:
        return {'is_new': False}

    email = details.get('email')

    fields = dict((name, kwargs.get(name, details.get(name)))
                  for name in backend.setting('USER_FIELDS', USER_FIELDS))
    if not fields:
        return

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }
