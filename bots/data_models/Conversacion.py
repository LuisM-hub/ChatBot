from enum import Enum

class Pregunta(Enum):
    NOMBRE = 1
    EDAD = 2
    FECHA = 3
    NONE = 4

class PreguntaEvento(Enum):
    EVENTO = 1
    NONE = 2
    SINO = 3

class AltaEvento(Enum):
    NOMBRE = 1
    APELLIDO = 2
    TIPOEVENTO = 3
    FECHA = 4 
    CORREO = 5
    NONE = 6
    SINO = 7

class Encuesta(Enum):
    SUEVENTO = 1
    CORREO = 2
    PREGUNTA1 = 3
    PREGUNTA2 = 4
    PREGUNTA3 = 5
    PREGUNTA4 = 6
    PREGUNTA5 = 7
    NONE = 8
    SINO = 9

class Multiconversacion(Enum):
    PosventaConsultarEvento = 1
    DarAltaEvento = 2
    Encuesta = 3
    NONE = 4

class Conversacion:
    def __init__(self, pregunta_anterior: Pregunta = Pregunta.NONE, pregunta_eventoanterior: PreguntaEvento = PreguntaEvento.NONE, pregunta_alta_anterior: AltaEvento = AltaEvento.NONE ,multiconversacion: Multiconversacion = Multiconversacion.NONE, pregunta_encuesta_anterior: Encuesta = Encuesta.NONE):
        self.pregunta_anterior = pregunta_anterior
        self.pregunta_eventoanterior = pregunta_eventoanterior
        self.BanderaConversacionAbierta = multiconversacion
        self.pregunta_alta_anterior = pregunta_alta_anterior
        self.pregunta_encuesta_anterior = pregunta_encuesta_anterior
        #Si necesitas gestionar dos o más conversaciones agregar más propiedades.