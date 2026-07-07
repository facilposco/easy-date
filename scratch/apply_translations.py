# -*- coding: utf-8 -*-
import sys

# Asegurar que se procese con codificación utf-8
sys.stdout.reconfigure(encoding='utf-8')

replacements = [
    # Caso 1
    (
        '<div class="bubble me">amanecer para cualquier noche, pero necesito mi café de la mañana con eso<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Prefiero el amanecer ante cualquier noche, pero necesito mi café de la mañana para acompañarlo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">cuello en V profundo para que veas cómo brillo<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">cuello en V bien profundo para que veas cómo brillo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">el pelo en pecho también necesita amor<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">el pelo en pecho también necesita cariño<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">buen eslogan, deberías ponerlo en tu camisa de cuello en V<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">buen eslogan, deberías estamparlo en tu camisa de cuello en V<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">pero eso le quitaría atención al premio<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">pero eso le quitaría protagonismo al verdadero premio<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">o atraerle más atención potencialmente<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">o tal vez le traería aún más atención<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">no queremos que luzca como una drag queen, ya soy demasiado sexy<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">tampoco queremos exagerar, ya soy demasiado sexy de por sí<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">mi ubicación dice a 2,000 millas de distancia pero, ¿te amo?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">mi ubicación dice que estoy a 2,000 millas de distancia, pero ¿quién le cree a la distancia? 😉<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">creo que mi ubicación no está bien, vivo en esta<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">creo que mi ubicación está mal, yo vivo en esta ciudad<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">caminaría 2,000 millas por algunas risas sobre el pelo en pecho<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">caminaría 2,000 millas solo para reírnos de mi pelo en pecho<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">lástima que solo haya canciones para 500 o 1,000 millas<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">lástima que solo haya canciones de 500 o 1,000 millas<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">tú, yo, una botella de vino y podrías jugar con mi pelo en pecho<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">tú, yo, una botella de vino y te dejo jugar con mi pelo en pecho<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">una canción original, nada menos, inspirada en la estupidez de Tinder<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">una canción original inspirada en las tonterías de Tinder<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">puede que incluya o no agarrarte el trasero<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">podría incluir o no agarrarte el trasero 😏<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">escuché que tienes debilidad por un buen trasero<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">escuché que tienes debilidad por los buenos traseros<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">maldición, no estoy seguro de poder esperar un par de días<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Rayos, no sé si pueda esperar un par de días<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">no busco ser un pasatiempo como lo he sido en el pasado<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">no busco ser solo un pasatiempo como en el pasado<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Caso 2
    (
        '<div class="bubble me">lo dice la chica de la foto echándole gasolina al fuego carita guiñando<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Lo dice la chica que sale echándole gasolina al fuego 😉<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">touché en realidad no estaba echándola fue solo el momento perfecto de la cámara qué te hace no ser bueno y seguro<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Touché. En realidad no la estaba echando, fue solo el momento justo de la foto. ¿Y qué te hace a ti no ser "bueno y seguro"?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">no te encuentro sorprendentemente encantadora y excéntrica hasta ahora pensaba que estabas insinuando que eras rara y disculpándote por tu chiste cursi jajaja<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Para nada. De hecho, me pareces sorprendentemente encantadora y exótica. Pensaba que estabas insinuando que eras rara y te disculpabas por tu chiste cursi jajaja<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">si texteas más seguido de lo que usas hinge<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">A ver si escribes más seguido de lo que usas Hinge...<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Caso 3
    (
        '<div class="bubble me">deslicé a la derecha por esas ganancias de glúteos<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Le di a la derecha por el resultado de tus sentadillas 😏<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">deslicé a la derecha por todo tu tren superior, por favor dime que tú también vienes con trasero<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Le di a la derecha por todo tu torso. Por favor dime que tú también tienes lo tuyo atrás<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">de si puedes quitarle los ojos a mis abdominales<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">De si puedes quitarle la mirada a mis abdominales<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">hmm si no puedo resistirme a tus abdominales tendré que estirar la mano y agarrarte el trasero<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Hmm, si no puedo resistirme a tus abdominales, tendré que estirar la mano y agarrarte el trasero<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿vas a hacer eso cuando tengas las manos esposadas?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Y cómo vas a hacer eso si tienes las manos esposadas? 😏<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">um, la pregunta es si serás capaz de someterme antes de que yo te agarre<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Mmm, la pregunta es si vas a poder someterme antes de que te agarre yo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">Me gusta pelear un poco, pero estoy seguro de que puedo. Si todo lo demás falla, simplemente te agarraré de la cara por el cabello y te ahorcaré para que te sometas.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Me gusta el juego rudo, así que seguro puedo. Y si todo falla, te agarro del cabello y te pongo en tu lugar hasta que te rindas.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">oh, ahora eso va a ser difícil, me gusta eso así que probablemente no me resista<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Uy, ahora eso va a estar difícil. Me gusta, así que probablemente no me resista<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">Sé que eres un poco traviesa, luego te doblaré sobre mi regazo con una tela envuelta en tu boca mientras te nalgueo con mi brazo fuerte y tú te retuerces<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Sé que eres traviesa. Te voy a poner sobre mi regazo, te tapo la boca y te doy unas buenas nalgadas con ganas mientras te retuerces<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¡Qué injusto! tú puedes nalguearme y yo ni siquiera puedo tocarte<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¡Qué injusto! Tú me nalgueas y yo ni puedo tocarte<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿todo eso? Le voy a hacer cosas más traviesas a mi cuerpecito<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¿Todo eso? Yo le hago cosas más traviesas a mi cuerpo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">hmm estoy intrigada, ¿tendremos que armar una cita entonces?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Mmm, me intriga. ¿Entonces tenemos que armar una cita?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">[ __ ] increíble, relajándome en mi balcón romántico, ¿y tú?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">De maravilla, relajándome en mi balcón romántico, ¿y tú?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">eres muy romántico ¿no? acabo de salir de la cama, ahora estoy haciendo el desayuno, ¿quieres un poco?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Súper romántico, ¿no? Acabo de levantarme y estoy preparando el desayuno, ¿gustas?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">sí, pero después de los huevos y el tocino, ¿qué voy a recibir?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Sí, pero después de los huevos con tocino, ¿qué me vas a dar de postre?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">está bien, te haré un poco. Te ofrecería postre pero ¿no es muy temprano para el postre?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Bueno, te cocino un poco. Te ofrecería postre, pero ¿no es muy temprano?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">oh, tendrías que probarlo para saber con 100% de certeza que te encantaría<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Vas a tener que probarlo para estar cien por ciento segura de que te va a encantar<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">tendremos que armar una sesión de degustación de postres<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Entonces hay que armar una degustación de postres<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿podemos vernos en público? Porque necesito saber que no eres un viejo gordo apestoso asesino del hacha<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Pero ¿nos vemos en público? Necesito comprobar que no eres un viejo gordo, feo y psicópata<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿cómo sé que no eres un tipo negro de 300 libras?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Y yo cómo sé que no eres un tipo de dos metros y 150 kilos?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">por eso nos vemos en público, para que puedas salir corriendo si lo soy<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Por eso mismo en público, así puedes salir corriendo si lo soy jajaja<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Caso 4
    (
        '<div class="bubble me">Gracias [her name], tú tampoco te ves nada mal. Entonces, ¿esta es la parte donde empezamos un romance torbellino y nos casamos y divorciamos en tiempo récord? 🤔<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Gracias [her name], tú tampoco estás nada mal. ¿Entonces aquí es donde empezamos un romance fugaz, nos casamos y nos divorciamos en tiempo récord? 🤔<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">y eso significa que vivo aquí parte del año pero viajo mucho. Parece que el español sería mejor para ti.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Eso significa que vivo aquí parte del año pero viajo un buen. Igual si quieres podemos hablar en español.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">Wow, eres muy ofensivo. Jaja, hablo inglés. Fui a la universidad, jaja. Dios mío, chico blanco loco [ __ ]<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¡Wow, qué ofensivo! Jaja, sí hablo inglés, fui a la universidad. Dios, qué loco estás.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">Jaja, dijiste que tu amiga tradujo, así que estaba intentando ayudarte. 😂 Me alegra que seas segura de ti misma, educada y un poco atrevida.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Jaja, como dijiste que tu amiga te tradujo, solo quería facilitarte las cosas. 😂 Pero me gusta que seas segura, inteligente y con carácter.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">solo tradujo chico blanco y volteé los ojos.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Ella solo tradujo "chico blanco" y yo viré los ojos.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">Afortunadamente, hablo con fluidez tanto \'chico blanco\' como \'Latina loca\', así que no necesitaremos un traductor en nuestras citas, pero puede que necesitemos un acompañante para proteger al inocente de mí de tus encantos femeninos. 😇<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Por suerte, hablo fluido tanto "chico blanco" como "latina intensa", así que no ocuparemos traductor en nuestras citas. Aunque tal vez sí un guardaespaldas para protegerme de tus encantos. 😇<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">[number] avísame si me escribes porque mi [ __ ] está súper hackeado. Sé cómo suena eso.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">[number] Avísame si me escribes porque mi teléfono anda fallando horrible. Ya sé cómo suena eso.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">Hola, [her name], soy Douglas de Hinge. Tengo ganas de conocerte pronto. Por favor guarda este número para que puedas emocionarte adecuadamente al saber de mí.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Hola [her name], soy Douglas de Hinge. Ya quiero que nos conozcamos. Guarda mi número para que te emociones cada vez que te escriba.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">Hola, lo haré. Tengo que conseguir un Android de emergencia, así que de verdad lo siento si desaparezco. Es como una onda Bebé Reno [ __ ]<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Hola, ya lo guardé. Tengo que conseguir un Android de repuesto rápido, así que perdón si me pierdo. Esto parece de película de terror.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">[her plans] conseguir algo de dinero y comprar un Android. Eres un hombre blanco, así que sé que esta onda de acosadores [ __ ] les parece divertida a ustedes, pero en serio, no lo es. ¿Necesitan a Cristo? ¿Qué estás haciendo? Poniéndome al día, recibiendo palizas. Jaja. Oh Dios mío D. Mi funda la rompe.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">[sus plans] conseguir dinero y comprar un Android. Como eres blanco, seguro te da gracia todo este rollo de los acosadores, pero en serio no da risa. ¿Ocupan a Dios en su vida? ¿Tú qué andas haciendo? Yo aquí poniéndome al día y cansadísima. Jaja. Ay no, me da demasiada risa mi situación.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">Estoy ocupado durante el día, pero posiblemente podría encontrar tiempo para tomar algo y una charla ingeniosa por la noche, ya sea hoy o mañana<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Estoy ocupado de día, pero podría darme un espacio para tomar algo y conversar un rato en la noche, ya sea hoy o mañana.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">Douglas, mejor dale gracias a Dios que no estás por mi zona porque te quiero partir la madre. Dios mío. Sabes cuánta gente me escribe en español. Uh, mayormente mi familia. Jaja. Estaba pensando que esto era el fin. Uh, hubieras aprobado el AP Spanish 4. Um, no te enojes tanto. Habla ahora o no sé. No se me ocurre con qué amenazarte.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Douglas, dale gracias a Dios que no estás cerca porque te daría una paliza jajaja. Qué locura. No sabes cuánta gente me escribe en español (bueno, casi toda mi familia). Pensé que este era el fin. Seguro habrías aprobado Español Avanzado en la escuela. Tampoco te enojes. Habla ahora o no sé... no se me ocurre con qué amenazarte.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">O sea, podrías amenazarme con unos tragos y una charla ingeniosa con una linda pero un poco loca nueva amiga. Salgo de la ciudad mañana, así que esta amenaza solo está disponible por tiempo limitado. ⏰<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">O sea, podrías amenazarme con unos tragos y una charla divertida con una linda pero intensa nueva amiga. Salgo de la ciudad mañana, así que esta amenaza expira pronto. ⏰<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">Como, okey. No sabía que teníamos a una celebridad en el chat. Dios mío. ¿Cómo se supone que esté lista? O sea, alguien con tu estatus de proxeneta debería saber que las perras necesitan al menos un mes. Ahora me veo obligada a lanzarte un maleficio por toda la eternidad. Es broma. No pierdas tiempo con pobres almas en desgracia, pero mis disculpas, su santidad. Estoy bromeando por completo, hijo. No te enojes, loquito<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">O sea, okay. No sabía que estaba hablando con una celebridad. Ay dios. ¿Y cómo se supone que me arregle rápido? Alguien con tu estatus de galán debería saber que una mujer necesita mínimo un mes. Ahora me obligas a echarte una maldición eterna. Mentira. No pierdas el tiempo con esta pobre alma, pero te pido disculpas, su santidad. Es puro juego, no te vayas a enojar, loquito.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">Bueno, sin duda me halaga que le dediques un mes de esfuerzo por mí, pero prefiero que simplemente seas tú misma. 😗 Apuesto a que puedes estar linda y presentable digamos para las siete u ocho de la noche. Sin problema.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Bueno, me halaga que le dediques un mes de esfuerzo a arreglarte para mí, pero prefiero que seas tú misma. 😗 Apuesto a que puedes estar lista para las siete u ocho de la noche sin problema.<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Caso 11
    (
        '<div class="bubble her">perdón, días ajetreados así que me desconecté un rato de tinder y todo eso mmm ¿podría hacerte una pregunta totalmente única y nada típica? ¿qué estás buscando?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Perdón, anduve muy ocupada y me desconecté un rato de Tinder. Mmm, ¿te puedo hacer una pregunta totalmente única y nada cliché? ¿Qué estás buscando por aquí?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">ooh ahora tú eres el que me emociona jajaja soy bastante de mente abierta con respecto a lo que busco, pero ¿prefieres que nos conozcamos un poco primero? me pregunto si eso es un deal breaker<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Ooh, ahora tú eres el que me está tentando jajaja. Soy de mente muy abierta con lo que busco, pero ¿prefieres que nos conozcamos un poco primero? Me pregunto si eso es un problema para ti.<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Caso 14
    (
        '<div class="bubble me">¿me huele a que te estás echando para atrás?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Me huele a que te estás arrepintiendo?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">no era mi intención no responder, me disculpo. No diría que me estoy echando para atrás per se, pero me pone muy nerviosa quedar con alguien del que no sé nada. Esto es muy nuevo para mí, si te soy sincera.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">No era mi intención ignorarte, de verdad disculpa. No diría que me estoy arrepintiendo, pero me pone muy nerviosa salir con alguien del que no sé nada. Esto es muy nuevo para mí, si te soy sincera.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">conocer a alguien por internet puede dar bastante miedo. Tengo una hermana, así que sé cómo se debe sentir. ¿Una llamada telefónica te haría sentir mejor? Así podemos entrar en confianza incluso antes de vernos cara a cara. Tampoco es que sea Thanos o algo así.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Conocer a alguien de internet puede dar algo de miedo, lo entiendo. Tengo una hermana, así que sé cómo se siente. ¿Una llamada rápida te haría sentir mejor? Así entramos en confianza antes de vernos en persona. Tampoco es que sea Thanos jajaja.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">de hecho me encantaría, gracias por entender. Eso me haría sentir mejor. El hecho de que acabes de decir que no eres Thanos literalmente me hizo reír a carcajadas. Y creo que tendremos que posponer lo del viernes por la noche porque se supone que va a nevar, no me siento cómoda manejando así. ¿Cómo está tu semana la próxima semana? Me gusta eso.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">De hecho me encantaría, gracias por entender. Eso me haría sentir más tranquila. Lo de que no eres Thanos me hizo reír de verdad. Creo que hay que posponer lo del viernes porque va a nevar y no me siento cómoda manejando así. ¿Qué tal tu próxima semana? Me late esa idea.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">sí, no soy el titán loco morado obsesionado con las gemas. El clima dice que solo estará nublado, no nevará. Estás mirando esa aplicación roja del clima de la que todos en el trabajo hablan, así que la busqué. Entiendo, odiaría que manejaras en la nieve. Puedo el martes o miércoles de la próxima semana.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Sí, no soy el titán loco morado. El pronóstico dice que solo estará nublado, no va a nevar. Seguro estás viendo esa app del clima de la que todos hablan jajaja. Pero entiendo, no quiero que manejes en la nieve. Puedo el martes o miércoles.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">sí, no haría eso aunque sí quiero conocerte. Normalmente no sé mis citas en esos días con anticipación, pero uno de esos días debería funcionar.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Sí, prefiero evitar el peligro, aunque sí quiero conocerte. Normalmente no sé mi horario con tanta anticipación para esos días, pero seguro uno de ellos funciona.<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Caso 17
    (
        '<div class="bubble her">eres una niña buena, todo eso apesta, creo que te ves mejor como chico<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Eso de ser "niño bueno" es aburrido, te ves mejor como chico malo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">gracias pero no te preocupes, soy demasiado dominante en la cama para eso<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">gracias pero no te preocupes, soy demasiado dominante en la cama como para ser un niño bueno<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">me gusta eso, siempre que pueda montarte todo está bien<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Me gusta. Mientras pueda dominarte un rato, todo bien<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">por supuesto, especialmente con ese trasero<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">por supuesto, sobre todo con ese trasero 😏<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">mido 5\'5 y no tengo mucho trasero, no es verdad<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Mido 1.65 y casi no tengo trasero, no inventes<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">oh basta, ambos sabemos que tienes buen trasero<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Ay, por favor. Los dos sabemos que tienes lo tuyo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">para mi tamaño de cuerpo sí lo tengo, gracias<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Bueno, para mi complexión sí, gracias<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">entonces dame lo básico, tatuajes, hijos, cosas raras<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">A ver, cuéntame lo básico: tatuajes, hijos, fetiches raros...<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">está prendido, me voy a casa, aburrida soltera jajaja<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Está buenísimo el ambiente. Ya voy a casa, aburrida y soltera jajaja<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">me imagino, estaré libre un poco más tarde mañana por la noche, deberías pasar por un trago o dos<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Me imagino. Mañana me libero tarde, deberías venir a tomar algo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">oh, eres una MILF<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Ah, eres una MILF<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">mi favorito, gracias amor<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Mis favoritas. Gracias por el dato, linda<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿qué harás esta noche? ¿quieres ir a Komodo conmigo? iré con unos amigos<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¿Qué vas a hacer hoy? ¿Quieres ir a Komodo conmigo y unos amigos?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">en el salón de belleza ahora, poniéndome rubia jajaja bueno caramelo<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Ando en la estética poniéndome más rubia jajaja. Hola, bombón<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">tengo planes esta noche, te veré mañana por la tarde-noche<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Hoy tengo planes y nosotros ya quedamos para mañana<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">planes esta noche y ya hicimos planes para mañana<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Hoy tengo planes y nosotros ya quedamos para mañana<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿es un interrogatorio?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Esto es un interrogatorio?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿por qué estás tan agresiva? voy a salir con mi amigo esta noche, tenemos planes mañana<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Por qué tan tóxica? Hoy salgo con un amigo y nosotros tenemos planes mañana<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿este es tu regalo de disculpa?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Esta foto es tu forma de pedir disculpas?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">digamos a las 9:00 ok<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Digamos a las 9, ¿va?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿qué quieres hacer? solo salgamos mañana, no hay nada abierto<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¿Qué quieres hacer? Mejor salgamos mañana, ya está todo cerrado<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">mi balcón está abierto, tequila y vino de barril<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Mi balcón está abierto, y tengo tequila y vino listos<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">hoy es el cumpleaños de mi amiga, qué conveniente, iré a eso así que podemos salir mañana<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Hoy es cumple de mi amiga, qué oportuno. Iré para allá, así que salimos mañana<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">solo busco citas pagadas para ser honesta, tipo que me pagas si cogemos<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Para ser sincera, solo busco citas de pago. O sea, cobro por acostarme con alguien<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">oh, eres una escort<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Ah, eres escort<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿con los feos coges gratis?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Y con los feos te acuestas gratis?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">no pago por sexo y eso es lo que querías, deberías haberlo dicho desde el principio<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">No pago por sexo, si eso era lo que querías me hubieras dicho desde el inicio<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿solo conoces gente por dinero?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Solo sales con gente por dinero?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿es eso raro? en realidad soy stripper, recién empecé de escort, mi amiga me recomendó eso<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¿Es muy raro? En realidad soy stripper, pero acabo de empezar como escort por recomendación de una amiga<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">no, he salido con algunas strippers pero tu enfoque es raro<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">No, he salido con strippers, pero tu forma de venderte es rarísima<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿hace cuánto? es un poco claro que eres amateur, una pro no usaría Tinder para esto<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Hace cuánto empezaste? Se nota que eres amateur, una profesional no usaría Tinder para esto<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">en realidad no me gusta coger mucho con gente, así que no soy escort solo con algún tipo a veces cuando estoy aburrida ese tipo de cosas, me gusta estar con una sola persona<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">En realidad no me gusta acostarme con cualquiera, así que no ando de escort siempre, solo a veces cuando estoy aburrida. Me gusta tener a alguien exclusivo<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿y crees que diciéndome a unas horas de nuestra cita que solo quieres verte por dinero me va a dar ganas de salir contigo?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿Y crees que avisarme unas horas antes de la cita que solo sales por dinero me va a dar ganas de verte?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">jajaja quieres salir conmigo, no te culpo, soy increíble<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Jajaja pero bien que quieres salir conmigo, no te culpo, soy increíble<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">bueno, definitivamente estás perdiendo puntos ahora mismo, la vida sigue, bla bla bla<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Bueno, definitivamente estás perdiendo puntos. En fin, la vida sigue<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">típica niña mimada de Miami<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">La típica niña mimada de Miami<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">oh gracias bebé eres muy dulce, en realidad no soy mimada pero gracias jajaja<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Ay gracias bebé, qué lindo. En realidad no soy mimada, pero gracias jajaja<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">finge esa actitud, buena idea, si dejas de poner excusas yo solo estoy aquí en el mundo haciendo lo mío<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Finge demencia, buena idea. Si vas a dejarte de excusas, avísame. Yo sigo en lo mío<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿quieres venir a mr. Jones conmigo?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¿Quieres venir a Mr. Jones conmigo?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">¿no me cancelaste hace una hora? lo siento<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">¿No me habías cancelado hace una hora? Qué pena<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">puedes venir a mi casa<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Si quieres ven a mi casa<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">a mr. Jones ven conmigo<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Ven conmigo a Mr. Jones<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">suena aburrido, paso<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Qué flojera, paso<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">un club nocturno era aburrido sí, especialmente ese, odio todos los clubes<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Un antro es aburrido, sí. Especialmente ese, odio los antros<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿tienes un bong o marihuana que podamos fumar?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¿Tienes una pipa o hierba para fumar?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">probably tengo por ahí<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Seguro tengo algo por ahí<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">ven a mr. Alex<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Mejor ven a ver a Mr. Alex<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">¿estás borracho con jdj o lo que sea, alguna tontería?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">¿Estás ebrio o algo así?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">oye, ¿quieres que nos abracemos y cojamos?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Oye, ¿quieres que nos acurruquemos y tengamos sexo?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">alistándome ahora, debería llegar 12:30 ¿está bien? vivo bla bla bla a unos 20 minutos de ahí pero hay tráfico<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Me estoy arreglando. Llego como 12:30, ¿está bien? Vivo a 20 minutos de ahí, pero hay algo de tráfico<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">ok genial ¿quieres que lleve marihuana, fumas?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Súper. ¿Quieres que lleve hierba? ¿Fumas?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">así que ahora todo lo que quiero es ahogarme con una buena verga, espero que tu verga sea buena<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Así que ahora lo único que quiero es una buena cogida, espero que la tengas buena<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble me">voy a hacer que te tragues cada centímetro<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble me">Te voy a hacer sentir cada centímetro<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">ok genial, menos mal que estás despierto oh dios mío odio los consoladores bueno no puedo esperar estoy muy emocionada<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Genial que estés despierto. Odio los juguetes sexuales, ya no puedo esperar, estoy súper caliente<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">lo será, mándame una provocación, mi coño ya está súper mojado<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Así será. Mándame una foto sexy, ya estoy mojadísima<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble her">estoy en el auto ahora, saliendo de la casa de mi amiga, ya casi llego a casa 12:05 ahora bla bla bla perfecto<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble her">Estoy en el auto ahora, saliendo de casa de mi amiga, ya casi llego a mi casa 12:05 ahora perfecto<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Fails - Caso 1
    (
        '<div class="bubble fail-me">Y la mujer está de vuelta en la ciudad.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Y ya estás de vuelta en la ciudad.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble fail-me">Lo bueno es que estaré en Dubái en agosto para unas conferencias de yoga, sería genial ir con otra entusiasta del yoga. Sé que apenas nos conocemos, así que está bien si no quieres pasar el rato.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Lo bueno es que estaré en Dubái en agosto para unas conferencias de yoga. Estaría genial ir con otra apasionada del yoga. Aunque sé que apenas nos conocemos, así que no hay problema si no quieres que salgamos.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble fail-me">Sí, deberíamos conocernos y quiero llevarte a una cita alguna vez, así vemos mejor la vibra. Es muy formal en mi opinión.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Sí, deberíamos vernos. Me gustaría invitarte a salir y ver qué tal la vibra. Esto de chatear es muy formal en mi opinión.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble fail-me">Ahora te haces la linda, ¿te das cuenta de nuestra cita candente?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Ahora te haces la difícil. ¿Te olvidaste de nuestra cita candente?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble fail-me">Parece que la senilidad te pegó temprano, Jesucristo.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Parece que la senilidad te pegó temprano, por Dios.<div class="msg-time">⏱️ N/A</div></div>'
    ),

    # Fails - Caso 3
    (
        '<div class="bubble fail-me">Entonces, dos opciones: podemos ir a un lugar cool o puedes venir a mi casa, preparamos algo rico de comer, ponemos música y nos relajamos. ¿Qué día estás libre?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Entonces, hay de dos: o vamos a un lugar cool, o vienes a mi casa a cocinar algo rico, escuchar música y relajarnos. ¿Qué día estás libre?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble fail-me">Pero, ¿por qué dirías que estás libre y preguntas qué tengo en mente, y luego de que te doy mis ideas no dices nada? No tiene ningún sentido.<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Pero a ver, ¿por qué dices que estás libre y me preguntas qué tengo en mente, si luego de darte mis ideas me dejas en visto? No tiene ningún sentido.<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble fail-her">Honestamente, estaba considerando volver a vernos pero no sé, tal vez cambié de opinión. Simplemente no me siento cómoda con cómo van las cosas, va todo muy rápido, ¿no crees?<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-her">Sinceramente, estaba pensando en que nos viéramos otra vez, pero no sé, cambié de opinión. No me siento cómoda con el rumbo que lleva esto, va todo muy rápido, ¿no crees?<div class="msg-time">⏱️ N/A</div></div>'
    ),
    (
        '<div class="bubble fail-me">Ok, entiendo. Primero que nada, nunca querría hacerte sentir incómoda forzándote a hacer algo contra tu voluntad... además de las dos veces que salimos me dijiste que lo disfrutaste, sería bastante estúpido de mi parte hacer que nuestras futuras citas no sean agradables jaja<div class="msg-time">⏱️ N/A</div></div>',
        '<div class="bubble fail-me">Ok, entiendo. Primero que nada, jamás querría hacerte sentir incómoda ni presionarte a hacer algo que no quieras... Además, las dos veces que salimos me dijiste que la pasaste súper bien. Sería muy tonto de mi parte arruinar las cosas para nuestras próximas citas jaja<div class="msg-time">⏱️ N/A</div></div>'
    )
]

with open('estudio_textgame_casos_reales.html', 'r', encoding='utf-8') as f:
    content = f.read()

count = 0
not_found = []

for target, replacement in replacements:
    if target in content:
        content = content.replace(target, replacement)
        count += 1
    else:
        not_found.append(target)

if count > 0:
    with open('estudio_textgame_casos_reales.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Éxito: Se aplicaron {count} reemplazos en estudio_textgame_casos_reales.html.")
else:
    print("Error: No se encontró ninguno de los fragmentos a reemplazar.")

if not_found:
    print(f"No encontrados ({len(not_found)}):")
    for nf in not_found:
        print("  - " + nf[:80] + "...")
