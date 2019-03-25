import graphene
from graphene_django.types import DjangoObjectType
from django.contrib.auth import get_user_model
from graphene import relay, ObjectType
import graphql_jwt
from graphql_jwt.decorators import login_required
from graphql_jwt.shortcuts import get_token
from django.contrib.auth import authenticate
import graphql_social_auth
from social_core.actions import do_complete, do_auth
from social_core.backends.email import EmailAuth
from social_core.utils import partial_pipeline_data
from social_django.utils import load_backend, load_strategy


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        interfaces = (relay.Node, )


class EmailAuth(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        password = graphene.String()

    user = graphene.Field(UserType)
    token = graphene.String()

    def mutate(self, info, email, password):
        strategy = load_strategy(info.context)

        def _request_data():
            return {
                'email': email,
                'password': password
            }

        strategy.request_data = _request_data

        print(strategy.request_data())

        backend = load_backend(strategy, 'email', redirect_uri=None)

        # user = backend.strategy.authenticate(backend=backend, email=email, password=password)
        user = None
        partial = partial_pipeline_data(backend, user)

        if partial:
            user = backend.continue_pipeline(partial)
            # clean partial data after usage
            backend.strategy.clean_partial_pipeline(partial.token)
        else:
            user = backend.complete(user=user)

        # Get a token for that user, (if there is a user?)
        token = get_token(user)

        return EmailAuth(user=user, token=token)


class Query(ObjectType):
    user = graphene.Field(UserType)


class Mutation(ObjectType):
    email_auth = EmailAuth.Field()
    social_auth = graphql_social_auth.SocialAuthJWT.Field()
