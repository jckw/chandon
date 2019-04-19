"""
A kind of monkey patch for 'django-graphql-jwt' until https://github.com/flavors/django-graphql-jwt/issues/91 is resolved.
"""
from django.utils.translation import ugettext as _
import jwt
import graphene
from graphene.types.generic import GenericScalar
from graphql_jwt.settings import jwt_settings
from graphql_jwt import exceptions
from graphql_jwt.utils import get_user_by_payload
from graphql_jwt.mixins import RefreshTokenMixin, JSONWebTokenMixin
from graphql_jwt.decorators import setup_jwt_cookie


def jwt_decode(token, context=None, refresh=False):
    return jwt.decode(
        token,
        jwt_settings.JWT_SECRET_KEY,
        jwt_settings.JWT_VERIFY,
        options={
            'verify_exp': False if refresh else jwt_settings.JWT_VERIFY_EXPIRATION,
        },
        leeway=jwt_settings.JWT_LEEWAY,
        audience=jwt_settings.JWT_AUDIENCE,
        issuer=jwt_settings.JWT_ISSUER,
        algorithms=[jwt_settings.JWT_ALGORITHM])


def get_payload(token, context=None, refresh=False):
    try:
        payload = jwt_decode(token, context, refresh)
    except jwt.ExpiredSignature:
        raise exceptions.JSONWebTokenExpired()
    except jwt.DecodeError:
        raise exceptions.JSONWebTokenError(_('Error decoding signature'))
    except jwt.InvalidTokenError:
        raise exceptions.JSONWebTokenError(_('Invalid token'))
    return payload


class KeepAliveRefreshMixin(object):

    class Fields:
        token = graphene.String(required=True)

    @classmethod
    @setup_jwt_cookie
    def refresh(cls, root, info, token, **kwargs):
        context = info.context
        payload = get_payload(token, context, refresh=True)
        user = get_user_by_payload(payload)
        orig_iat = payload.get('origIat')

        if not orig_iat:
            raise exceptions.JSONWebTokenError(_('origIat field is required'))

        if jwt_settings.JWT_REFRESH_EXPIRED_HANDLER(orig_iat, context):
            raise exceptions.JSONWebTokenError(_('Refresh has expired'))

        payload = jwt_settings.JWT_PAYLOAD_HANDLER(user, context)
        payload['origIat'] = orig_iat

        token = jwt_settings.JWT_ENCODE_HANDLER(payload, context)
        return cls(token=token, payload=payload)


class RefreshMixin((RefreshTokenMixin
                    if jwt_settings.JWT_LONG_RUNNING_REFRESH_TOKEN
                    else KeepAliveRefreshMixin),
                   JSONWebTokenMixin):

    payload = GenericScalar()


class Refresh(RefreshMixin, graphene.Mutation):

    class Arguments(RefreshMixin.Fields):
        """Refresh Arguments"""

    @classmethod
    def mutate(cls, *arg, **kwargs):
        return cls.refresh(*arg, **kwargs)
