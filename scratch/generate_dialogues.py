import json
import os

def main():
    dialogues = {
        "game_title": "Easy Date V2: Simulador de Juego de Texto",
        "mechanics_config": {
            "starting_investment": 50,
            "max_investment": 100,
            "min_investment": 0,
            "penalty_needy_time": -10,
            "bonus_calibrated_emoji": 5
        },
        "levels": [
            {
                "level_id": 1,
                "girl_name": "Natalia",
                "name": "Nivel 1: El Match en Tinder",
                "description": "Hiciste match con Natalia en Tinder. Mándale un mensaje para iniciar la conversación, captar su atención y demostrar que no estás desesperado.",
                "steps": [
                    {
                        "step_id": 1,
                        "her_message": "Jajaja, acepto la apuesta. A ver, ¿por qué lo dices? 😜",
                        "her_time": "20 min",
                        "state": "curiosa",
                        "options": [
                            {
                                "text": "Te apuesto tres preguntas y un helado a que tu perfil es más interesante de lo que parece 😏",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "¡Perfecto! Un abrador desafiante y juguetón. Esperar 15 minutos demuestra que tienes una vida interesante y no estás pegado a la pantalla.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Hola hermosa! ¿Cómo estás hoy? 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "¡Te viste súper intenso! Le soltaste todos los halagos de golpe por un simple match. Te vio urgido y su interés se fue al suelo.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Hola",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Demasiado simple. Eres uno más del montón que solo dice 'hola'. Qué aburrido, así la conversación va a morir de inmediato.",
                                "investment_impact": -5
                            },
                            {
                                "text": "Qué guapa eres en tu primera foto, ¿qué buscas por aquí?",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Suenas como entrevistador de recursos humanos y encima le regalaste un cumplido de entrada. Perdiste todo el misterio de inmediato.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 2,
                        "her_message": "Jajaja, un 7. Y no soy tan seria, ya lo verás. Oye, me caes bien, pásame tu WhatsApp y seguimos hablando por ahí 😅",
                        "her_time": "10 min",
                        "state": "receptiva",
                        "options": [
                            {
                                "text": "Es que te ves muy seria en tus fotos, pero presiento que tienes tu lado divertido. ¿Cómo va tu día de 1 a 10? 😏",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "¡Excelente! Usas muy bien el 'estira y afloja' al decirle que se ve seria pero divertida, manteniendo el juego activo. Calibraste perfecto el tiempo de respuesta.",
                                "investment_impact": 20
                            },
                            {
                                "text": "No te preocupes hermosa, yo te enseño a divertirte 😘",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Te pasaste de lanzado y creído de forma barata. Ella se va a espantar por ese exceso de confianza.",
                                "investment_impact": -25
                            },
                            {
                                "text": "jaja sí, a veces es difícil de explicar",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Una respuesta súper tibia y floja. No le aportas nada a la charla y dejas que muera el interés.",
                                "investment_impact": -10
                            },
                            {
                                "text": "¿Y a qué te dedicas?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Mataste toda la vibra juguetona de golpe para hacerle la típica pregunta de entrevista. Qué aburrido.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 3,
                        "her_message": "Ya te agregué a WhatsApp. ¿Quién eres? Para guardarte con tu nombre jaja.",
                        "her_time": "15 min",
                        "state": "interesada",
                        "options": [
                            {
                                "text": "Soy el chico del helado y de las tres preguntas. Guárdame como tu futuro heladero preferido 😉",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "¡Excelente! Retomas el chiste interno (helado) y creas un rol divertido de inmediato.",
                                "investment_impact": 15
                            },
                            {
                                "text": "Soy Carlos. Qué bueno que me agregas al fin, ya quería hablar contigo por acá.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Demasiado seco y revelaste excesivo interés. Demuestra calma.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Adivina quién soy... a ver si te acuerdas.",
                                "is_correct": False,
                                "required_time": "45 min",
                                "coach_feedback": "El cliché de 'adivina quién soy' aburre y suena infantil. No lo uses.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Hola, soy yo Carlos el de Tinder.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Muy plano y formal. Pierdes la tensión juguetona que traías desde Tinder.",
                                "investment_impact": -5
                            }
                        ]
                    },
                    {
                        "step_id": 4,
                        "her_message": "Jajaja ya te guardé así. ¿Qué haces? Yo aquí aburrida en mi cama viendo pelis.",
                        "her_time": "5 min",
                        "state": "relajada",
                        "options": [
                            {
                                "text": "Yo acabo de terminar unos pendientes y ahora voy a leer un poco. ¿Qué película estás viendo para ver si te la apruebo? 😜",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "¡Perfecto! Demuestras que estabas ocupado, no respondes de inmediato a su 'aburrimiento' y desafías su elección de película.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Qué coincidencia! Yo también estoy en mi cama sin hacer nada. ¿Quieres que hablemos por llamada?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "¡Súper intenso! Proponer llamada de inmediato cuando ella solo dijo estar aburrida es demasiado apresurado.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Nada, también aburrido jaja.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Dos personas aburridas no hacen una buena conversación. Debes liderar con algo de valor o actividad.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Ah qué chido.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Cortante sin sentido. Tardar una hora para decir 'ah qué chido' matará la conversación.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 5,
                        "her_message": "Estoy viendo una de terror. Oye, vi tus fotos de Tinder de nuevo, te ves muy fiestero, seguro le hablas a mil niñas jaja 🙄",
                        "her_time": "10 min",
                        "state": "provocadora",
                        "options": [
                            {
                                "text": "Jaja me gusta pasarla bien con mis amigos. Pero veo que me andas investigando a fondo... ¿ya te estoy gustando o es solo curiosidad? 😏",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "¡Brillante! Superas el shit test (fiestero/mil niñas) sin ponerte a la defensiva y le devuelves la acusación coqueteando.",
                                "investment_impact": 20
                            },
                            {
                                "text": "No, te lo juro que casi no salgo y no le hablo a nadie más. Eres la única con la que hablo, de verdad.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Explicación rogona y defensiva. Le entregaste todo el control y te ves sumamente necesitado de su aprobación.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Jaja sí, tengo muchas amigas, pero ninguna es como tú 😘",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Un cumplido barato y trillado que suena falso y manipulador. Bajas tu valor.",
                                "investment_impact": -15
                            },
                            {
                                "text": "¿Y a ti te gusta salir de fiesta o eres más tranquila?",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Ignoraste su provocación para hacer una pregunta genérica. Perdiste la tensión.",
                                "investment_impact": -10
                            }
                        ]
                    },
                    {
                        "step_id": 6,
                        "her_message": "Jajaja qué creído eres. Curiosidad no más. Bueno, y dime, ¿qué es lo que más te llama la atención de una mujer? A ver si paso tu filtro.",
                        "her_time": "12 min",
                        "state": "interesada",
                        "options": [
                            {
                                "text": "Me gusta que sea divertida, que tenga metas propias y que no se asuste con mis chistes malos jaja. ¿Cumples con los requisitos? 😜",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "Muy bien. Calificas tus estándares (metas, divertida) y la pones a ella a prueba de manera juguetona.",
                                "investment_impact": 15
                            },
                            {
                                "text": "Que sea hermosa e inteligente como tú, con eso me basta y me sobra 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Nuevamente cayendo en el halago fácil y regalado. Ella no ha hecho nada para ganarse ese cumplido.",
                                "investment_impact": -20
                            },
                            {
                                "text": "No sé, que sea buena persona.",
                                "is_correct": False,
                                "required_time": "45 min",
                                "coach_feedback": "Respuesta insípida y sin personalidad. Demuestra que no tienes estándares reales.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Cualquiera que me haga caso jaja.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Broma auto-despreciativa fatal. Te proyecta como alguien sin opciones y con autoestima baja.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 7,
                        "her_message": "Jajaja obvio que cumplo con eso y más. Oye, la verdad es que he tenido una semana súper pesada con exámenes de la universidad y proyectos 😫.",
                        "her_time": "25 min",
                        "state": "cansada",
                        "options": [
                            {
                                "text": "Te entiendo, los proyectos te drenan la energía. Suena a que te ganaste un premio para relajarte un rato. ¿Qué tal un helado el sábado? 🍦",
                                "is_correct": True,
                                "required_time": "45 min",
                                "coach_feedback": "¡Perfecto! Validas su cansancio de forma madura y enganchas de inmediato la propuesta de cita como un 'premio/recompensa'.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¡Ay pobrecita! Si quieres voy a tu casa y te hago tus tareas para que descanses mi reina 🥺",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Comportamiento 'simpatizante' extremo. Te estás ofreciendo como asistente gratis, perdiendo toda masculinidad y atractivo.",
                                "investment_impact": -25
                            },
                            {
                                "text": "Qué mal. Échale ganas, ya saldrás de eso.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Demasiado frío y desinteresado. Parece que no te importa en absoluto lo que te está contando.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Bueno, cuando termines me avisas y salimos.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Cortante y pasivo. Le tiras la pelota de la iniciativa a ella en lugar de liderar.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 8,
                        "her_message": "Ay sí, un helado me vendría increíble la verdad. Me urge distraerme un ratito.",
                        "her_time": "8 min",
                        "state": "entusiasmada",
                        "options": [
                            {
                                "text": "Perfecto, conozco un lugar genial con terraza cerca de tu zona. El sábado a las 5:00 pm te queda bien, ¿o prefieres más tarde? 😏",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "Excelente liderazgo. Defines el plan, el lugar y das dos opciones de hora para facilitar el cierre sin verte indeciso.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Súper! Dime tú a dónde quieres ir, a qué hora y yo paso por ti cuando tú me indiques.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Cero liderazgo. Le pides a ella que planee toda la cita. Las mujeres prefieren hombres resolutivos y que lideren el plan.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Bueno, ahí vemos a dónde vamos entonces.",
                                "is_correct": False,
                                "required_time": "45 min",
                                "coach_feedback": "Indeciso y vago. Transmite falta de entusiasmo o poca preparación.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Va, pero tú invitas esta vez jajaja.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Broma tacaña inapropiada en la fase de seducción inicial. Puede matar la atracción de golpe.",
                                "investment_impact": -20
                            }
                        ]
                    },
                    {
                        "step_id": 9,
                        "her_message": "El sábado a las 5:00 pm me queda perfecto. ¿Cómo nos vemos allá o nos encontramos en algún punto?",
                        "her_time": "15 min",
                        "state": "cooperativa",
                        "options": [
                            {
                                "text": "Te veo directo en la entrada del lugar a las 5:00. Así el que llegue tarde paga el primer helado, ¿trato hecho? 🍦😜",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "Perfecto. Cierras la logística con un pequeño reto divertido que mantiene la conversación lúdica.",
                                "investment_impact": 15
                            },
                            {
                                "text": "Pásame tu dirección exacta de una vez y yo paso por ti en mi auto a las 4:30 pm sin falta hermosa 😘",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Muy apresurado para ir a recogerla a su casa en la primera cita, especialmente en Tinder donde aún no se conocen en persona.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Como quieras, me da igual la verdad.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Suena desinteresado y apático. Muestra que no te importa si se ven o no.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Mejor encuéntrame tú en el metro más cercano a mi casa.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Poco caballero y perezoso. Estás pidiéndole que haga todo el esfuerzo logístico a ella.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 10,
                        "her_message": "¡Jajaja trato hecho! Ya tienes la de perder porque soy súper puntual. Nos vemos el sábado. ¡Cuídate mucho! 😊",
                        "her_time": "10 min",
                        "state": "emocionada",
                        "options": [
                            {
                                "text": "Ya lo veremos. ¡Cuídate y que termines pronto tus proyectos! Hablamos el viernes para confirmar. 😎",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "Excelente cierre de conversación. Dejas el gancho para confirmar, no sigues chateando indefinidamente y demuestras que respetas su tiempo de estudio.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¡Perfecto hermosa! Oye, y cuéntame, ¿qué vas a hacer mañana? ¿Seguimos platicando por aquí?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Error común: seguir chateando sin parar después de haber concretado la cita. Pierdes el misterio y te ves desocupado.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Ok.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Cierre demasiado seco y robótico. Pierde la calidez final.",
                                "investment_impact": -10
                            },
                            {
                                "text": "No te vayas, cuéntame algo más, todavía no tengo sueño 🥺",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Comportamiento 'needy' clásico. Estás rogando atención, rompiendo toda la calibración lograda.",
                                "investment_impact": -25
                            }
                        ]
                    }
                ]
            },
            {
                "level_id": 2,
                "girl_name": "Sofía",
                "name": "Nivel 2: Pasando a WhatsApp",
                "description": "Conseguiste el WhatsApp de Sofía, pero ahora debes mantener la atracción y agendar la cita sin verte desesperado. Sofía es más ocupada e inteligente.",
                "steps": [
                    {
                        "step_id": 1,
                        "her_message": "¡Hola! Jajaja sí, ya por fin por aquí 👻. Oye, por cierto, esta semana ando súper ocupada en el trabajo, tal vez la otra semana podamos vernos.",
                        "her_time": "4 horas",
                        "state": "ocupada",
                        "options": [
                            {
                                "text": "No hay problema, de hecho yo también ando a mil con unos proyectos. Hablamos luego, ¡cuídate! 😎",
                                "is_correct": True,
                                "required_time": "4 horas",
                                "coach_feedback": "¡Brillante desapego! Al no rogarle ni molestarte, demuestras que tienes una vida interesante y que no te urge verla. Le quitas toda la presión.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¿Por qué tan ocupada? 🥺 yo sí quería verte",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Te viste muy necesitado. Ella te acaba de poner una barrera laboral y tú le respondes de forma infantil y dependiente.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Bueno, dime qué día puedes y me acomodo a tu horario",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Someterte al 100% a su agenda te hace ver como alguien que no valora su propio tiempo. Calibra mejor.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Si no quieres salir dímelo directo y ya, no me hagas perder el tiempo",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Reacción inmadura y resentida. Demuestras baja tolerancia al rechazo y falta de control emocional.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 2,
                        "her_message": "¡Hola! Perdón por desaparecer, estuve a mil. ¿Qué tal estuvo tu semana? 😊",
                        "her_time": "3 días",
                        "state": "desaparecida",
                        "options": [
                            {
                                "text": "Hola Sofía. Estuvo movida pero excelente. Qué bueno que sobreviviste a tu semana laboral jaja. ¿Cómo va todo? 😏",
                                "is_correct": True,
                                "required_time": "4 horas",
                                "coach_feedback": "¡Perfecto! No le reclamas por tardar 3 días en contestar (demuestras alto valor y control emocional) y respondes con buena vibra.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¡Al fin apareces! Creí que te habías muerto o que ya te habías olvidado de mí 🙄",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Hacer reclamos de forma pasivo-agresiva a una chica que apenas estás conociendo es el repelente de atracción definitivo.",
                                "investment_impact": -25
                            },
                            {
                                "text": "Estuvo bien. ¿Y la tuya?",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Demasiado seco y cortante. Parece que estás molesto por su tardanza, transmitiendo frustración implícita.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Hola hermosa, te extrañé mucho estos días, qué bueno que me escribes al fin 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Exceso de sentimentalismo. Decirle que la extrañaste cuando desapareció 3 días te posiciona como su opción de respaldo disponible.",
                                "investment_impact": -20
                            }
                        ]
                    },
                    {
                        "step_id": 3,
                        "her_message": "Jaja sí, sobreviví de milagro. Oye, ¿qué plan tienes para este fin de semana? A ver si ahora sí coincidimos.",
                        "her_time": "1 hora",
                        "state": "receptiva",
                        "options": [
                            {
                                "text": "Tengo ganas de tomar unos cocteles en un bar nuevo con terraza. ¿Te apuntas a acompañarme el viernes por la noche? 🍸",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "Lideras el plan de forma atractiva, sugiriendo un lugar interesante (cocteles/terraza) y fijando un día específico.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Lo que tú quieras hacer! Estoy libre todo el fin de semana para ti, dime a dónde vamos y yo te sigo.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Cero misterio y disponibilidad total. Transmites que no tienes vida social propia fuera de esperar su llamada.",
                                "investment_impact": -20
                            },
                            {
                                "text": "No sé, no tengo planes. ¿Tú qué quieres hacer?",
                                "is_correct": False,
                                "required_time": "45 min",
                                "coach_feedback": "Aburrido e indeciso. Le devuelves el trabajo de planificar la cita a ella.",
                                "investment_impact": -10
                            },
                            {
                                "text": "El sábado tengo una fiesta súper top con unas amigas, si quieres puedes venir.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Invitarla a un plan grupal en la primera cita diluye la tensión sexual y romántica cara a cara. Es mejor algo individual.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 4,
                        "her_message": "Mmm el viernes se me complica un poco porque tengo cena familiar. ¿Podría ser el sábado?",
                        "her_time": "30 min",
                        "state": "negociando",
                        "options": [
                            {
                                "text": "El sábado me queda bien temprano o a partir de las 9:00 pm. Hagámoslo el sábado a las 9:00 pm entonces. ¿Trato hecho? 😏",
                                "is_correct": True,
                                "required_time": "45 min",
                                "coach_feedback": "Excelente calibración. Aceptas su propuesta pero pones límites en tus horarios, concretando la cita con liderazgo.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Sí! El sábado a la hora que tú quieras, cancelo cualquier cosa que tenga para estar contigo hermosa.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Decir que vas a cancelar tus planes por ella demuestra un nivel de desesperación tremendo. La espantarás.",
                                "investment_impact": -25
                            },
                            {
                                "text": "No, si no puedes el viernes mejor lo dejamos para después. Qué flojera.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Demasiado rígido e intolerante. Ella te propuso una alternativa lógica (sábado), no hay razón para molestarse.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Bueno, el sábado entonces. Avísame a qué hora te queda bien.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Cedes el control de la hora. Es mejor proponer tú la hora en base a tu disponibilidad.",
                                "investment_impact": -10
                            }
                        ]
                    },
                    {
                        "step_id": 5,
                        "her_message": "¡Va! Sábado a las 9:00 pm me parece súper bien. Oye, ¿y a dónde me vas a llevar? Sorpréndeme jaja 😉",
                        "her_time": "15 min",
                        "state": "retadora",
                        "options": [
                            {
                                "text": "Es un bar secreto con una vista espectacular de la ciudad, te va a encantar. Solo asegúrate de llevar buena actitud, del resto me encargo yo 😜",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "Excelente. Creas misterio al no revelar el lugar exacto y le pones un reto divertido ('llevar buena actitud') para calificarla.",
                                "investment_impact": 20
                            },
                            {
                                "text": "Te voy a llevar al restaurante más caro de comida italiana de la zona, quiero consentirte al máximo.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Gastar demasiado dinero e intentar 'comprar' su interés en la primera cita transmite baja autoestima y desesperación.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Pues al bar de la esquina de mi casa, está barato jaja.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Falta total de esfuerzo y romance. Se lee tacaño y poco emocionante.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Dime qué tipo de comida te gusta y yo busco opciones en Google Maps.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Pierdes todo el factor sorpresa y demuestras que no tenías nada planeado de antemano.",
                                "investment_impact": -10
                            }
                        ]
                    },
                    {
                        "step_id": 6,
                        "her_message": "Jajaja ya me dio curiosidad. Trato hecho, llevaré mi mejor actitud. ¿Nos vemos allá?",
                        "her_time": "10 min",
                        "state": "cooperativa",
                        "options": [
                            {
                                "text": "Sí, te paso la ubicación el mismo sábado por la tarde para mantener el misterio. ¡Que tengas buena semana! 😎",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "¡Perfecto! Dejas la logística clara, prolongas el misterio y cierras tú la interacción de forma asertiva.",
                                "investment_impact": 15
                            },
                            {
                                "text": "Pásame tu dirección exacta de una vez y yo paso a buscarte a las 8:30 pm hermosa 😘",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Nuevamente presionando para ir a su casa en la primera cita. Respeta su espacio y privacidad inicial.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Ok, ahí nos vemos.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Cierre plano y sin emoción. Podrías haber mantenido un toque más coqueto.",
                                "investment_impact": -5
                            },
                            {
                                "text": "Oye, ¿y qué vas a hacer hoy en la noche? Sigamos platicando jaja.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Error de seguimiento: intentar alargar el chat tras cerrar la cita destruye la anticipación de la misma.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 7,
                        "her_message": "Hola, ya es sábado. ¿Sigue en pie lo de hoy? Cuéntame cuál es el bar misterioso jaja.",
                        "her_time": "10:00 AM",
                        "state": "curiosa",
                        "options": [
                            {
                                "text": "Hola Sofía. Claro que sí, todo listo. Te paso la ubicación: [Dirección]. Llega puntual para ganarte la sorpresa 😉. Nos vemos a las 9.",
                                "is_correct": True,
                                "required_time": "1 hora",
                                "coach_feedback": "Perfecto. Confirmas con calma a media tarde, revelas el lugar y mantienes el juego de la puntualidad.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Hola hermosa! ¡Sí, obvio! Llevo esperando todo el día que fuera sábado para verte, ya estoy súper listo 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Exceso de entusiasmo y vulnerabilidad. Transmite que tu vida gira alrededor de esta cita.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Hola. Sí, sigue en pie. El lugar es [Dirección]. Nos vemos allá.",
                                "is_correct": False,
                                "required_time": "2 horas",
                                "coach_feedback": "Demasiado formal e informativo. Pierdes la sazón juguetona que habías construido.",
                                "investment_impact": -5
                            },
                            {
                                "text": "Oye, me surgió un contratiempo, ¿podríamos cambiarlo para el próximo fin?",
                                "is_correct": False,
                                "required_time": "3 horas",
                                "coach_feedback": "Cancelar de tu lado en el último momento sin una emergencia real destruye la confianza y el interés.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 8,
                        "her_message": "Jaja anotado, ahí estaré puntual. ¿Qué tipo de código de vestimenta es? ¿Formal o casual?",
                        "her_time": "2 horas",
                        "state": "cooperativa",
                        "options": [
                            {
                                "text": "Casual pero con estilo, como para impresionar a un chico genial del helado jaja. Nos vemos en un rato. 😎",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "¡Genial! Calibras el estilo de vestir y usas un chiste coqueto para elevar la anticipación de la cita.",
                                "investment_impact": 20
                            },
                            {
                                "text": "Vente súper elegante, quiero presumirte con todo el mundo en el bar.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Presión innecesaria y se lee un poco superficial e inseguro.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Como quieras, da igual.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Cortante y poco empático. Ella solo quería saber cómo ir vestida para no desentonar.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Lleva ropa cómoda por si decidimos caminar mucho tarde en la noche.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Proyectar que van a caminar tarde en la noche antes de la cita genera desconfianza respecto a tu seguridad.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 9,
                        "her_message": "Jajaja va, me vestiré para impresionar entonces. Ya voy saliendo en camino.",
                        "her_time": "8:30 PM",
                        "state": "en_camino",
                        "options": [
                            {
                                "text": "Perfecto, yo también voy en camino. Con cuidado al manejar/transporte, nos vemos allá. 🚗",
                                "is_correct": True,
                                "required_time": "inmediato",
                                "coach_feedback": "Muy bien. Confirmación logística rápida, segura y caballerosa.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Qué emoción! Ya estoy en el bar esperándote desde hace media hora, corre por favor 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Llegar media hora antes y rogarle que corra te hace ver extremadamente ansioso. Muestra calma.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Ok.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Cierre demasiado escueto para alguien que ya va en camino a verte.",
                                "investment_impact": -5
                            },
                            {
                                "text": "Oye, ¿si vas a venir sola o vas con alguien más?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Pregunta de inseguridad fatal. Muestra celos o dudas paranoicas antes de la cita.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 10,
                        "her_message": "Ya llegué, estoy afuera de la entrada del bar. ¿Dónde estás?",
                        "her_time": "9:02 PM",
                        "state": "llegó",
                        "options": [
                            {
                                "text": "Justo voy cruzando la calle, te veo en la entrada en un minuto. Busca al chico del helado 😏",
                                "is_correct": True,
                                "required_time": "inmediato",
                                "coach_feedback": "Excelente coordinación. Cierras el chat para pasar a la interacción real en persona de forma calibrada y carismática.",
                                "investment_impact": 20
                            },
                            {
                                "text": "Ay perdón hermosa, me retrasé 20 minutos por el tráfico, espérame por favor 🥺",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Llegar tarde en la primera cita y dar excusas te resta puntos de madurez y seriedad. Planifica mejor.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Pasa y pide una mesa a mi nombre, yo tardo un rato.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Poco caballeroso. Dejarla sola en la entrada de un bar en la primera cita da una pésima impresión inicial.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Busca una mesa y espérame, estoy terminando una llamada importante.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Proyectas que la cita no es tu prioridad, mostrando arrogancia mal calibrada.",
                                "investment_impact": -15
                            }
                        ]
                    }
                ]
            },
            {
                "level_id": 3,
                "girl_name": "Camila",
                "name": "Nivel 3: El Post-Cita",
                "description": "Tuviste una cita espectacular con Camila. Ahora debes calibrar el seguimiento al día siguiente para mantener el interés sin sonar needy. Camila es una chica muy bonita y selectiva.",
                "steps": [
                    {
                        "step_id": 1,
                        "her_message": "La pasé súper bien ayer contigo, gracias por la cena y la plática. Ya voy a dormir, buenas noches 😊",
                        "her_time": "12:00 AM (noche)",
                        "state": "agradecida",
                        "options": [
                            {
                                "text": "Ayer la pasé excelente. Espero que tu garganta esté mejor hoy, no te vayas a enfermar por mi culpa 😂",
                                "is_correct": True,
                                "required_time": "4 horas",
                                "coach_feedback": "¡Excelente! Te ves empático, usas un chiste interno de la cita y no te muestras desesperado por escribirle temprano al día siguiente.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¡Hola Camila! ¿Cómo amaneciste? La pasé increíble ayer, ya te extraño ❤️",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Decirle 'ya te extraño' a la mañana siguiente de la primera cita te hace ver extremadamente dependiente emocionalmente.",
                                "investment_impact": -25
                            },
                            {
                                "text": "Oye, ¿por qué tan perdida hoy?",
                                "is_correct": False,
                                "required_time": "4 horas",
                                "coach_feedback": "Exigir atención de manera tosca cuando apenas te despertaste transmite posesividad descalibrada.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Hola, ¿cómo estás?",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Muy plano. Después de una cita emocionante, un simple 'cómo estás' apaga la vibra del juego.",
                                "investment_impact": -10
                            }
                        ]
                    },
                    {
                        "step_id": 2,
                        "her_message": "Jaja no te preocupes, mi garganta está bien, solo fue por el frío de la terraza. Qué lindo que te acuerdes.",
                        "her_time": "15 min",
                        "state": "receptiva",
                        "options": [
                            {
                                "text": "Qué mal, tómate algo calientito y descansa. Ya recargaremos energías después.",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "¡Perfecto! Te muestras empático pero respetas su espacio. No te regalas y tu tiempo de respuesta es el ideal (espejeaste su tiempo).",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Oh no! ¿Quieres que vaya a cuidarte? Te llevo sopa a tu casa 🥺",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Extrema necesidad. Ofrecerte a ir a su casa a cuidarla por un simple resfriado post-cita es demasiado invasivo.",
                                "investment_impact": -25
                            },
                            {
                                "text": "Yo también la pasé genial. Eres increíble, la verdad me encantaste muchísimo.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Exceso de confesión emocional. Declarar que te encantó muchísimo de golpe mata el reto de conquistarte.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Uy, seguro te cansé mucho ayer 😂",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Chiste de doble sentido mal calibrado o arrogancia inoportuna. Puede leerse un poco tosco.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 3,
                        "her_message": "Ay, gracias, qué lindo eres la verdad.",
                        "her_time": "30 min",
                        "state": "halagada",
                        "options": [
                            {
                                "text": "Solo cuando me conviene. ¡Descansa! 😈",
                                "is_correct": True,
                                "required_time": "45 min",
                                "coach_feedback": "¡Genial! No aceptas la etiqueta de 'lindo' de forma pasiva, juegas con el doble sentido, esperas el tiempo justo y cierras tú la conversación.",
                                "investment_impact": 20
                            },
                            {
                                "text": "Siempre seré lindo contigo",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Cisne de peluche. Aceptar el rol de 'lindo' incondicional te mete de cabeza a la friendzone.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Tú eres más linda ❤️",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Devolver el cumplido de forma automática demuestra falta de ingenio y sumisión conversacional.",
                                "investment_impact": -15
                            },
                            {
                                "text": "De nada, para eso estamos",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Respuesta de servicio al cliente. Suena aburrido y desprovisto de toda chispa coqueta.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 4,
                        "her_message": "Jaja qué malo. Bueno, ya estoy mejor. Oye, ¿qué vas a hacer el miércoles? Vi que hay un evento de arte que quería ir.",
                        "her_time": "1 día después",
                        "state": "iniciando",
                        "options": [
                            {
                                "text": "Suena interesante ese evento de arte. El miércoles tengo libre por la tarde, ¿a qué hora empieza? 😎",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "Excelente. Aceptas su iniciativa (alto interés de su parte) pero mantienes tu postura de liderazgo coordinando con calma.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Iría a donde fuera contigo! Cancelo todas mis citas de trabajo para acompañarte 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Priorizarla por encima de tu trabajo tan rápido destruye tu valor profesional y personal. Calibra.",
                                "investment_impact": -25
                            },
                            {
                                "text": "El arte me da hueva, prefiero ir a jugar play.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Demasiado cortante y descortés con sus gustos. Matará el interés.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Como quieras, invítame tú.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Cero caballerosidad. Muestra pereza extrema.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 5,
                        "her_message": "Empieza a las 7:00 pm. ¿Nos vemos en la entrada del museo?",
                        "her_time": "20 min",
                        "state": "cooperativa",
                        "options": [
                            {
                                "text": "Perfecto, te veo ahí a las 6:50 pm. El que llegue tarde invita la primera ronda de bebidas después del museo 😉.",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "Muy bien. Lideras la logística y mantienes la dinámica de retos divertidos.",
                                "investment_impact": 15
                            },
                            {
                                "text": "Sí hermosa, a la hora que tú me digas, yo estaré ahí desde una hora antes esperándote.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Llegar una hora antes a esperar demuestra desesperación por su presencia.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Bueno, ahí nos vemos.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Corto y plano. Le quitas emoción al plan.",
                                "investment_impact": -5
                            },
                            {
                                "text": "Mejor cámbialo para el fin de semana.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Intentar cambiar su plan propuesto sin una justificación válida te hace ver poco flexible.",
                                "investment_impact": -10
                            }
                        ]
                    },
                    {
                        "step_id": 6,
                        "her_message": "¡Jajaja trato! Me encanta ese reto. Prepárate para pagar las bebidas.",
                        "her_time": "10 min",
                        "state": "retadora",
                        "options": [
                            {
                                "text": "Ya veremos quién ríe al final. Disfruta tu lunes, ¡hablamos el miércoles! 😎",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "Excelente. Cierras la conversación dejando la tensión en alto, sin alargar el chat innecesariamente.",
                                "investment_impact": 20
                            },
                            {
                                "text": "No, en serio, yo pago todo hermosa, no te preocupes por el dinero jamás.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Pagar todo de forma solemne mata el juego y la diversión del reto inicial.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Ok cuídate.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Cierre demasiado seco, casi parece molesto.",
                                "investment_impact": -5
                            },
                            {
                                "text": "Oye, ¿y de qué quieres hablar mientras llega el miércoles?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Alargar el chat sin propósito concreto desgasta la interacción.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 7,
                        "her_message": "Hola, ya estoy llegando al museo, hay un poco de tráfico pero estaré ahí justo a tiempo.",
                        "her_time": "6:45 PM",
                        "state": "informando",
                        "options": [
                            {
                                "text": "Perfecto, acabo de estacionarme. Te veo en las escaleras principales. Con cuidado al bajar 🚗.",
                                "is_correct": True,
                                "required_time": "inmediato",
                                "coach_feedback": "Excelente confirmación en tiempo real. Seguro y enfocado.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Qué bueno! Ya estaba preocupado de que no vinieras y me dejaras plantado 🥺",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Revelas miedo al rechazo e inseguridad personal justo antes de verla. Evítalo.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Apúrate por favor.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Tosco e impaciente. Ella te avisó con educación y va a tiempo.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Ok.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Demasiado seco para la emoción del momento.",
                                "investment_impact": -5
                            }
                        ]
                    },
                    {
                        "step_id": 8,
                        "her_message": "La pasé increíble en el museo y las copas de después. Eres un gran conversador la verdad. Quédate con cuidado de camino a casa. 😊",
                        "her_time": "11:30 PM",
                        "state": "encantada",
                        "options": [
                            {
                                "text": "Yo también la pasé genial Camila. Ya en casa. Descansa, nos vemos pronto. 😎",
                                "is_correct": True,
                                "required_time": "1 hora",
                                "coach_feedback": "Muy calibrado. Muestras interés mutuo pero mantienes tu espacio personal al no alargar el chat nocturno.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Yo la pasé mil veces mejor! Ya te extraño demasiado, no puedo esperar a verte mañana de nuevo 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Nivel de desesperación crítico. Proyectas que te apegas demasiado rápido.",
                                "investment_impact": -25
                            },
                            {
                                "text": "Ok, gracias por venir.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Suena a transacción comercial. Cero romance u hombría.",
                                "investment_impact": -10
                            },
                            {
                                "text": "¿Quieres que sigamos platicando por llamada de video ahora que llegué?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Invadir su espacio nocturno después de haber salido horas juntos es contraproducente.",
                                "investment_impact": -20
                            }
                        ]
                    },
                    {
                        "step_id": 9,
                        "her_message": "Hola, oye... ando un poco confundida con lo nuestro. Siento que todo va muy rápido y no sé qué busco realmente ahora.",
                        "her_time": "2 días después",
                        "state": "duda",
                        "options": [
                            {
                                "text": "Te entiendo perfectamente. Vamos con calma, no hay prisa de etiquetar nada. Disfrutemos el proceso. ¿Cómo va tu día? 😊",
                                "is_correct": True,
                                "required_time": "4 horas",
                                "coach_feedback": "¡Excelente control! Al no asustarte ni presionarla, demuestras madurez y le quitas toda la presión, calmando sus dudas.",
                                "investment_impact": 25
                            },
                            {
                                "text": "¿Cómo que confundida? ¿Hay otro tipo? Exijo que me digas la verdad ahora mismo 😠",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Celos y posesividad descontrolada. Acabas de destruir toda la atracción por tu inseguridad.",
                                "investment_impact": -30
                            },
                            {
                                "text": "Ah, bueno. Si no quieres nada serio mejor ya no me hables.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Ultimátum infantil. Demuestra inmadurez emocional extrema.",
                                "investment_impact": -25
                            },
                            {
                                "text": "Dime qué hice mal por favor, yo cambio lo que quieras para que estés feliz conmigo 🥺",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Sumisión total. Te arrodillaste ante la primera duda conversacional. Perdiste todo atractivo.",
                                "investment_impact": -30
                            }
                        ]
                    },
                    {
                        "step_id": 10,
                        "her_message": "Gracias por entender, me dejas mucho más tranquila. Oye, ¿sigue en pie la cena de este viernes? Me gustaría verte.",
                        "her_time": "3 horas",
                        "state": "aliviada",
                        "options": [
                            {
                                "text": "Claro que sí, sigue en pie. Pasaré a las 8:30 pm por ti. ¡Prepárate para una buena plática! 😏",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "¡Cierre de oro! Mantienes la cita inicial, dejas ver que tienes el control y manejas la situación de forma sumamente atractiva.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¡Sí! Menos mal, ya estaba llorando pensando que me ibas a cancelar. Nos vemos el viernes hermosa 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Revelar que estabas llorando o excesivamente preocupado rompe la figura masculina protectora y segura.",
                                "investment_impact": -25
                            },
                            {
                                "text": "No sé, déjame ver si no me sale algo mejor.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Arrogancia barata que busca castigarla. Suena inmaduro y manipulador.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Mejor veámonos hoy mismo, no puedo esperar hasta el viernes.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Ansiedad descalibrada. Ella te pidió ir con calma y tú aceleras el paso al instante.",
                                "investment_impact": -25
                            }
                        ]
                    }
                ]
            },
            {
                "level_id": 4,
                "girl_name": "Isabella",
                "name": "Nivel 4: El Shit Test de Cancelación",
                "description": "Tienes una cita programada con Isabella hoy por la tarde, pero ella te lanza un shit test cancelándote a última hora. Isabella es modelo, sumamente cotizada y fría. Solo puedes fallar 1 vez.",
                "steps": [
                    {
                        "step_id": 1,
                        "her_message": "¡Hola! Oye, perdón, pero hoy se me complicó muchísimo el día y no voy a poder vernos. Qué pena en serio 😫",
                        "her_time": "2 horas antes",
                        "state": "cancelando",
                        "options": [
                            {
                                "text": "¡Hola Isabella! Espero que tu día vaya bien. ¿Sigue en pie lo de hoy en la tarde? 😎",
                                "is_correct": True,
                                "required_time": "4 horas",
                                "coach_feedback": "Bien jugado. Confirmas con calma y educación unas horas antes, sin sonar desesperado ni urgido.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Hola Isabella! Todo listo para vernos en unas horas, ¿no? Avísame si ya vas en camino 😎",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Confirmación demasiado ansiosa presionándola para saber si ya va en camino. Transmite urgencia.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Espero que no me vayas a cancelar como la otra vez...",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Pre-confirmas asumiendo el rechazo o reclamando antes de tiempo. Te proyecta como alguien resentido.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Oye, ¿si vamos a salir hoy?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Pregunta de inseguridad muy escueta. Muestra impaciencia.",
                                "investment_impact": -15
                            }
                        ]
                    },
                    {
                        "step_id": 2,
                        "her_message": "Sí, me salió una sesión de fotos de último minuto que no puedo aplazar. De verdad lo siento mucho, se me sale de las manos.",
                        "her_time": "15 min",
                        "state": "justificándose",
                        "options": [
                            {
                                "text": "Entiendo, yo también tengo cosas pendientes que terminar de hecho. Que se resuelva rápido, cuídate.",
                                "is_correct": True,
                                "required_time": "1 hora",
                                "coach_feedback": "¡Control emocional de crack! No le reclamas nada y dejas ver que tu tiempo es valioso y que tienes una vida ocupada.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¡No te preocupes hermosa! ¿Mañana puedes?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Error fatal. Te cancela y tú inmediatamente le propones reagendar para el día siguiente. Te ves 100% disponible y sin opciones.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Ah ok.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Respuesta cortante pasivo-agresiva. Demuestras que te dolió y te molestó su cancelación laboral.",
                                "investment_impact": -15
                            },
                            {
                                "text": "¿Otra vez? Me hubieras avisado antes, ya me había arreglado.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Berrinche emocional. Le estás reclamando y demostrando que tu día dependía enteramente de ella. Perdiste todo atractivo.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 3,
                        "her_message": "Ay, gracias por entender en serio. Oye, para compensarte, ¿qué te parece si salimos el jueves? Yo invito los tragos jaja 🙈",
                        "her_time": "45 min",
                        "state": "receptiva",
                        "options": [
                            {
                                "text": "Déjame revisar mi agenda y te confirmo más al rato, pero creo que sí se arma. 😎",
                                "is_correct": True,
                                "required_time": "45 min",
                                "coach_feedback": "¡Excelente cierre! Demuestras que tu tiempo es valioso y que tienes planes por revisar, pero te mantienes buena onda y abierto a coordinar.",
                                "investment_impact": 25
                            },
                            {
                                "text": "¡Sí, claro! El jueves está perfecto.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Aceptación inmediata y sumisa. Pierdes la oportunidad de mantener tu valor y demostrar que tienes agenda propia.",
                                "investment_impact": -15
                            },
                            {
                                "text": "No sé, ya veremos...",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Demasiado distante y evasivo, puede enfriar el interés de ella si te pasas de misterioso.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Más te vale que esta vez sí vayas 😠",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Amenaza o advertencia tosca disfrazada de juego. Genera tensión negativa innecesaria.",
                                "investment_impact": -20
                            }
                        ]
                    },
                    {
                        "step_id": 4,
                        "her_message": "Dale, me avisas entonces. Estaré atenta a tu confirmación.",
                        "her_time": "15 min",
                        "state": "esperando",
                        "options": [
                            {
                                "text": "Todo listo para el jueves. Ya agendado. Nos vemos a las 8:30 pm en el bar secreto 😏.",
                                "is_correct": True,
                                "required_time": "4 horas",
                                "coach_feedback": "Excelente. Confirmas unas horas después, asumiendo el liderazgo y concretando la cita definitiva.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Oye sí puedo! Ya revisé mi agenda y está totalmente libre para ti el jueves y cualquier día 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Disponible en bandeja de plata. Rompes el misterio en un segundo.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Aún no sé, ando muy ocupado. Luego te digo.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Exceso de desinterés. Si ella ya te propuso compensarte, no debes ser grosero ni postergarlo demasiado.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Mejor ven tú a mi casa hoy mismo en la noche.",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Propuesta sexual descalibrada de último momento. Te reportará un bloqueo inmediato con este perfil de chica.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 5,
                        "her_message": "Hola, ya es jueves. ¿Sigue en pie la cena o también me vas a hacer esperar? jaja",
                        "her_time": "11:00 AM",
                        "state": "probando",
                        "options": [
                            {
                                "text": "Hola Isabella. Claro que sí, todo listo. Te veo a las 8:30 pm. Llega guapa 😎.",
                                "is_correct": True,
                                "required_time": "1 hora",
                                "coach_feedback": "Muy bien. Devuelves el reto con carisma ('llega guapa') y confirmas de forma segura.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Hola hermosa! ¡Sí obvio! Llevo pensando en ti desde el lunes, no te cancelaría jamás mi reina 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Sumisión desmedida. Te declaras incondicional y pierdes todo el valor que habías acumulado.",
                                "investment_impact": -20
                            },
                            {
                                "text": "Sí, nos vemos allá.",
                                "is_correct": False,
                                "required_time": "3 horas",
                                "coach_feedback": "Respuesta insípida. Con una modelo cotizada, la falta de chispa coqueta la aburrirá.",
                                "investment_impact": -5
                            },
                            {
                                "text": "La verdad ando cansado, mejor salgamos otro día.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Castigo infantil por su cancelación anterior. Puede enfriar el juego de forma definitiva.",
                                "investment_impact": -20
                            }
                        ]
                    },
                    {
                        "step_id": 6,
                        "her_message": "Jaja obvio que llegaré guapa. Oye, ¿puedes pasar por mí a mi casa? Queda un poco retirado el bar.",
                        "her_time": "3 horas antes",
                        "state": "probando_esfuerzo",
                        "options": [
                            {
                                "text": "El bar nos queda en un punto medio ideal. Nos vemos directo allá a las 8:30 pm, maneja con cuidado 🚗.",
                                "is_correct": True,
                                "required_time": "espejeo",
                                "coach_feedback": "¡Excelente calibración de esfuerzo! Al no ceder a ser su chofer gratis en la primera cita, mantienes tu valor e inviertes con equilibrio.",
                                "investment_impact": 20
                            },
                            {
                                "text": "¡Sí claro! Pásame tu ubicación y yo manejo 1 hora de ida y otra de vuelta sin problema hermosa 😘",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Proveedor y chofer. Hacer un esfuerzo logístico desmedido por alguien que apenas conoces te posiciona abajo en valor.",
                                "investment_impact": -20
                            },
                            {
                                "text": "No, no tengo auto. Vete en uber.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Demasiado tosco y seco. Podrías haber liderado el punto medio con mayor tacto.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Si paso por ti, ¿qué gano yo a cambio? 😏",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Negociación sexual/afectiva barata muy tosca para esta fase. Suena urgido.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 7,
                        "her_message": "Mmm bueno, nos vemos directo allá entonces. Ya voy saliendo.",
                        "her_time": "8:00 PM",
                        "state": "resignada",
                        "options": [
                            {
                                "text": "Perfecto, yo también voy en camino. Con cuidado al manejar. 🚗",
                                "is_correct": True,
                                "required_time": "inmediato",
                                "coach_feedback": "Confirmación segura y caballerosa.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Sí corre por favor! Ya estoy aquí esperándote en el frío 🥺",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Revelas impaciencia y te quejas del clima. Demuestra debilidad.",
                                "investment_impact": -15
                            },
                            {
                                "text": "Ok.",
                                "is_correct": False,
                                "required_time": "15 min",
                                "coach_feedback": "Cierre seco sin calidez.",
                                "investment_impact": -5
                            },
                            {
                                "text": "Oye, ¿si te vestiste como te pedí?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Pregunta controladora e insegura. Genera desconfianza.",
                                "investment_impact": -20
                            }
                        ]
                    },
                    {
                        "step_id": 8,
                        "her_message": "La pasé increíble hoy contigo. Tienes una vibra súper diferente a los demás niños. Avisa cuando llegues a casa.",
                        "her_time": "11:45 PM",
                        "state": "interesada_alta",
                        "options": [
                            {
                                "text": "Yo también la pasé excelente Isabella. Ya en casa. Descansa, hablamos luego. 😎",
                                "is_correct": True,
                                "required_time": "1 hora",
                                "coach_feedback": "Excelente. Mantienes la calma, demuestras que tu vida continúa y no te desvelas chateando de más.",
                                "investment_impact": 15
                            },
                            {
                                "text": "¡Yo la pasé muchísimo mejor hermosa! Eres perfecta, no puedo dejar de pensar en ti 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Nivel de intensidad extremo. Decirle que es perfecta tras la primera cita rompe la intriga.",
                                "investment_impact": -25
                            },
                            {
                                "text": "Ok gracias.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Demasiado frío, parece que no te importó salir con ella.",
                                "investment_impact": -10
                            },
                            {
                                "text": "¿Quieres que sigamos platicando por llamada de video ahora que llegué?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Avance sexual desmedido y apresurado. Puede arruinar toda la comodidad construida.",
                                "investment_impact": -25
                            }
                        ]
                    },
                    {
                        "step_id": 9,
                        "her_message": "Hola, ando libre hoy por la tarde. ¿Qué haces? Podríamos ver una película en mi departamento si no tienes planes.",
                        "her_time": "2 días después",
                        "state": "proponiendo",
                        "options": [
                            {
                                "text": "Me gusta la idea. Tengo libre a partir de las 6:00 pm. Yo llevo el vino, ¿tinto o blanco? 😏",
                                "is_correct": True,
                                "required_time": "4 horas",
                                "coach_feedback": "¡Excelente! Aceptas de forma madura su invitación a su espacio personal (máximo nivel de atracción) y lideras llevando el vino.",
                                "investment_impact": 25
                            },
                            {
                                "text": "¡¡SÍ!! Voy volando para allá ahora mismo, no me importa nada más en el mundo 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Desesperación total. Pareces un perrito esperando que le abran la puerta. Calibra tu valor.",
                                "investment_impact": -25
                            },
                            {
                                "text": "No, qué flojera ir hasta allá. Mejor ven tú a mi casa.",
                                "is_correct": False,
                                "required_time": "espejeo",
                                "coach_feedback": "Tosco y flojo. Ella te invitó a su espacio y tú le pides que haga el esfuerzo logístico.",
                                "investment_impact": -20
                            },
                            {
                                "text": "No sé si pueda, tengo muchas cosas que hacer. Te aviso luego.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Postergar la cita de forma artificial cuando la atracción está al máximo es un error. Acepta con liderazgo.",
                                "investment_impact": -10
                            }
                        ]
                    },
                    {
                        "step_id": 10,
                        "her_message": "Tinto está súper bien. Te paso mi dirección: [Dirección]. Te veo a las 6:00 pm entonces. ¡No vayas a llegar tarde! 😉",
                        "her_time": "1 hora",
                        "state": "esperando_cita",
                        "options": [
                            {
                                "text": "Ya agendado. Allá estaré a las 6:00 pm en punto con el vino. Prepárate para perder la apuesta del helado jaja. ¡Cuídate! 😏",
                                "is_correct": True,
                                "required_time": "15 min",
                                "coach_feedback": "¡Soberbia calibración! Cierras el juego por completo, concretas el encuentro definitivo y mantienes el chiste de la apuesta en alto. ¡Felicidades, ganaste el juego!",
                                "investment_impact": 25
                            },
                            {
                                "text": "¡Perfecto mi reina! Ya voy saliendo desde ahorita para no llegar tarde, te amo 😍",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Decirle 'te amo' en esta fase es un suicidio de atracción. Ella saldrá corriendo.",
                                "investment_impact": -30
                            },
                            {
                                "text": "Ok, ahí nos vemos.",
                                "is_correct": False,
                                "required_time": "1 hora",
                                "coach_feedback": "Cierre demasiado seco y plano para una cita en su departamento.",
                                "investment_impact": -10
                            },
                            {
                                "text": "Oye, ¿y si mejor salimos a cenar a un restaurante caro?",
                                "is_correct": False,
                                "required_time": "inmediato",
                                "coach_feedback": "Intentar cambiar una invitación a su departamento (el plano de mayor intimidad) por un restaurante público y costoso es un autogol de atracción.",
                                "investment_impact": -25
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    out_path = r"C:\desarrollos\antigravity\text game youtube estudio ejemplos\scratch\game_dialogues.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dialogues, f, ensure_ascii=False, indent=2)
    print("Database JSON generated successfully with 40 detailed questions!")

if __name__ == "__main__":
    main()
