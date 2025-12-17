def player(prev_play, state={
    # Tilstand som lever videre mellom kall til player()
    "round": 0,             # Hvilken runde vi er i
    "opp": [],              # Historikk over motstanderens trekk
    "me": [],               # Historikk over våre egne trekk
    "pred_last": {},        # Hva vi predikerte at motstanderen ville spille forrige runde
    "score": {              # Hvor godt hver hypotese (bot) har truffet
        "quincy": [0, 0],   # [antall treff, antall forsøk]
        "kris":   [0, 0],
        "mrugesh":[0, 0],
        "abbey":  [0, 0],
    }
}):
    # ------------------------------------------------------------
    # HJELPEFUNKSJONER
    # ------------------------------------------------------------

    # Hvilket trekk slår hvilket
    beat = {"R": "P", "P": "S", "S": "R"}

    def dbl(x):
        """
        Returnerer trekket som slår trekket som slår x.
        Brukes for å 'overliste' Abbey, som selv spiller et mot-trekk.
        """
        return beat[beat[x]]

    # ------------------------------------------------------------
    # RESET – kjøres ved starten av en ny kamp
    # ------------------------------------------------------------

    if prev_play == "":
        # Nullstill all tilstand
        state["round"] = 0
        state["opp"].clear()
        state["me"].clear()
        state["pred_last"].clear()

        # Nullstill treffsikkerheten til alle hypoteser
        for k in state["score"]:
            state["score"][k][0] = 0
            state["score"][k][1] = 0

        # Åpningstrekk er ikke kritisk
        return "R"

    # ------------------------------------------------------------
    # OPPDATER HISTORIKK OG SCORE
    # ------------------------------------------------------------

    # Logg motstanderens forrige trekk
    state["round"] += 1
    state["opp"].append(prev_play)

    # Sjekk hvor gode prediksjonene våre var forrige runde
    for bot, (m, t) in state["score"].items():
        if bot in state["pred_last"]:
            state["score"][bot][1] += 1        # Øk antall forsøk
            if state["pred_last"][bot] == prev_play:
                state["score"][bot][0] += 1    # Øk treff

    # ------------------------------------------------------------
    # GENERER PREDIKSJONER FOR HVER BOT
    # ------------------------------------------------------------

    # 1) Quincy
    # Quincy spiller et fast mønster:
    # R, P, P, S, R  (periodisk med lengde 5)
    quincy_cycle = ["R", "P", "P", "S", "R"]
    pred_quincy = quincy_cycle[len(state["opp"]) % 5]

    # 2) Kris
    # Kris spiller alltid trekket som slår vårt forrige trekk
    if state["me"]:
        pred_kris = beat[state["me"][-1]]
    else:
        # Første runde antar Kris at vi spilte "R"
        pred_kris = beat["R"]

    # 3) Mrugesh
    # Mrugesh ser på våre siste 10 trekk og slår det mest brukte
    # Han har et tomt trekk "" i starten av historikken
    mr_hist = [""] + state["me"]
    last_ten = mr_hist[-10:]

    # Tell forekomster og bryt likt deterministisk
    counts = {c: last_ten.count(c) for c in ["R", "P", "S", ""]}
    most_freq = max(
        counts,
        key=lambda k: (counts[k], {"R": 3, "P": 2, "S": 1, "": 0}[k])
    )

    # Tom streng behandles som "S"
    if most_freq == "":
        most_freq = "S"

    pred_mrugesh = beat[most_freq]

    # 4) Abbey
    # Abbey prøver å predikere vårt neste trekk basert på overgangssannsynligheter
    # Deretter spiller hun trekket som slår vår predikerte neste move

    # Abbey starter med å anta at vårt første trekk var "R"
    abb_hist = ["R"] + state["me"]

    # Tell overganger mellom trekk (RR, RP, RS, osv.)
    trans = {
        "RR": 0, "RP": 0, "RS": 0,
        "PR": 0, "PP": 0, "PS": 0,
        "SR": 0, "SP": 0, "SS": 0,
    }

    for a, b in zip(abb_hist[:-1], abb_hist[1:]):
        trans[a + b] += 1

    # Abbey antar at vårt neste trekk følger det mest vanlige mønsteret
    last = abb_hist[-1]
    cand = [last + "R", last + "P", last + "S"]

    # Tie-break: R > P > S (matcher Abbey sin implementasjon)
    pred_my_move = max(cand, key=lambda k: trans[k])[-1]
    pred_abbey = beat[pred_my_move]

    # Lagre prediksjoner for bruk i neste runde
    state["pred_last"] = {
        "quincy": pred_quincy,
        "kris": pred_kris,
        "mrugesh": pred_mrugesh,
        "abbey": pred_abbey,
    }

    # ------------------------------------------------------------
    # IDENTIFISER HVILKEN BOT VI SPILLER MOT
    # ------------------------------------------------------------

    def acc(bot):
        """
        Returnerer treffsikkerheten til en hypotese.
        """
        m, t = state["score"][bot]
        return (m / t) if t else 0.0

    # Prioritert rekkefølge ved lik score
    bot_order = ["kris", "quincy", "mrugesh", "abbey"]
    best_bot = max(bot_order, key=acc)
    best_acc = acc(best_bot)

    # ------------------------------------------------------------
    # VELG TREKK
    # ------------------------------------------------------------

    # Hvis vi er tidlig i kampen eller usikre:
    # spill et robust anti-Abbey-trekk
    if state["round"] < 6 or best_acc < 0.65:
        move = dbl(pred_my_move)
    else:
        # Når vi er sikre: spill eksplisitt mot beste hypotese
        if best_bot == "quincy":
            move = beat[pred_quincy]
        elif best_bot == "kris":
            move = beat[pred_kris]
        elif best_bot == "mrugesh":
            move = beat[pred_mrugesh]
        else:  # abbey
            move = dbl(pred_my_move)

    # Logg vårt eget trekk og returner det
    state["me"].append(move)
    return move
