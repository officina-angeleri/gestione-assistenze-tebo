from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, joinedload
import datetime
import os

# Component data is now loaded dynamically from the ProductRegistry via JSON files.
Base = declarative_base()

class Intervento(Base):
    __tablename__ = 'interventi'
    
    id = Column(Integer, primary_key=True)
    prodotto = Column(String(50), nullable=False)
    data = Column(DateTime, default=datetime.datetime.now)
    ore_lavoro = Column(Float, default=0.0)
    note_tecniche = Column(Text)
    descrizione = Column(Text)
    
    componenti = relationship("ComponenteIntervento", back_populates="intervento", cascade="all, delete-orphan")

class ComponenteIntervento(Base):
    __tablename__ = 'componenti_intervento'
    
    id = Column(Integer, primary_key=True)
    intervento_id = Column(Integer, ForeignKey('interventi.id'))
    numero_componente = Column(Integer, nullable=False)
    codice_componente = Column(String(50))
    descrizione_componente = Column(String(255))
    quantita = Column(Float, default=1.0)
    sostituito = Column(Boolean, default=True)
    note = Column(String(255))
    
    intervento = relationship("Intervento", back_populates="componenti")

class DatabaseManager:
    def __init__(self, db_path='gestione_assistenze.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()

    def add_intervento(self, prodotto, ore, note, descrizione, componenti_data=None):
        session = self.get_session()
        try:
            nuovo = Intervento(
                prodotto=prodotto,
                ore_lavoro=ore,
                note_tecniche=note,
                descrizione=descrizione
            )
            if componenti_data:
                for comp in componenti_data:
                    c = ComponenteIntervento(
                        numero_componente=comp['numero'],
                        codice_componente=comp.get('codice', ''),
                        descrizione_componente=comp.get('descrizione', ''),
                        quantita=comp.get('quantita', 1.0),
                        sostituito=comp.get('sostituito', True),
                        note=comp.get('note', '')
                    )
                    nuovo.componenti.append(c)
            session.add(nuovo)
            session.commit()
            return nuovo.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_intervento(self, id_intervento, ore, note, descrizione, componenti_data=None):
        session = self.get_session()
        try:
            inv = session.query(Intervento).filter(Intervento.id == id_intervento).first()
            if not inv: return False
            
            inv.ore_lavoro = ore
            inv.note_tecniche = note
            inv.descrizione = descrizione
            
            # Clear old components
            session.query(ComponenteIntervento).filter(ComponenteIntervento.intervento_id == id_intervento).delete()
            
            # Add new components
            if componenti_data:
                for comp in componenti_data:
                    c = ComponenteIntervento(
                        intervento_id=id_intervento,
                        numero_componente=comp['numero'],
                        codice_componente=comp.get('codice', ''),
                        descrizione_componente=comp.get('descrizione', ''),
                        quantita=comp.get('quantita', 1.0),
                        sostituito=comp.get('sostituito', True),
                        note=comp.get('note', '')
                    )
                    session.add(c)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_interventi(self, prodotto=None):
        session = self.get_session()
        try:
            query = session.query(Intervento).options(joinedload(Intervento.componenti))
            if prodotto:
                query = query.filter(Intervento.prodotto == prodotto)
            return query.order_by(Intervento.data.desc()).all()
        finally:
            session.close()

    def delete_intervento(self, id_intervento):
        session = self.get_session()
        try:
            # Delete components first (cascade-like)
            session.query(ComponenteIntervento).filter(ComponenteIntervento.intervento_id == id_intervento).delete()
            # Delete intervention
            inv = session.query(Intervento).filter(Intervento.id == id_intervento).first()
            if inv:
                session.delete(inv)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
