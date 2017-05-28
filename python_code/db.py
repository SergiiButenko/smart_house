# coding: utf-8
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Text, Time, text
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('postgres://sprinkler:drop#@185.20.216.94:35432/test', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                     autoflush=False,
                                     bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
metadata = Base.metadata


class CurrentLinesState(Base):
    __tablename__ = 'current_lines_state'

    id = Column(Integer, primary_key=True, server_default=text("nextval('current_lines_state_id_seq'::regclass)"))
    line_id = Column(ForeignKey(u'lines.id'), nullable=False)
    state_id = Column(ForeignKey(u'state_of_line.id'), nullable=False)

    line = relationship(u'Line')
    state = relationship(u'StateOfLine')


class DayOfWeek(Base):
    __tablename__ = 'day_of_week'

    id = Column(Integer, primary_key=True, server_default=text("nextval('day_of_week_id_seq'::regclass)"))
    num = Column(Integer, nullable=False, unique=True)
    name = Column(Text, nullable=False)


class Life(Base):
    __tablename__ = 'life'

    id = Column(Integer, primary_key=True, server_default=text("nextval('life_id_seq'::regclass)"))
    line_id = Column(ForeignKey(u'lines.id'), nullable=False)
    rule_id = Column(ForeignKey(u'type_of_rule.id'), nullable=False)
    state = Column(Integer, nullable=False, server_default=text("0"))
    date = Column(Date, nullable=False)
    timer = Column(DateTime, nullable=False)

    line = relationship(u'Line')
    rule = relationship(u'TypeOfRule')


class Line(Base):
    __tablename__ = 'lines'

    id = Column(Integer, primary_key=True, server_default=text("nextval('lines_id_seq'::regclass)"))
    number = Column(Integer, nullable=False)
    name = Column(Text)


class StateOfLine(Base):
    __tablename__ = 'state_of_line'

    id = Column(Integer, primary_key=True, server_default=text("nextval('state_of_line_id_seq'::regclass)"))
    short_name = Column(Text, nullable=False)
    full_name = Column(Text, nullable=False)


class TypeOfRule(Base):
    __tablename__ = 'type_of_rule'

    id = Column(Integer, primary_key=True, server_default=text("nextval('type_of_rule_id_seq'::regclass)"))
    name = Column(Text, nullable=False)


class WeekSchedule(Base):
    __tablename__ = 'week_schedule'

    id = Column(Integer, primary_key=True, server_default=text("nextval('week_schedule_id_seq'::regclass)"))
    day_number = Column(ForeignKey(u'day_of_week.num'), nullable=False, index=True)
    line_id = Column(ForeignKey(u'lines.id'), nullable=False)
    rule_id = Column(ForeignKey(u'type_of_rule.id'), nullable=False)
    time = Column(Time, nullable=False)
    interval = Column(Integer, nullable=False)

    day_of_week = relationship(u'DayOfWeek')
    line = relationship(u'Line')
    rule = relationship(u'TypeOfRule')