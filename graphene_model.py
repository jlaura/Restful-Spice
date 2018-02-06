from sqlalchemy import Column, Integer, Boolean, String, Date
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from graphene_sqlalchemy import SQLAlchemyObjectType
class MetaModel(Base):
    __tablename__='metakernels'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    newest = Column(Boolean)
    path = Column(String)
    year = Column(Date)
    mission = Column(String)

class MetaM(SQLAlchemyObjectType):
    class Meta:
        model = MetaModel

import graphene
class Query(graphene.ObjectType):
    metakernels = graphene.List(MetaM)
    def resolve_metakernels(self, args, context, info):
        query = MetaM.get_query(context)
        return query.all()

schema = graphene.Schema(query=Query)
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('sqlite:///mk.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

from flask_graphql import GraphQLView
view_func = GraphQLView.as_view('graphql', schema=schema, context={'session':db_session})
app.add_url_rule('/graphql', view_func=view_func)
