#---LUIS--- RecognizerResult
#from _typeshed import OpenBinaryModeReading
from os import truncate
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext, UserState, ConversationState, RecognizerResult, recognizer
from botbuilder.schema import ChannelAccount, HeroCard
from recognizers_number.number.chinese.parsers import ChineseNumberParserConfiguration

from .data_models import Usuario, Conversacion, Pregunta, Encuesta, PreguntaEvento, Multiconversacion, AltaEvento

from recognizers_number import recognize_number, Culture
from datetime import date
#Clase de configuración para enviar variables del QNA
from config import DefaultConfig
#Libreria del QnA
from botbuilder.ai.qna import QnAMaker, QnAMakerEndpoint
#---LUIS--- ai - result Libreria de manejo de respuestas
from botbuilder.ai.luis import LuisApplication, LuisRecognizer, LuisPredictionOptions
from azure.cognitiveservices.language.luis.runtime.models import LuisResult
#DB
import mysql.connector as mysql

class ValidacionEspecial:
    def __init__(self, aceptado:bool = False, valor: object = None, mensaje: str = None):
        self.aceptado=aceptado
        self.valor=valor
        self.mensaje=mensaje


class BotImitador(ActivityHandler):

    def __init__(self, conversation_state: ConversationState, user_state: UserState, config: DefaultConfig):
        self.user_state = user_state
        self.conversation_state = conversation_state
        self.perfil = self.user_state.create_property("Usuario")
        self.conversacion = self.conversation_state.create_property("Conversacion")
        #Conectamos el QNA con nuestro BOT
        self.qna_maker = QnAMaker(
            QnAMakerEndpoint(
                knowledge_base_id=config.QNA_KNOWLEDGEBASE_ID,
                endpoint_key=config.QNA_ENDPOINT_KEY,
                host=config.QNA_ENDPOINT_HOST,
            )
        )
        #---LUIS--- # Encender includeApiResults - true, Nos devuelve la respuesta completa
        # Incluiran propiedades --- en RecognizerResult
        #---LUIS---  APP
        luis_application = LuisApplication(config.LUIS_APP_ID,config.LUIS_API_KEY,'https://'+config.LUIS_API_HOST_NAME)
        #---LUIS---  OPCIONES
        luis_options = LuisPredictionOptions(include_all_intents = True, include_instance_data = True)
        #---LUIS---  IDENTIFICADOR
        self.recognizer = LuisRecognizer(luis_application, luis_options, True)

    
    async def on_members_added_activity(self, members_added: [ChannelAccount], turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hola mi nombre es Sura")

    async def on_message_activity(self, turn_context: TurnContext):
        #print("Antes del IF")
        perfil = await self.perfil.get(turn_context, Usuario)
        conversacion = await self.conversacion.get(turn_context, Conversacion)
        #print(conversacion.BanderaConversacionAbierta)
        if conversacion.BanderaConversacionAbierta != Multiconversacion.NONE:
            #print("Entro al IF")
            recognizer_result = await self.recognizer.recognize(turn_context)
            intent = conversacion.BanderaConversacionAbierta.name
            #print("El intento es " + intent)
            await self._dispatch_to_top_intent(turn_context, intent, recognizer_result)
        else:
            recognizer_result = await self.recognizer.recognize(turn_context)
            intent= LuisRecognizer.top_intent(recognizer_result)
            #await turn_context.send_activity("Intención: " + intent)
            await self._dispatch_to_top_intent(turn_context, intent, recognizer_result)
    #---DISPATCHER---
    async def _dispatch_to_top_intent(self, turn_context: TurnContext, intent, recognizer_result: RecognizerResult):
        perfil = await self.perfil.get(turn_context, Usuario)
        conversacion = await self.conversacion.get(turn_context, Conversacion)
        #print("Entro al dispatcher")
        if intent == "l_HomeAutomation":
            await self._process_home_automation(turn_context, recognizer_result.properties["luisResult"])
        elif intent == "QnA":
            await self._process_sample_qna(turn_context)
        elif intent == "PosventaConsultarEvento":
            await self._proceso_de_consulta_evento(turn_context, recognizer_result.properties["luisResult"], conversacion, perfil)
            await self.conversation_state.save_changes(turn_context)
            await self.user_state.save_changes(turn_context)
        elif intent == "DarAltaEvento":
            await self._proceso_de_alta_evento(turn_context, recognizer_result.properties["luisResult"], conversacion, perfil)
            await self.conversation_state.save_changes(turn_context)
            await self.user_state.save_changes(turn_context)
        elif intent == "Encuesta":
            await self._proceso_encuesta(turn_context, recognizer_result.properties["luisResult"], conversacion, perfil)
            await self.conversation_state.save_changes(turn_context)
            await self.user_state.save_changes(turn_context)
        else:
            await turn_context.send_activity(f"Lo siento, no te entiendí, vuelve a intentarlo por favor")


    async def _process_home_automation(self, turn_context: TurnContext, luis_result: LuisResult):
        await turn_context.send_activity(
            f"HomeAutomation top intent {luis_result.top_scoring_intent}."
        )

        intents_list = "\n\n".join(
            [intent_obj.intent for intent_obj in luis_result.intents]
        )
        await turn_context.send_activity(
            f"HomeAutomation intents detected: {intents_list}."
        )

        if luis_result.entities:
            entities_list = "\n\n".join(
                [entity_obj.entity for entity_obj in luis_result.entities]
            )
            await turn_context.send_activity(
                f"HomeAutomation entities were found in the message: {entities_list}."
            )

    async def _proceso_de_consulta_evento( self, turn_context: TurnContext, luis_result: LuisResult, conversacion: Conversacion, perfil: Usuario):
        user_input = turn_context.activity.text.strip()
        if user_input.lower() == 'cancelar':
            await turn_context.send_activity(MessageFactory.text("Okay, lo entiendo, dime en que más te puedo ayudar"))
            conversacion.pregunta_eventoanterior = PreguntaEvento.NONE
            conversacion.BanderaConversacionAbierta = Multiconversacion.NONE        
        else:
            print("ANTERIOR "+str(conversacion.pregunta_eventoanterior))
            conversacion.BanderaConversacionAbierta = Multiconversacion.PosventaConsultarEvento
            if conversacion.pregunta_eventoanterior == PreguntaEvento.NONE:
                if perfil.evento:
                    #DECIRTE QUE YA TENGO EL EVENTO y PREGUNTARTE SI QUIERES CONSULTAR OTRO EVENTO
                    await turn_context.send_activity(MessageFactory.text("Tengo tu evento " + str(perfil.evento) + "\n ¿Quieres consultar este? [Si / No] | Si quiere cancelar escribe [Cancelar]"))
                    conversacion.pregunta_eventoanterior = PreguntaEvento.SINO
                    #Aqui en lugar de poner el texto podems usar las tarjetas
                else:
                    await turn_context.send_activity(MessageFactory.text("¿Cuál es el nombre de tu evento?  | Si quiere cancelar escribe [Cancelar]"))
                    conversacion.pregunta_eventoanterior = PreguntaEvento.EVENTO
            elif conversacion.pregunta_eventoanterior == PreguntaEvento.EVENTO:
                #VALIDAR EVENTO -----
                print("Entramos a la segunta pregunta")
                perfil.evento = user_input
                #CONSULTAR EVENTO EN CASO DE VALIDO
                _query="SELECT * FROM `sepherot_lorenaBD`.`T_Eventos` WHERE Nombre = '"+ perfil.evento +"'"
                print (_query)
                resultado=self._query(_query)
                await turn_context.send_activity(MessageFactory.text("Resultado Query "+str(resultado.valor))) 
                conversacion.pregunta_eventoanterior = PreguntaEvento.NONE
                conversacion.BanderaConversacionAbierta = Multiconversacion.NONE
            elif conversacion.pregunta_eventoanterior == PreguntaEvento.SINO:
                if user_input.lower() == 'si':
                    _query="SELECT * FROM `sepherot_lorenaBD`.`T_Eventos` WHERE Nombre = '"+ perfil.evento +"'"
                    print (_query)
                    resultado=self._query(_query)
                    if resultado.valor != None:
                        await turn_context.send_activity(MessageFactory.text("Resultado Query "+str(resultado.valor)))
                        conversacion.pregunta_eventoanterior = PreguntaEvento.NONE
                        conversacion.BanderaConversacionAbierta = Multiconversacion.NONE
                    else:
                        await turn_context.send_activity(MessageFactory.text("Ese evento no lo tengo registrado, prueba con otro | Si quiere cancelar escribe [Cancelar]"))
                else:
                    await turn_context.send_activity(MessageFactory.text("Okay, dame el nombre del evento que quieres consultar por favor | Si quiere cancelar escribe [Cancelar]"))
                    conversacion.pregunta_eventoanterior = PreguntaEvento.EVENTO
                    #PREGUNTAR POR EL NOMBRE DEL EVENTO PARA IRLO A BUSCAR
                    #MESSAGE FACTORY

    async def _proceso_de_alta_evento( self, turn_context: TurnContext, luis_result: LuisResult, conversacion: Conversacion, perfil: Usuario):
        today = date.today()
        print(today)
        user_input = turn_context.activity.text.strip()
        if user_input.lower() == 'cancelar':
            await turn_context.send_activity(MessageFactory.text("Okay, lo entiendo, dime en que más te puedo ayudar"))
            conversacion.pregunta_alta_anterior = AltaEvento.NONE
            conversacion.BanderaConversacionAbierta = Multiconversacion.NONE        
        else:
            print("Anterior " + str(conversacion.pregunta_alta_anterior))
            conversacion.BanderaConversacionAbierta = Multiconversacion.DarAltaEvento
            if conversacion.pregunta_alta_anterior == AltaEvento.NONE:
                if perfil.alta:
                    await turn_context.send_activity(MessageFactory.text("Ya tienes un proceso activo, ¿quieres seguirlo? [Si/No] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.SINO
                else:
                    await turn_context.send_activity(MessageFactory.text("Perfecto, entonces empecemos con el papeleo ; ¿Cuál es tu nombre? [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.NOMBRE

            elif conversacion.pregunta_alta_anterior == AltaEvento.NOMBRE:
                perfil.nombre = user_input
                await turn_context.send_activity(MessageFactory.text(f"Gracias {perfil.nombre}... ¿Cuál dijiste que era tu apellido paterno? [Puedes escribir Cancelar para salir del proceso]"))
                conversacion.pregunta_alta_anterior = AltaEvento.APELLIDO

            elif conversacion.pregunta_alta_anterior == AltaEvento.APELLIDO:
                perfil.apellido = user_input
                await turn_context.send_activity(MessageFactory.text(f"Perfecto {perfil.nombre} {perfil.apellido} ; Dime ¿qué tipo de evento quieres hacer? [XV años, Boda, Tecnológico, Otro] [Puedes escribir Cancelar para salir del proceso]"))
                conversacion.pregunta_alta_anterior = AltaEvento.TIPOEVENTO

            elif conversacion.pregunta_alta_anterior == AltaEvento.TIPOEVENTO:
                if user_input.lower() == 'xv años':
                    perfil.evento = 4
                    perfil.nombreevento = "XV de " + perfil.nombre
                    await turn_context.send_activity(MessageFactory.text(f"Excelente, dime ¿en qué fecha quieres hacer los {user_input}? [aaaa-mm-dd] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.FECHA
                elif user_input.lower() == 'boda':
                    perfil.evento = 3
                    perfil.nombreevento = "Boda de " + perfil.nombre
                    await turn_context.send_activity(MessageFactory.text(f"Excelente, dime ¿en qué fecha quieres hacer tu {user_input}? [aaaa-mm-dd] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.FECHA
                elif user_input.lower() == 'tecnológico' or user_input.lower() == 'tecnologico':
                    perfil.evento = 5
                    perfil.nombreevento = "Evento Tecnológico de " + perfil.nombre
                    await turn_context.send_activity(MessageFactory.text(f"Excelente, dime ¿en qué fecha quieres hacer tu evento {user_input}? [aaaa-mm-dd] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.FECHA        
                elif user_input.lower() == 'otro':
                    perfil.evento = 6
                    perfil.nombreevento = "Evento de " + perfil.nombre
                    await turn_context.send_activity(MessageFactory.text(f"Excelente, dime ¿en qué fecha quieres hacer tu evento? [aaaa-mm-dd] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.FECHA
                else:
                    await turn_context.send_activity(MessageFactory.text(f"Responde con [Xv años, Boda, Tecnológico, Otro] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.TIPOEVENTO

            elif conversacion.pregunta_alta_anterior == AltaEvento.FECHA:
                if user_input[4] == '-' and user_input[7] == '-':
                    if user_input < str(today):
                        await turn_context.send_activity(MessageFactory.text("A menos que tengas una máquina del tiempo no podemos hacer tu evento en el pasado :D, por favor pon una fecha superior a " + str(today)))
                        conversacion.pregunta_alta_anterior = AltaEvento.FECHA
                    else:
                        perfil.fecha = user_input
                        await turn_context.send_activity(MessageFactory.text("Excelente, para finalizar el proceso necesito un correo para poder enviarte el contrato [Puedes escribir Cancelar para salir del proceso]"))
                        conversacion.pregunta_alta_anterior = AltaEvento.CORREO
                else:
                    await turn_context.send_activity(MessageFactory.text(f"Responde con el formato aaaa-mm-dd, por favor [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_alta_anterior = AltaEvento.FECHA

            elif conversacion.pregunta_alta_anterior == AltaEvento.CORREO:
                perfil.correo = user_input
                await turn_context.send_activity(MessageFactory.text(f"Gracias, te va a llegar un correo a {perfil.correo} con la información necesaria, muchas gracias, ahora... ¿Te puedo ayudar en algo más?"))
                conversacion.pregunta_alta_anterior = AltaEvento.NONE
                conversacion.BanderaConversacionAbierta = Multiconversacion.NONE
                _sql = f"INSERT INTO T_Preventa (Nombre,Apellido,Correo,Fecha,ID_Tipo_Ev,Estatus, Sentimiento ) VALUES ('{perfil.nombre}','{perfil.apellido}','{perfil.correo}', '{perfil.fecha}', '{perfil.evento}', 0 , 'neutral');"
                resultado=self._insert(_sql)
                if resultado.valor == False:
                    await turn_context.send_activity(MessageFactory.text(f"Lo siento, no pude registrar tu reserva, podrias hacerlo de manera manual en el boton de 'Reserva Ya' que esta en la parte superior Muchas gracias. ¿Te puedo ayudar en algo más?"))                
                _sql1 = f"INSERT INTO T_Eventos (ID_Evento, Nombre) VALUES ({perfil.evento},'{perfil.nombreevento}')"
                _evento = self._insert(_sql1)
                print(_evento.valor)
                print(_sql1)

    async def _proceso_encuesta(self, turn_context: TurnContext, luis_result: LuisResult, conversacion: Conversacion, perfil: Usuario):
        user_input = turn_context.activity.text.strip()
        if user_input.lower() == 'cancelar':
            await turn_context.send_activity(MessageFactory.text("Okay, lo entiendo, dime en que más te puedo ayudar"))
            conversacion.pregunta_encuesta_anterior = Encuesta.NONE
            conversacion.BanderaConversacionAbierta = Multiconversacion.NONE
        else:
            conversacion.BanderaConversacionAbierta = Multiconversacion.Encuesta
            if conversacion.pregunta_encuesta_anterior == Encuesta.NONE:
                if perfil.encuesta:
                    await turn_context.send_activity(MessageFactory.text("Ya tienes un proceso activo, ¿quieres seguirlo? [Si/No] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.SINO
                else:
                    await turn_context.send_activity(MessageFactory.text("¿Cuál es el nombre del evento al que asististe? [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.SUEVENTO

            elif conversacion.pregunta_encuesta_anterior == Encuesta.SUEVENTO:
                _sql = f"SELECT * FROM `T_Eventos` WHERE Nombre = '{user_input}'"
                resultado=self._query(_sql)
                if resultado.valor == None:
                    await turn_context.send_activity(MessageFactory.text("No tengo registrado ese evento, puedes intentar otra vez o escribe cancelar"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.SUEVENTO
                else:    
                    perfil.idevent = resultado.valor[0]
                    perfil.idevento = resultado.valor[1]
                    await turn_context.send_activity(MessageFactory.text("Perfecto, dime ¿El evento fue lo que esperabas? [Si No] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA1

            elif conversacion.pregunta_encuesta_anterior == Encuesta.PREGUNTA1:
                if user_input.lower() == 'si':
                    perfil.calificacion = 1
                    perfil.pregunta1 = user_input
                    await turn_context.send_activity(MessageFactory.text("Me alegra mucho que haya sido lo que esperabas, necesito que califiques el evento por favor [Malo Regular Bueno Excelente] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA2
                elif user_input.lower() == 'no':
                    perfil.pregunta1 = user_input
                    await turn_context.send_activity(MessageFactory.text("Lamento que no haya sido lo que esperabas, ¿Cómo calificarías el evento? [Malo Regular Bueno Excelente] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA2
                else:
                    await turn_context.send_activity(MessageFactory.text("Contéstame con un Si o un No por favor [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA1

            elif conversacion.pregunta_encuesta_anterior == Encuesta.PREGUNTA2:
                if user_input.lower() == 'malo' or user_input.lower() == 'regular':
                    perfil.pregunta2 = user_input
                    await turn_context.send_activity(MessageFactory.text("Trataremos de mejorar, dime ¿Asistirías de nuevo a uno de nuestros eventos? [Si No] [Puedes escribir Cancelar para salir del proceso]"))
                    if user_input.lower() == 'malo':
                        perfil.calificacion += .25
                    else:
                        perfil.calificacion += .50
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA3
                elif user_input.lower() == 'bueno' or user_input.lower() == 'excelente':
                    perfil.pregunta2 = user_input
                    await turn_context.send_activity(MessageFactory.text("¡Wow! ¡Muchas gracias!, dime ¿Asistirías de nuevo a uno de nuestros eventos? [Si No] [Puedes escribir Cancelar para salir del proceso]"))
                    if user_input.lower() == 'bueno':
                        perfil.calificacion += .75
                    else:
                        perfil.calificacion += 1
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA3
                else:
                    await turn_context.send_activity(MessageFactory.text("Contesta con [Malo, Regular, Bueno, Excelente] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA2

            elif conversacion.pregunta_encuesta_anterior == Encuesta.PREGUNTA3:
                if user_input.lower() == 'si':
                    perfil.calificacion += 1
                    perfil.pregunta3 = user_input
                    await turn_context.send_activity(MessageFactory.text("Siempre te esperaremos en nuevos eventos, ya casi vamos a terminar, dime ¿Nos recomendarías con amigos y/o familiares? [Si No] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA4
                elif user_input.lower() == 'no':
                    perfil.pregunta3 = user_input
                    await turn_context.send_activity(MessageFactory.text("Ya casi vamos a terminar, dime ¿Nos recomendarías con amigos y/o familiares? [Si No] [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA4
                else:
                    await turn_context.send_activity(MessageFactory.text("Contéstame con un Si o un No por favor [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA3

            elif conversacion.pregunta_encuesta_anterior == Encuesta.PREGUNTA4:
                if user_input.lower() == 'si':
                    perfil.calificacion += 1
                    perfil.pregunta4 = user_input
                    await turn_context.send_activity(MessageFactory.text("Muchas gracias, ya casi vamos a acabar dejame un comentario de lo que te gustó del evento [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA5
                elif user_input.lower() == 'no':
                    perfil.pregunta4 = user_input
                    await turn_context.send_activity(MessageFactory.text("Okay, ya casi vamos a acabar... dejame un comentario de porque no nos recomendarias,  haremos cambios en base a tus comentarios, Muchas gracias [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA5
                else:
                    await turn_context.send_activity(MessageFactory.text("Contéstame con un Si o un No por favor [Puedes escribir Cancelar para salir del proceso]"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.PREGUNTA4

            elif conversacion.pregunta_encuesta_anterior == Encuesta.PREGUNTA5:
                perfil.pregunta5 = user_input
                await turn_context.send_activity(MessageFactory.text("En verdad muchas gracias por tu sinceridad, por último me puedes dar tu correo para poder consentirte con descuentos [Puedes escribir Cancelar para salir del proceso]"))
                conversacion.pregunta_encuesta_anterior = Encuesta.CORREO

            elif conversacion.pregunta_encuesta_anterior == Encuesta.CORREO:
                perfil.correoencuesta = user_input
                if int(perfil.calificacion) > 2.5:
                    await turn_context.send_activity(MessageFactory.text("Gracias, ¿Te puedo ayudar en algo más?"))
                    conversacion.pregunta_encuesta_anterior = Encuesta.NONE
                    conversacion.BanderaConversacionAbierta = Multiconversacion.NONE
                    _insert = f"INSERT INTO Encuesta (ID_Evento, ID_Sexo, ID_Event, Correo, P1, P2, P3, P4, P5, Estatus, Calificación, Sentimiento, Valor_Sent) VALUES ('{perfil.idevento}', '3', '{perfil.idevent}', '{perfil.correoencuesta}', '{perfil.pregunta1}', '{perfil.pregunta2}', '{perfil.pregunta3}', '{perfil.pregunta4}', '{perfil.pregunta5}', '0', '{perfil.calificacion}', 'neutral', '0.82');"
                    print(_insert)
                    resultado=self._insert(_insert)
                    print(resultado.valor)
                else:
                    await turn_context.send_activity(MessageFactory.text("Sentimos que el evento no haya sido de tu agrado, tomaremos tus respuetas como retroalimentación para mejorar, muchas gracias, ¿Te puedo ayudar en algo más?"))
                    _insert = f"INSERT INTO Encuesta (ID_Evento, ID_Sexo, ID_Event, Correo, P1, P2, P3, P4, P5, Estatus, Calificación, Sentimiento, Valor_Sent) VALUES ('{perfil.idevento}', '3', '{perfil.idevent}', '{perfil.correoencuesta}', '{perfil.pregunta1}', '{perfil.pregunta2}', '{perfil.pregunta3}', '{perfil.pregunta4}', '{perfil.pregunta5}', '0', '{perfil.calificacion}', 'neutral', '0.82');"
                    print(_insert)
                    conversacion.pregunta_encuesta_anterior = Encuesta.NONE
                    conversacion.BanderaConversacionAbierta = Multiconversacion.NONE


    async def _process_sample_qna(self, turn_context: TurnContext):
        response = await self.qna_maker.get_answers(turn_context)
        if response and len(response)>0:
            await turn_context.send_activity(MessageFactory.text(response[0].answer))
        else:
            await turn_context.send_activity("Lo siento, no te entiendí, intenta otra cosa por favor")
            # perfil = await self.perfil.get(turn_context, Usuario)
            # conversacion = await self.conversacion.get(turn_context, Conversacion)

            # await self._llenado_de_perfil(conversacion, perfil, turn_context)

            # await self.conversation_state.save_changes(turn_context)
            # await self.user_state.save_changes(turn_context)

    async def _llenado_de_perfil(self, conversacion: Conversacion, perfil: Usuario,  turn_context: TurnContext):
        user_input = turn_context.activity.text.strip()
        print("ANTERIOR "+str(conversacion.pregunta_anterior))
        if conversacion.pregunta_anterior == Pregunta.NONE:
            await turn_context.send_activity(MessageFactory.text("Bienvenido, ¿Cuál es tu nombre?"))
            conversacion.pregunta_anterior = Pregunta.NOMBRE
        elif conversacion.pregunta_anterior == Pregunta.NOMBRE:
            if user_input:
                perfil.nombre = user_input
                conversacion.pregunta_anterior = Pregunta.EDAD
                await turn_context.send_activity(MessageFactory.text(f"Hola {perfil.nombre}"))
                await turn_context.send_activity(MessageFactory.text("¿Cuantos años tienes?"))                
            else:
                await turn_context.send_activity(MessageFactory.text("Amigo dame tu nombre!"))
        elif conversacion.pregunta_anterior == Pregunta.EDAD:
            resultado = self._validar_edad(user_input)
            if resultado.aceptado:
                perfil.edad=resultado.valor
                await turn_context.send_activity(MessageFactory.text("¿Tu fecha de nacimiento?"))
                conversacion.pregunta_anterior = Pregunta.FECHA
            else:
                await turn_context.send_activity(MessageFactory.text(resultado.mensaje))
        elif conversacion.pregunta_anterior == Pregunta.FECHA:
            await turn_context.send_activity(MessageFactory.text(f"Tu nombre es: {perfil.nombre}"))
            await turn_context.send_activity(MessageFactory.text(f"Tu edad es: {perfil.edad}"))
            conversacion.pregunta_anterior = Pregunta.NONE
    
    def _validar_edad(self, user_input: str) -> ValidacionEspecial:
        valores = recognize_number(user_input, Culture.Spanish)
        bandera = True
        mensaje = None
        edad = 0
        for valor in valores:
            if "value" in valor.resolution:
                edad = int(valor.resolution["value"])
                if edad < 18:
                    bandera=False
                    mensaje="Tas chiquito, solo mayores de 18 años"
                    edad = None
        print(edad)
        return ValidacionEspecial(bandera,edad,mensaje)


    def _query(self, consulta) -> ValidacionEspecial:
        bandera = True
        mensaje = None
        resultado = 0
        conn = mysql.connect(host='sepheroth.com',user='sepherot_lorena', password='9LwPFmj9QS',database='sepherot_lorenaBD')
        cursor = conn.cursor()
        cursor.execute(consulta)
        resultado=cursor.fetchone()
        print(resultado)
        return ValidacionEspecial(bandera,resultado,mensaje)
    
    def _insert(self,consulta) -> ValidacionEspecial:
        try:
            bandera = True
            mensaje = None
            conn = mysql.connect(host='sepheroth.com',user='sepherot_lorena', password='9LwPFmj9QS',database='sepherot_lorenaBD')
            cursor = conn.cursor()
            cursor.execute(consulta)
            conn.commit()
            resultado = True
            return ValidacionEspecial(bandera,resultado,mensaje)
        except:
            bandera = True
            mensaje = None
            resultado = False
            return ValidacionEspecial(bandera,resultado,mensaje)