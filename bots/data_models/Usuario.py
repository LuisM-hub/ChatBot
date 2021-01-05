class Usuario:
    def __init__(self, nombre: str = None, apellido: str = None, tipoevento: str = None, correo: str = None ,edad: int=0, fecha: str = None, evento: str = None, alta: str = None, encuesta: str = None, pregunta1: str = None, pregunta2: str = None, pregunta3: str = None, pregunta4: str = None, pregunta5: str = None, correoencuesta: str = None, calificacion: float = 0, idevent: str = None, idevento: str = None, nombreevento: str = None):
        self.nombre = nombre
        self.apellido = apellido
        self.tipoevento = tipoevento
        self.correo = correo
        self.fecha = fecha
        self.evento = evento
        self.alta = alta
        self.encuesta = encuesta
        self.pregunta1 = pregunta1
        self.pregunta2 = pregunta2
        self.pregunta3 = pregunta3
        self.pregunta4 = pregunta4
        self.pregunta5 = pregunta5
        self.correoencuesta = correoencuesta
        self.edad = edad
        self.calificacion = calificacion
        self.idevent = idevent
        self.idevento = idevento
        self.nombreevento = nombreevento