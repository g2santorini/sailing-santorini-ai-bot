def get_text(key: str, language: str, booking_link: str, whatsapp_link: str) -> str:
    translations = {
        "empty_reply": {
            "en": "Hello! I’ll be happy to help you with our cruises in Santorini.",
            "el": "Γεια σας! Θα χαρώ να σας βοηθήσω με τις κρουαζιέρες μας στη Σαντορίνη.",
            "it": "Ciao! Sarò felice di aiutarti con le nostre crociere a Santorini.",
            "pt": "Olá! Terei todo o gosto em ajudar com os nossos cruzeiros em Santorini.",
        },
        "greeting_reply": {
            "en": "Hello and welcome! I’ll be happy to help you with our cruises in Santorini. Feel free to ask me about availability, prices, shared or private options.",
            "el": "Γεια σας και καλώς ήρθατε! Θα χαρώ να σας βοηθήσω με τις κρουαζιέρες μας στη Σαντορίνη. Μπορείτε να με ρωτήσετε για διαθεσιμότητα, τιμές, κοινές ή ιδιωτικές επιλογές.",
            "it": "Ciao e benvenuto! Sarò felice di aiutarti con le nostre crociere a Santorini. Puoi chiedermi disponibilità, prezzi e opzioni condivise o private.",
            "pt": "Olá e bem-vindo! Terei todo o gosto em ajudar com os nossos cruzeiros em Santorini. Pode perguntar sobre disponibilidade, preços e opções partilhadas ou privadas.",
        },
        "discount_reply": {
            "en": f"For special rate requests, please contact us via WhatsApp: {whatsapp_link}",
            "el": f"Για ειδικά αιτήματα τιμών, παρακαλούμε επικοινωνήστε μαζί μας μέσω WhatsApp: {whatsapp_link}",
            "it": f"Per richieste di tariffe speciali, ti preghiamo di contattarci via WhatsApp: {whatsapp_link}",
            "pt": f"Para pedidos de tarifas especiais, por favor contacte-nos via WhatsApp: {whatsapp_link}",
        },
        "cruise_passenger_reply": {
            "en": f"For cruise ship guests, we kindly recommend contacting us directly via WhatsApp so we can assist you based on your ship schedule:\n{whatsapp_link}",
            "el": f"Για επισκέπτες κρουαζιερόπλοιου, σας προτείνουμε να επικοινωνήσετε απευθείας μαζί μας μέσω WhatsApp, ώστε να σας βοηθήσουμε βάσει του προγράμματος του πλοίου σας:\n{whatsapp_link}",
            "it": f"Per gli ospiti delle navi da crociera, consigliamo gentilmente di contattarci direttamente via WhatsApp così potremo assistervi in base all’orario della vostra nave:\n{whatsapp_link}",
            "pt": f"Para passageiros de cruzeiro, recomendamos gentilmente que nos contacte diretamente via WhatsApp para que possamos ajudar de acordo com o horário do seu navio:\n{whatsapp_link}",
        },
        "contact_reply": {
            "en": f"You can contact our reservations team directly on WhatsApp and we’ll be happy to assist you:\n{whatsapp_link}",
            "el": f"Μπορείτε να επικοινωνήσετε απευθείας με το τμήμα κρατήσεων μέσω WhatsApp και θα χαρούμε να σας εξυπηρετήσουμε:\n{whatsapp_link}",
            "it": f"Puoi contattare direttamente il nostro team prenotazioni su WhatsApp e saremo felici di aiutarti:\n{whatsapp_link}",
            "pt": f"Pode contactar diretamente a nossa equipa de reservas via WhatsApp e teremos todo o gosto em ajudar:\n{whatsapp_link}",
        },
        "irrelevant_reply": {
            "en": "I may not have fully understood your question, but I’ll be happy to help 🙂\n\nCould you please clarify if you are asking about the cruise experience?",
            "el": "Ίσως δεν κατάλαβα πλήρως την ερώτησή σας, αλλά θα χαρώ να βοηθήσω 🙂\n\nΜπορείτε να διευκρινίσετε αν αφορά την εμπειρία της κρουαζιέρας;",
            "it": "Potrei non aver compreso completamente la tua domanda, ma sarò felice di aiutarti 🙂\n\nPuoi chiarire se riguarda l’esperienza della crociera?",
            "pt": "Talvez eu não tenha compreendido totalmente a sua pergunta, mas terei todo o gosto em ajudar 🙂\n\nPode esclarecer se se refere à experiência do cruzeiro?",
        },
        "availability_fallback": {
            "en": f"The best way to check the latest availability is through our booking page:\n{booking_link}\n\nSimply select your preferred date and you’ll see all available options instantly.\n\nFor any clarification, feel free to contact us on WhatsApp:\n{whatsapp_link}",
            "el": f"Ο καλύτερος τρόπος για να δείτε την πιο πρόσφατη διαθεσιμότητα είναι μέσω της σελίδας κρατήσεών μας:\n{booking_link}\n\nΑπλώς επιλέξτε την ημερομηνία που προτιμάτε και θα δείτε άμεσα όλες τις διαθέσιμες επιλογές.\n\nΓια οποιαδήποτε διευκρίνιση, μπορείτε να επικοινωνήσετε μαζί μας στο WhatsApp:\n{whatsapp_link}",
            "it": f"Il modo migliore per controllare la disponibilità più aggiornata è tramite la nostra pagina di prenotazione:\n{booking_link}\n\nTi basta selezionare la data che preferisci e vedrai subito tutte le opzioni disponibili.\n\nPer qualsiasi chiarimento, puoi contattarci su WhatsApp:\n{whatsapp_link}",
            "pt": f"A melhor forma de verificar a disponibilidade mais atualizada é através da nossa página de reservas:\n{booking_link}\n\nBasta selecionar a data pretendida e verá imediatamente todas as opções disponíveis.\n\nPara qualquer esclarecimento, contacte-nos via WhatsApp:\n{whatsapp_link}",
        },
        "spots_fallback": {
            "en": "I’m sorry, I could not identify the exact cruise from the previous message. Please tell me the cruise name and date, and I’ll gladly check the number of available spots for you.",
            "el": "Λυπάμαι, δεν μπόρεσα να εντοπίσω ακριβώς ποια κρουαζιέρα εννοείτε από το προηγούμενο μήνυμα. Πείτε μου το όνομα της κρουαζιέρας και την ημερομηνία και θα ελέγξω ευχαρίστως τις διαθέσιμες θέσεις.",
            "it": "Mi dispiace, non sono riuscito a identificare con precisione la crociera dal messaggio precedente. Indicami il nome della crociera e la data e controllerò con piacere i posti disponibili.",
            "pt": "Lamento, não consegui identificar exatamente o cruzeiro a partir da mensagem anterior. Diga-me o nome do cruzeiro e a data e verificarei com todo o gosto os lugares disponíveis.",
        },
        "booking_details_reply": {
            "en": f"I can’t see personal booking details here. Please check your booking confirmation, or contact us on WhatsApp and we’ll gladly assist you directly:\n{whatsapp_link}",
            "el": f"Δεν μπορώ να δω προσωπικά στοιχεία κράτησης εδώ. Παρακαλούμε ελέγξτε την επιβεβαίωση της κράτησής σας ή επικοινωνήστε μαζί μας στο WhatsApp και θα χαρούμε να σας εξυπηρετήσουμε:\n{whatsapp_link}",
            "it": f"Non posso vedere qui i dettagli personali della prenotazione. Ti preghiamo di controllare la conferma della prenotazione oppure di contattarci su WhatsApp e saremo lieti di aiutarti:\n{whatsapp_link}",
            "pt": f"Não consigo ver aqui os dados pessoais da reserva. Por favor consulte a confirmação da sua reserva ou contacte-nos via WhatsApp e teremos todo o gosto em ajudar:\n{whatsapp_link}",
        },
        "whatsapp_uncertain_reply": {
            "en": f"I don’t have that exact detail here, but our team can assist you directly on WhatsApp:\n{whatsapp_link}",
            "el": f"Δεν έχω αυτή την ακριβή πληροφορία εδώ, αλλά η ομάδα μας μπορεί να σας βοηθήσει απευθείας στο WhatsApp:\n{whatsapp_link}",
            "it": f"Non ho qui questo dettaglio preciso, ma il nostro team può aiutarti direttamente su WhatsApp:\n{whatsapp_link}",
            "pt": f"Não tenho aqui esse detalhe exato, mas a nossa equipa pode ajudar diretamente via WhatsApp:\n{whatsapp_link}",
        },
        "morning_unavailable_reply": {
            "en": f"Morning cruises are available only until 24 October 2026, so the requested morning cruise is not available on that date.\n\nDuring that period, only sunset cruises are operating.\n\nYou can check availability here:\n{booking_link}\n\nFor any clarification, feel free to contact us on WhatsApp:\n{whatsapp_link}",
            "el": f"Οι πρωινές κρουαζιέρες είναι διαθέσιμες μόνο έως τις 24 Οκτωβρίου 2026, επομένως η ζητούμενη πρωινή κρουαζιέρα δεν είναι διαθέσιμη για εκείνη την ημερομηνία.\n\nΚατά την περίοδο αυτή πραγματοποιούνται μόνο απογευματινές κρουαζιέρες ηλιοβασιλέματος.\n\nΜπορείτε να δείτε τη διαθεσιμότητα εδώ:\n{booking_link}\n\nΓια οποιαδήποτε διευκρίνιση, επικοινωνήστε μαζί μας στο WhatsApp:\n{whatsapp_link}",
            "it": f"Le crociere mattutine sono disponibili solo fino al 24 ottobre 2026, quindi la crociera mattutina richiesta non è disponibile in quella data.\n\nDurante quel periodo operano solo le crociere al tramonto.\n\nPuoi controllare la disponibilità qui:\n{booking_link}\n\nPer qualsiasi chiarimento, puoi contattarci su WhatsApp:\n{whatsapp_link}",
            "pt": f"Os cruzeiros da manhã estão disponíveis apenas até 24 de outubro de 2026, por isso o cruzeiro da manhã solicitado não está disponível nessa data.\n\nDurante esse período operam apenas os cruzeiros ao pôr do sol.\n\nPode verificar a disponibilidade aqui:\n{booking_link}\n\nPara qualquer esclarecimento, contacte-nos via WhatsApp:\n{whatsapp_link}",
        },
        "sunset_only_reply": {
            "en": f"During that period, we operate sunset cruises only.\n\nThe sunset cruise is a beautiful experience, as you can enjoy the famous Santorini sunset from the sea.\n\nYou can check availability here:\n{booking_link}\n\nIf you need help choosing, feel free to contact us on WhatsApp:\n{whatsapp_link}",
            "el": f"Κατά την περίοδο αυτή πραγματοποιούνται μόνο απογευματινές κρουαζιέρες ηλιοβασιλέματος.\n\nΗ απογευματινή κρουαζιέρα είναι μια όμορφη εμπειρία, καθώς μπορείτε να απολαύσετε το διάσημο ηλιοβασίλεμα της Σαντορίνης από τη θάλασσα.\n\nΜπορείτε να δείτε τη διαθεσιμότητα εδώ:\n{booking_link}\n\nΑν χρειάζεστε βοήθεια για να επιλέξετε, επικοινωνήστε μαζί μας στο WhatsApp:\n{whatsapp_link}",
            "it": f"Durante quel periodo operano solo le crociere al tramonto.\n\nLa crociera al tramonto è una bellissima esperienza, perché permette di ammirare il famoso tramonto di Santorini dal mare.\n\nPuoi controllare la disponibilità qui:\n{booking_link}\n\nSe hai bisogno di aiuto nella scelta, puoi contattarci su WhatsApp:\n{whatsapp_link}",
            "pt": f"Durante esse período operam apenas os cruzeiros ao pôr do sol.\n\nO cruzeiro ao pôr do sol é uma experiência muito bonita, pois permite apreciar o famoso pôr do sol de Santorini a partir do mar.\n\nPode verificar a disponibilidade aqui:\n{booking_link}\n\nSe precisar de ajuda para escolher, contacte-nos via WhatsApp:\n{whatsapp_link}",
        },
        "off_season_reply": {
            "en": f"Our cruises are not operating during that period, as the season is closed.\n\nWe resume from 15 March 2027.\n\nYou can check available dates here:\n{booking_link}\n\nFor any clarification, feel free to contact us on WhatsApp:\n{whatsapp_link}",
            "el": f"Οι κρουαζιέρες μας δεν πραγματοποιούνται κατά την περίοδο αυτή, καθώς η σεζόν είναι κλειστή.\n\nΞεκινάμε ξανά από τις 15 Μαρτίου 2027.\n\nΜπορείτε να δείτε τις διαθέσιμες ημερομηνίες εδώ:\n{booking_link}\n\nΓια οποιαδήποτε διευκρίνιση, επικοινωνήστε μαζί μας στο WhatsApp:\n{whatsapp_link}",
            "it": f"Le nostre crociere non operano in quel periodo, poiché la stagione è chiusa.\n\nRiprendiamo dal 15 marzo 2027.\n\nPuoi controllare le date disponibili qui:\n{booking_link}\n\nPer qualsiasi chiarimento, puoi contattarci su WhatsApp:\n{whatsapp_link}",
            "pt": f"Os nossos cruzeiros não operam durante esse período, pois a temporada está encerrada.\n\nRetomamos a partir de 15 de março de 2027.\n\nPode verificar as datas disponíveis aqui:\n{booking_link}\n\nPara qualquer esclarecimento, contacte-nos via WhatsApp:\n{whatsapp_link}",
        },
        "sunset_reply": {
            "en": "Yes, you will enjoy the sunset from onboard the catamaran. Our sunset cruises are timed so you can watch the famous Santorini sunset directly from the sea.",
            "el": "Ναι, θα απολαύσετε το ηλιοβασίλεμα πάνω στο καταμαράν. Οι απογευματινές μας κρουαζιέρες είναι προγραμματισμένες ώστε να βλέπετε το διάσημο ηλιοβασίλεμα της Σαντορίνης απευθείας από τη θάλασσα.",
            "it": "Sì, potrete godervi il tramonto direttamente a bordo del catamarano. Le nostre crociere al tramonto sono programmate per permettervi di ammirare il famoso tramonto di Santorini dal mare.",
            "pt": "Sim, irá desfrutar do pôr do sol a bordo do catamarã. Os nossos cruzeiros ao pôr do sol são programados para que possa apreciar o famoso pôr do sol de Santorini a partir do mar.",
        },
        "weather_reply": {
            "en": "Weather conditions can change quickly in Santorini 🙂 Our cruises take place inside the caldera, where the sea is usually quite calm. In case of unsafe conditions, cruises are cancelled only under official Port Authority instructions, and guests are offered a reschedule or full refund.",
            "el": "Οι καιρικές συνθήκες στη Σαντορίνη μπορούν να αλλάξουν γρήγορα 🙂 Οι κρουαζιέρες μας πραγματοποιούνται μέσα στην καλντέρα, όπου η θάλασσα είναι συνήθως αρκετά ήρεμη. Σε περίπτωση μη ασφαλών συνθηκών, οι κρουαζιέρες ακυρώνονται μόνο κατόπιν επίσημων οδηγιών του Λιμεναρχείου και προσφέρεται αλλαγή ημερομηνίας ή πλήρης επιστροφή χρημάτων.",
            "it": "Le condizioni meteo a Santorini possono cambiare rapidamente 🙂 Le nostre crociere si svolgono all’interno della caldera, dove il mare è di solito piuttosto calmo. In caso di condizioni non sicure, le crociere vengono cancellate solo su indicazione ufficiale dell’Autorità Portuale e viene offerta una riprogrammazione o un rimborso completo.",
            "pt": "As condições meteorológicas em Santorini podem mudar rapidamente 🙂 Os nossos cruzeiros decorrem dentro da caldeira, onde o mar costuma ser bastante calmo. Em caso de condições inseguras, os cruzeiros são cancelados apenas por instruções oficiais da Autoridade Portuária, sendo oferecida remarcação ou reembolso total.",
        },
        "food_reply": {
            "en": "A freshly prepared BBQ meal is included on all cruises. Vegetarian options are also available.",
            "el": "Σε όλες τις κρουαζιέρες περιλαμβάνεται φρεσκομαγειρεμένο γεύμα BBQ. Υπάρχουν επίσης διαθέσιμες χορτοφαγικές επιλογές.",
            "it": "Su tutte le crociere è incluso un pasto BBQ preparato al momento. Sono disponibili anche opzioni vegetariane.",
            "pt": "Em todos os cruzeiros está incluída uma refeição BBQ preparada na hora. Também existem opções vegetarianas disponíveis.",
        },
        "drinks_reply": {
            "en": "Complimentary drinks are included on board, such as white wine, soft drinks and water. Beer is included in selected cruises, and Diamond also includes one cocktail per guest.",
            "el": "Στο σκάφος περιλαμβάνονται δωρεάν ποτά, όπως λευκό κρασί, αναψυκτικά και νερό. Μπύρα περιλαμβάνεται σε επιλεγμένες κρουαζιέρες, ενώ στο Diamond περιλαμβάνεται και ένα cocktail ανά άτομο.",
            "it": "A bordo sono incluse bevande gratuite come vino bianco, bibite e acqua. La birra è inclusa in alcune crociere selezionate, mentre Diamond include anche un cocktail per ospite.",
            "pt": "As bebidas incluídas a bordo são vinho branco, refrigerantes e água. A cerveja está incluída em alguns cruzeiros selecionados, e o Diamond inclui também um cocktail por pessoa.",
        },
        "transfer_reply": {
            "en": "Transfers are included in most cruise options, except for no-transfer options. If you tell me which cruise you are interested in, I can guide you more precisely.",
            "el": "Οι μεταφορές περιλαμβάνονται στις περισσότερες επιλογές κρουαζιέρας, εκτός από τις επιλογές χωρίς μεταφορά. Αν μου πείτε ποια κρουαζιέρα σας ενδιαφέρει, μπορώ να σας καθοδηγήσω πιο συγκεκριμένα.",
            "it": "I trasferimenti sono inclusi nella maggior parte delle opzioni, tranne nelle opzioni senza transfer. Se mi dici quale crociera ti interessa, posso guidarti in modo più preciso.",
            "pt": "Os transfers estão incluídos na maioria das opções de cruzeiro, exceto nas opções sem transfer. Se me disser em que cruzeiro tem interesse, posso orientá-lo com mais precisão.",
        },
        "route_reply": {
            "en": "Our cruises usually include stops for swimming, snorkeling and sightseeing around the Santorini caldera. Exact stops may vary depending on weather conditions.",
            "el": "Οι κρουαζιέρες μας συνήθως περιλαμβάνουν στάσεις για κολύμπι, snorkeling και sightseeing γύρω από την καλντέρα της Σαντορίνης. Οι ακριβείς στάσεις μπορεί να διαφέρουν ανάλογα με τις καιρικές συνθήκες.",
            "it": "Le nostre crociere includono di solito soste per nuotare, fare snorkeling e ammirare i luoghi più belli della caldera di Santorini. Le soste esatte possono variare a seconda delle condizioni meteo.",
            "pt": "Os nossos cruzeiros incluem normalmente paragens para nadar, fazer snorkeling e apreciar os pontos mais bonitos da caldeira de Santorini. As paragens exatas podem variar consoante as condições meteorológicas.",
        },
    }

    return translations.get(key, {}).get(
        language,
        translations.get(key, {}).get("en", "")
    )


def translate_availability_reply(reply_text: str, language: str) -> str:
    if language == "en":
        return reply_text

    replacements = {
        "el": [
            ("Thank you for your message.", "Σας ευχαριστούμε για το μήνυμά σας."),
            (
                "Unfortunately, we do not currently have any",
                "Δυστυχώς, δεν έχουμε αυτή τη στιγμή",
            ),
            ("cruises available for", "διαθέσιμες κρουαζιέρες για"),
            ("available for", "διαθέσιμες για"),
            (
                "You may check other dates here:",
                "Μπορείτε να δείτε άλλες ημερομηνίες εδώ:",
            ),
            ("For ", "Για "),
            ("the following private", "τις παρακάτω ιδιωτικές"),
            ("the following shared", "τις παρακάτω κοινές"),
            ("the following", "τις παρακάτω"),
            (
                "private cruises are available:",
                "ιδιωτικές κρουαζιέρες είναι διαθέσιμες:",
            ),
            ("shared cruises are available:", "κοινές κρουαζιέρες είναι διαθέσιμες:"),
            ("cruises are available:", "κρουαζιέρες είναι διαθέσιμες:"),
            (" is available.", " είναι διαθέσιμη."),
            (" are available.", " είναι διαθέσιμες."),
            ("Shared cruises:", "Κοινές κρουαζιέρες:"),
            ("Private cruises:", "Ιδιωτικές κρουαζιέρες:"),
            (
                "You can proceed directly with your booking here:",
                "Μπορείτε να προχωρήσετε απευθείας στην κράτησή σας εδώ:",
            ),
            (
                "You may proceed with your booking here:",
                "Μπορείτε να προχωρήσετε στην κράτησή σας εδώ:",
            ),
            (
                "Please select the date on the booking page.",
                "Παρακαλούμε επιλέξτε την ημερομηνία στη σελίδα κράτησης.",
            ),
            ("morning", "πρωινές"),
            ("sunset", "απογευματινές"),
        ],
        "it": [
            ("Thank you for your message.", "Grazie per il tuo messaggio."),
            (
                "Unfortunately, we do not currently have any",
                "Purtroppo al momento non abbiamo",
            ),
            ("cruises available for", "crociere disponibili per"),
            ("available for", "disponibili per"),
            ("You may check other dates here:", "Puoi controllare altre date qui:"),
            ("For ", "Per il "),
            ("the following private", "le seguenti private"),
            ("the following shared", "le seguenti condivise"),
            ("the following", "le seguenti"),
            ("private cruises are available:", "crociere private disponibili:"),
            ("shared cruises are available:", "crociere condivise disponibili:"),
            ("cruises are available:", "crociere disponibili:"),
            (" is available.", " è disponibile."),
            (" are available.", " sono disponibili."),
            ("Shared cruises:", "Crociere condivise:"),
            ("Private cruises:", "Crociere private:"),
            (
                "You can proceed directly with your booking here:",
                "Puoi procedere direttamente con la prenotazione qui:",
            ),
            (
                "You may proceed with your booking here:",
                "Puoi procedere con la prenotazione qui:",
            ),
            (
                "Please select the date on the booking page.",
                "Ti preghiamo di selezionare la data nella pagina di prenotazione.",
            ),
        ],
        "pt": [
            ("Thank you for your message.", "Obrigado pela sua mensagem."),
            (
                "Unfortunately, we do not currently have any",
                "Infelizmente, neste momento não temos",
            ),
            ("cruises available for", "cruzeiros disponíveis para"),
            ("available for", "disponíveis para"),
            ("You may check other dates here:", "Pode verificar outras datas aqui:"),
            ("For ", "Para "),
            ("the following private", "os seguintes privados"),
            ("the following shared", "os seguintes partilhados"),
            ("the following", "os seguintes"),
            ("private cruises are available:", "cruzeiros privados disponíveis:"),
            ("shared cruises are available:", "cruzeiros partilhados disponíveis:"),
            ("cruises are available:", "cruzeiros disponíveis:"),
            (" is available.", " está disponível."),
            (" are available.", " estão disponíveis."),
            ("Shared cruises:", "Cruzeiros partilhados:"),
            ("Private cruises:", "Cruzeiros privados:"),
            (
                "You can proceed directly with your booking here:",
                "Pode avançar diretamente com a sua reserva aqui:",
            ),
            (
                "You may proceed with your booking here:",
                "Pode avançar com a sua reserva aqui:",
            ),
            (
                "Please select the date on the booking page.",
                "Por favor selecione a data na página de reservas.",
            ),
        ],
    }

    translated = reply_text
    for source, target in replacements.get(language, []):
        translated = translated.replace(source, target)

    return translated