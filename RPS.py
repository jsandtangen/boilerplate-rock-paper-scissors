
def player(prev_play, state={
    "round": 0,
    "opp": [],
    "me": [],
    "pred_last": {},         # what we predicted opponent would play last round
    "score": {               # hypothesis match counts
        "quincy": [0, 0],    # [matches, total]
        "kris":   [0, 0],
        "mrugesh":[0, 0],
        "abbey":  [0, 0],
    }
}):
    # Helpers
    beat = {"R": "P", "P": "S", "S": "R"}  # move that beats key
    def dbl(x):  # beats the move that beats x
        return beat[beat[x]]

    # Reset at start of each match
    if prev_play == "":
        state["round"] = 0
        state["opp"].clear()
        state["me"].clear()
        state["pred_last"].clear()
        for k in state["score"]:
            state["score"][k][0] = 0
            state["score"][k][1] = 0
        # Any opener is fine; this works well with our predictors
        return "R"

    # Record opponent last move
    state["round"] += 1
    state["opp"].append(prev_play)

    # Update hypothesis scores by comparing last-round prediction vs actual
    for bot, (m, t) in state["score"].items():
        if bot in state["pred_last"]:
            state["score"][bot][1] += 1
            if state["pred_last"][bot] == prev_play:
                state["score"][bot][0] += 1

    # --- Predict opponent's NEXT move under each bot hypothesis ---

    # 1) Quincy: fixed cycle due to internal counter implementation
    # Sequence is: R, P, P, S, R, R, P, P, S, R, ... (period 5: "RPPSR")
    quincy_cycle = ["R", "P", "P", "S", "R"]
    pred_quincy = quincy_cycle[len(state["opp"]) % 5]

    # 2) Kris: plays the move that beats OUR previous move
    if state["me"]:
        pred_kris = beat[state["me"][-1]]
    else:
        pred_kris = beat["R"]  # kris treats '' as 'R' on its first call

    # 3) Mrugesh: counters our most frequent move in the last 10 (with ''->"S")
    # He has an initial '' in history (first call), so include that.
    mr_hist = [""] + state["me"]
    last_ten = mr_hist[-10:]
    # Avoid tie weirdness by deterministic tie-break (R > P > S > '')
    counts = {c: last_ten.count(c) for c in ["R", "P", "S", ""]}
    most_freq = max(counts, key=lambda k: (counts[k], {"R":3, "P":2, "S":1, "":0}[k]))
    if most_freq == "":
        most_freq = "S"
    pred_mrugesh = beat[most_freq]

    # 4) Abbey: predicts our next from transition counts, then counters prediction
    # Abbey treats first prev_opponent_play '' as 'R', and seeds history with that.
    # Build transition counts from our played moves, with a starting 'R'.
    abb_hist = ["R"] + state["me"]
    trans = {
        "RR": 0, "RP": 0, "RS": 0,
        "PR": 0, "PP": 0, "PS": 0,
        "SR": 0, "SP": 0, "SS": 0,
    }
    for a, b in zip(abb_hist[:-1], abb_hist[1:]):
        trans[a + b] += 1

    last = abb_hist[-1]  # Abbey's prev_opponent_play at next call
    cand = [last + "R", last + "P", last + "S"]
    # Tie-break matches Abbey: order R, then P, then S
    pred_my_move = max(cand, key=lambda k: trans[k])[-1]
    pred_abbey = beat[pred_my_move]

    # Store predictions for scoring on next call
    state["pred_last"] = {
        "quincy": pred_quincy,
        "kris": pred_kris,
        "mrugesh": pred_mrugesh,
        "abbey": pred_abbey,
    }

    # --- Identify bot (pick hypothesis with best recent accuracy) ---
    def acc(bot):
        m, t = state["score"][bot]
        return (m / t) if t else 0.0

    # After a few rounds, the correct bot stands out strongly.
    # Prefer "kris" early if it matches, because it's extremely distinctive.
    bot_order = ["kris", "quincy", "mrugesh", "abbey"]
    best_bot = max(bot_order, key=acc)
    best_acc = acc(best_bot)

    # If we’re not confident yet, use a robust default that crushes Abbey
    # and does fine while we collect evidence.
    if state["round"] < 6 or best_acc < 0.65:
        move = dbl(pred_my_move)  # anti-Abbey move (beats Abbey's counter)
    else:
        if best_bot == "quincy":
            move = beat[pred_quincy]
        elif best_bot == "kris":
            move = beat[pred_kris]  # beats Kris's response
        elif best_bot == "mrugesh":
            move = beat[pred_mrugesh]
        else:  # abbey
            move = dbl(pred_my_move)

    state["me"].append(move)
    return move
