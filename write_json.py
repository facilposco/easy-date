import json
import os

data = {
    "video_id": "HU6AdwK_rnk",
    "scoring": 7.0,
    "justificacion_scoring": "Conversaciones muy orgánicas, largas y enfocadas en confort/rapport (salud, orígenes, anécdotas), con poca tensión. La resistencia de las chicas es nula y la fluidez es muy alta. Economía de palabras pobre (muchos bloques de texto largos), pero efectivo al aprovechar intereses comunes.",
    "fases": [
        {
            "plataforma": "Hinge (Conversación 1)",
            "mensajes": [
                {"autor": "Ella", "texto": "I'm weirdly attracted to science guys especially biology", "multimedia": "[En perfil]"},
                {"autor": "El", "texto": "it might be a good time to clarify that i'm a huge science and psychology note", "multimedia": None},
                {"autor": "El", "texto": "i have a joke where did napoleon put his armies where in his sleeves is this a good time to mention that the only thing i know about napoleon is that he was a short french guy oh you didn't get my lame joke", "multimedia": None},
                {"autor": "Ella", "texto": "unless you're talking about dynamite in which case i still don't get it", "multimedia": None},
                {"autor": "El", "texto": "armies childish way of saying arms sleevies childish way of saying sleeves sleeves oh haha joke crash and burn", "multimedia": None},
                {"autor": "Ella", "texto": "well if you laughed at it at least it had a 50 success rate so that's not a total loss lol", "multimedia": None},
                {"autor": "El", "texto": "thanks it's true though i really do laugh at my own jokes why tell a joke if it doesn't make yourself laugh", "multimedia": None},
                {"autor": "Ella", "texto": "i do the same i think i'm hilarious but i might be the only one huh i see you're just the next suburb over i bet if i yodeled loudly enough you might hear me", "multimedia": None},
                {"autor": "El", "texto": "but i try to keep my public yodelings to a limit", "multimedia": None},
                {"autor": "Ella", "texto": "oh that's you i've heard yearling that's more likely to be me yelling at my puppy when she escapes across the road did you grow up here", "multimedia": None},
                {"autor": "El", "texto": "nah i grew up in sydney moved here about four years ago you", "multimedia": None},
                {"autor": "Ella", "texto": "you're a trendsetter i moved here two years ago from sydney never looked back", "multimedia": None},
                {"autor": "El", "texto": "do you feel like getting a coffee or drink sometime", "multimedia": None},
                {"autor": "Ella", "texto": "sure where about and sid sure i'm at free sometime this weekend", "multimedia": None},
                {"autor": "El", "texto": "uh sure sometime this weekend works would work well perhaps coffee saturday afternoon", "multimedia": None},
                {"autor": "Ella", "texto": "yeah sounds good", "multimedia": None}
            ]
        },
        {
            "plataforma": "Hinge (Conversación 2)",
            "mensajes": [
                {"autor": "El", "texto": "i was almost arrested in that fear for being too happy on public transport", "multimedia": "[En perfil]"},
                {"autor": "Ella", "texto": "story of my life", "multimedia": "[Respuesta al perfil]"},
                {"autor": "El", "texto": "so i really have to know what compelled you to lie in a gym top in the snow", "multimedia": None},
                {"autor": "Ella", "texto": "ha ha well i've dived pretty deep into breath work and cold immersion these past couple of years so it's actually a pretty standard thing i do with my friends we go to the snow and jump in all the rivers and lakes while we're there", "multimedia": None},
                {"autor": "El", "texto": "haha sounds perfectly normal actually i got pretty heavily into breath work about five years ago and then again in a wood for a while but i never tried jumping into the into a cold lake haha i actually bought a chest freezer today for the purpose for the purposes of ice baths not storing frozen goods and as an added bonus if you ever find yourself in one of those wacky netflix show situations where you have accidentally killed someone you have a convenient place to store the body", "multimedia": None},
                {"autor": "Ella", "texto": "it's supposed to be great for prolonging lifespan cold baths not random murder", "multimedia": None},
                {"autor": "El", "texto": "exactly it's a win-win and yes i'm a bit of a health nut well it's my career so into all the crazy health hacks so much fun", "multimedia": None},
                {"autor": "Ella", "texto": "pretty neat what you into all that", "multimedia": None},
                {"autor": "El", "texto": "my first step was tim ferriss of all people i'm into the breathing and ice into the breathing and ice work stuff or health in general well the health stuff in general but i meant the more unusual end of things like the breath work and i stuff i've been in the industry for six years so it's all been kind of just been organic i find i found breath work when i was researching techniques for stress management for clients", "multimedia": None},
                {"autor": "Ella", "texto": "russell brand did an interview with vim hoff and i went down deep the breath work rabbit hole and now i'm friends with a crazy bunch of wim hof method instructors so we're always doing crazy things", "multimedia": None},
                {"autor": "El", "texto": "that sounds fun i always end up way too far down different rabbit holes it's the only real way to have adventures right what health work do you do", "multimedia": None},
                {"autor": "Ella", "texto": "absolutely i run an online fitness and mindset coaching business", "multimedia": None},
                {"autor": "El", "texto": "nice how long have you done that", "multimedia": None},
                {"autor": "Ella", "texto": "i have two companies in sydney a business coaching business and a dating and relationship coaching business over six years now took it online the start of the year", "multimedia": None},
                {"autor": "El", "texto": "awesome how involved are you in the coaching side", "multimedia": None},
                {"autor": "Ella", "texto": "well in the beginning i was the only staff so i did all the coaching now i don't do any of the coaching although looking to start a new shadow work and dark sexual energy programs so i'll start coaching that again", "multimedia": None},
                {"autor": "Ella", "texto": "love it let's go for a beach walk sometime i feel we would have much to connect over always enjoy speaking with people in the coaching space i assume we have multiple mutual friends too", "multimedia": None}
            ]
        },
        {
            "plataforma": "Tinder (Conversación 3)",
            "mensajes": [
                {"autor": "El", "texto": "hey great to meet another non-coffee drinker you want to hear something even more crazy i don't drink alcohol either", "multimedia": None},
                {"autor": "Ella", "texto": "hey damian it's great to meet you too i'm the same i don't drink alcohol i just love the energy and mental clarity i have without caffeine alcohol how's your day been", "multimedia": None},
                {"autor": "El", "texto": "my day's been pretty great finished a bit early today so watching sunset on the beach with a puppy which is a nice way to finish after a day full of zoom conferences did you grow up here on the gold coast", "multimedia": None},
                {"autor": "Ella", "texto": "yeah beach definitely sounds relaxing i've lived in sydney for nine years before moving to gold coast here been here in five years now", "multimedia": None},
                {"autor": "El", "texto": "oh wow where in sydney and where did you live before that", "multimedia": None},
                {"autor": "Ella", "texto": "i've lived in crow's nest and cameron sydney i moved to australia when i was 26 from indian himalayan town where i was born how about you", "multimedia": None},
                {"autor": "El", "texto": "ha i lived in camaray for a while then neutral bay then north sydney sydney has its charm but i'm honestly not in any rush to go back people are so much happier here my hairdresser in sydney was from nepal which i'm guessing is closest close-ish to indi india himalayas", "multimedia": None},
                {"autor": "Ella", "texto": "yeah sydney used to be really nice i have so many good memories of sydney it was my first experience living in a big city i really enjoyed it until i it got expensive and crowded yes indian himalayas are close to nepal in fact shimla the town i come from was a huge nepalese population very beautiful town if you like snow", "multimedia": None},
                {"autor": "El", "texto": "i bet it is for all my traveling there's still so much of the world left to see i think the lifestyle here is great people move here to be happy you know", "multimedia": None},
                {"autor": "Ella", "texto": "yeah i like it here nature especially people here don't stress as much which is great i'm guessing you adapted well to the culture here i'm guessing it's very different to back home and evidently you like it here in australia or you're a glutton for punishment", "multimedia": None},
                {"autor": "El", "texto": "yeah i was always the black sheep of the family i like doing my own thing instead of following the norm i've adapted to all the good things about the culture here yes i wouldn't live anywhere else australians have been very nice to me here always", "multimedia": None},
                {"autor": "Ella", "texto": "that's great i've heard some foreigners say people hear racist others have had a great experience i think it probably has something to do with how much you adapt to the culture perhaps i personally haven't experienced racism maybe because of my long blonde hair i think as long as i don't marry a white man no one would frown at what i'm doing", "multimedia": None},
                {"autor": "El", "texto": "your family wants you to marry a nice indian man", "multimedia": None},
                {"autor": "Ella", "texto": "no not really they gave up on me long ago they know i'll do the opposite of what they say", "multimedia": None},
                {"autor": "El", "texto": "poor family it's funny your family wants you marrying an indian man mine wanted me to marry a blonde head blue-eyed girl neither family will get what they want the irony i don't know your taste in men but my poor parents", "multimedia": None},
                {"autor": "Ella", "texto": "i like dark features i like masculine men with nice features", "multimedia": None},
                {"autor": "El", "texto": "quickly checks his own features haha", "multimedia": None},
                {"autor": "Ella", "texto": "you look good i think we should try meat for a drink sometime what do you say oh and thank you", "multimedia": None},
                {"autor": "El", "texto": "i think on an app like tinder the only thing you really have to go on when swiping is a person's features lol", "multimedia": None},
                {"autor": "Ella", "texto": "you are welcome yes that's all that's all it's about we should meet up for sure that'd be nice are you free saturday evening by chance", "multimedia": None},
                {"autor": "El", "texto": "yeah i think i am cool maybe we could meet around eight or so what part of gold coast is home for you we can try to find somewhere central", "multimedia": None},
                {"autor": "Ella", "texto": "yeah okay i'm at southport i don't drive so here so yeah", "multimedia": None}
            ]
        }
    ]
}

os.makedirs('parsed_cases', exist_ok=True)
with open('parsed_cases/HU6AdwK_rnk.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved to parsed_cases/HU6AdwK_rnk.json")
