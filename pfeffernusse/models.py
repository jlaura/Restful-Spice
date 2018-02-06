from sqlalchemy import Column, Integer, Boolean, String, Date, MetaData, ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy.ext.declarative import declarative_base

from flask_sqlalchemy import SQLAlchemy



metadata = MetaData()
Base = declarative_base(metadata=metadata)

db = SQLAlchemy(metadata=metadata)


class Missions(Base):
    __tablename__ = 'missions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    @property
    def serialize(self):
        return {'id':self.id,
                'name':self.name}

class Kernels(Base):
    __tablename__='kernels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    newest = Column(Boolean)
    path = Column(String)
    year = Column(Date)
    mission_id = Column(Integer, ForeignKey(Missions.id))

    mission = relationship('Missions', foreign_keys='Kernels.mission_id', lazy='joined')

    def __repr__(self):
        return "id: {}, name:{}, newest:{}, path:{}, year:{}, mission: {}".format(self.id,
                self.name, self.newest, self.path, self.year, self.mission)

    @property
    def serialize(self):
        return {'id':self.id,
                'name':self.name,
                'newest':self.newest,
                'path':self.path,
                'year':self.year.isoformat(),
                'mission':self.mission.serialize}
