from sqlalchemy import Column, Integer, Boolean, String, Date

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class MetaKernels(db.Model):
    __tablename__='metakernels'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    newest = Column(Boolean)
    path = Column(String)
    year = Column(Date)
    mission = Column(String)

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
                'mission':self.mission}
