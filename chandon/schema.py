from users import schema
import graphene


class Viewer(schema.Viewer, graphene.ObjectType):
    pass


class Query(schema.Query, graphene.ObjectType):
    viewer = graphene.Field(Viewer)


class Mutation(schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
