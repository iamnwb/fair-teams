import streamlit as st
import random
from datetime import datetime

# ---------- CONFIG & STYLES ----------
st.set_page_config(page_title="FOFA Team Generator", layout="centered")
st.markdown(
    """
    <style>
      :root { --bg:#0f111a; --card:#1f242b; --radius:8px; --muted:#777; }
      body { background: var(--bg); color: #f1f3f8; font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
      .container { max-width: 1000px; margin:auto; padding:12px 16px; }
      .title { background: var(--card); padding:14px 16px; border-radius: var(--radius); display:flex; align-items:center; gap:12px; margin-bottom:8px; }
      .title h1 { margin:0; font-size:2rem; }
      .step { margin-top:24px; }
      .step-header { font-size:1.5rem; font-weight:700; margin-bottom:4px; }
      .subtle { color:#aaa; font-size:0.85rem; }
      .sep { height:4px; background:#d1d5db; border-radius:2px; margin:16px 0; }
      .footer { margin-top:16px; font-size:0.7rem; color:#999; text-align:center; }
      .pill { background:#1f242b; padding:8px 16px; border-radius:999px; font-size:0.9rem; display:inline-block; }
      .whatsapp-box { border-radius:12px; background: #1f242b; padding:14px; }
      .swap-info { background:#1f242b; padding:12px; border-radius:8px; }
      .inline-gap > * { margin-right:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown(
    '<div class="title"><div style="font-size:2rem;">⚽</div><h1>FOFA Team Generator</h1></div>',
    unsafe_allow_html=True,
)

# ---------- SESSION STATE ----------
st.session_state.setdefault("players", [])
st.session_state.setdefault("teams", [])
st.session_state.setdefault("setup_confirmed", False)
st.session_state.setdefault("bib_team_idx", None)

# ---------- SAVED PLAYERS ----------
SAVED_PLAYERS = [
    {"name": "Bell", "rating": 9, "is_gk": False, "position": "MID"},
    {"name": "Ky", "rating": 10, "is_gk": False, "position": "MID"},
    {"name": "Jon C", "rating": 7, "is_gk": False, "position": "DEF"},
    {"name": "Jord", "rating": 9, "is_gk": False, "position": "DEF"},
    {"name": "Callum", "rating": 7, "is_gk": False, "position": "DEF"},
    {"name": "OB", "rating": 7, "is_gk": False, "position": "MID"},
    {"name": "Matts", "rating": 7, "is_gk": False, "position": "MID"},
    {"name": "Kie", "rating": 7, "is_gk": False, "position": "DEF"},
    {"name": "Cob", "rating": 7, "is_gk": False, "position": "MID"},
    {"name": "Middle", "rating": 6, "is_gk": False, "position": "DEF"},
    {"name": "Owen", "rating": 8, "is_gk": False, "position": "MID"},
    {"name": "Ant", "rating": 7, "is_gk": True, "position": "ATT"},
    {"name": "Stokes", "rating": 6, "is_gk": True, "position": "DEF"},
    {"name": "Hannon", "rating": 6, "is_gk": False, "position": "MID"},
    {"name": "Matt Field", "rating": 6, "is_gk": False, "position": "ATT"},
]

# ---------- UTILITIES ----------
def team_strengths(teams):
    return [(sum(p["rating"] for p in team) / len(team)) if team else 0 for team in teams]

def variance_of(strengths):
    mean = sum(strengths) / len(strengths)
    return sum((s - mean) ** 2 for s in strengths) / len(strengths)

def assign_teams_with_gks(players, num_teams, players_per_team):
    gks = [p for p in players if p.get("is_gk")]
    others = [p for p in players if not p.get("is_gk")]
    random.shuffle(gks)
    random.shuffle(others)
    teams = [[] for _ in range(num_teams)]
    for i in range(min(len(gks), num_teams)):
        teams[i].append(gks[i])
    remainder = others + gks[num_teams:]
    idx = 0
    for p in remainder:
        while len(teams[idx]) >= players_per_team:
            idx = (idx + 1) % num_teams
        teams[idx].append(p)
        idx = (idx + 1) % num_teams
    return teams

def find_best_swap(teams):
    base_strengths = team_strengths(teams)
    base_var = variance_of(base_strengths)
    best = {"new_var": base_var, "i": None, "j": None, "pi": None, "pj": None, "delta": 0.0}
    n = len(teams)
    for ti in range(n):
        for tj in range(ti + 1, n):
            for pi_idx, pi in enumerate(teams[ti]):
                for pj_idx, pj in enumerate(teams[tj]):
                    candidate = [list(t) for t in teams]
                    candidate[ti][pi_idx], candidate[tj][pj_idx] = pj, pi
                    cand_var = variance_of(team_strengths(candidate))
                    reduction = base_var - cand_var
                    if cand_var < best["new_var"]:
                        best.update({
                            "new_var": cand_var,
                            "i": ti, "j": tj,
                            "pi": pi, "pj": pj,
                            "delta": reduction,
                        })
    return best, base_var

# ---------- STEP 1 ----------
st.markdown('<div class="step"><div class="step-header">Step 1: Match Setup</div></div>', unsafe_allow_html=True)
col1, col2 = st.columns([2, 1], gap="small")
with col1:
    mode = st.radio("Match format", ["5-a-side", "7-a-side", "8-a-side", "11-a-side", "Custom"], horizontal=True)
    if mode == "5-a-side":
        players_per_team = 5
    elif mode == "7-a-side":
        players_per_team = 7
    elif mode == "8-a-side":
        players_per_team = 8
    elif mode == "11-a-side":
        players_per_team = 11
    else:
        players_per_team = st.number_input("Players per team (custom)", min_value=3, value=7, step=1)
with col2:
    number_of_teams = st.number_input("Number of teams", min_value=2, value=2, step=1)
total_needed = players_per_team * number_of_teams
if not st.session_state.setup_confirmed:
    if st.button("✅ Confirm Setup"):
        st.session_state.setup_confirmed = True
else:
    st.markdown("<div class='subtle'>Setup confirmed.</div>", unsafe_allow_html=True)
st.markdown('<div class="sep"></div>', unsafe_allow_html=True)

# ---------- STEP 2 ----------
st.markdown('<div class="step"><div class="step-header">Step 2: Add Players</div></div>', unsafe_allow_html=True)
if not st.session_state.setup_confirmed:
    st.info("Complete Step 1 first.")
else:
    remaining = total_needed - len(st.session_state.players)

    # Saved picker
    with st.expander("📦 Saved Players", expanded=True):
        if remaining <= 0:
            st.success("Target reached; cannot add more saved players.")
        else:
            added_names = {p["name"] for p in st.session_state.players}
            available = [p for p in SAVED_PLAYERS if p["name"] not in added_names]
            if not available:
                st.markdown("All saved players already added.")
            else:
                st.markdown(f"Select up to {remaining} player(s) to add:")
                grouped = {"GK": [], "DEF": [], "MID": [], "ATT": [], "Any": []}
                for p in available:
                    pos = p.get("position", "Any")
                    if pos not in grouped:
                        pos = "Any"
                    grouped[pos].append(p)
                picks = []
                for section in ["GK", "DEF", "MID", "ATT", "Any"]:
                    players_in_section = grouped[section]
                    if not players_in_section:
                        continue
                    st.markdown(f"**{section}**")
                    cols = st.columns(3)
                    for idx, player in enumerate(players_in_section):
                        col = cols[idx % 3]
                        key = f"pick_{player['name']}"
                        checked = col.checkbox(f"{player['name']}", key=key)
                        if checked:
                            picks.append(player)
                # persistent add button
                to_add = picks[:remaining] if remaining > 0 else []
                disabled = remaining <= 0 or not picks
                btn_label = f"Add Selected ({min(len(picks), remaining)})" if picks else "Add Selected (0)"
                if st.button(btn_label, disabled=disabled):
                    for pl in to_add:
                        st.session_state.players.append(pl)
                    for pl in to_add:
                        st.session_state.pop(f"pick_{pl['name']}", None)

    # Manual add
    with st.expander("➕ Add Player Manually", expanded=False):
        if len(st.session_state.players) < total_needed:
            with st.form("manual"):
                name = st.text_input("Name")
                pos_col, rating_col = st.columns(2, gap="small")
                position = pos_col.selectbox("Position", ["DEF", "MID", "ATT", "GK", "Any"])
                rating_val = rating_col.selectbox("Rating (1–10)", list(range(1, 11)), index=6)
                if st.form_submit_button("Add"):
                    if name:
                        st.session_state.players.append({
                            "name": name,
                            "rating": rating_val,
                            "is_gk": position == "GK",
                            "position": position,
                        })
        else:
            st.info("Manual add disabled; target met.")

    # Current players
    if st.session_state.players:
        st.markdown("**Current Players**")
        for p in st.session_state.players:
            role = "GK" if p.get("is_gk") else p.get("position", "")
            st.markdown(f"- {p['name']} ({role})")

st.markdown('<div class="sep"></div>', unsafe_allow_html=True)

# ---------- STEP 3 ----------
st.markdown('<div class="step"><div class="step-header">Step 3: Generate Teams</div></div>', unsafe_allow_html=True)
if not st.session_state.setup_confirmed:
    st.info("Complete Step 1.")
elif len(st.session_state.players) < total_needed:
    st.info(f"Need {total_needed - len(st.session_state.players)} more player(s).")
else:
    if st.button("Generate Teams"):
        sampled = random.sample(st.session_state.players, total_needed)
        initial = assign_teams_with_gks(sampled, number_of_teams, players_per_team)
        st.session_state.teams = initial
        if st.session_state.bib_team_idx is None:
            st.session_state.bib_team_idx = random.randrange(len(initial))
        st.success("Teams generated.")
    if st.session_state.teams:
        strengths = team_strengths(st.session_state.teams)
        var = variance_of(strengths)
        cols = st.columns(len(strengths) + 1, gap="small")
        for i, s in enumerate(strengths):
            cols[i].metric(f"Team {i+1} Avg", f"{s:.2f}")
        cols[-1].markdown(f"**Variance:** {var:.3f}")
        for ti, team in enumerate(st.session_state.teams):
            prefix = "🎽 " if ti == st.session_state.bib_team_idx else ""
            st.markdown(f"### {prefix}Team {ti+1}")
            for p in team:
                role = "GK" if p.get("is_gk") else ""
                line = f"- {p['name']} ({role})" if role else f"- {p['name']}"
                st.write(line)

        with st.expander("🔍 Suggested Best Swap", expanded=False):
            if not st.session_state.teams:
                st.markdown("Generate teams first.")
            else:
                base_strengths = team_strengths(st.session_state.teams)
                base_var = variance_of(base_strengths)
                st.markdown(f"**Current team averages:** " +
                            " / ".join([f"Team {i+1}: {s:.2f}" for i, s in enumerate(base_strengths)]))
                st.markdown(f"**Current variance:** {base_var:.4f}")

                best_swap, _ = find_best_swap(st.session_state.teams)
                if best_swap["i"] is not None:
                    ti, tj = best_swap["i"], best_swap["j"]
                    pi, pj = best_swap["pi"]["name"], best_swap["pj"]["name"]
                    st.markdown(
                        f"Swap **{pi}** (Team {ti+1}) with **{pj}** (Team {tj+1}) reduces variance "
                        f"from {base_var:.4f} → {best_swap['new_var']:.4f} (Δ {best_swap['delta']:.4f})"
                    )
                    if st.button("Apply suggested swap"):
                        idx_i = next(i for i, p in enumerate(st.session_state.teams[ti]) if p["name"] == pi)
                        idx_j = next(j for j, p in enumerate(st.session_state.teams[tj]) if p["name"] == pj)
                        st.session_state.teams[ti][idx_i], st.session_state.teams[tj][idx_j] = (
                            st.session_state.teams[tj][idx_j],
                            st.session_state.teams[ti][idx_i],
                        )
                        new_strengths = team_strengths(st.session_state.teams)
                        new_var = variance_of(new_strengths)
                        st.success("Swap applied.")
                        st.markdown(f"**New team averages:** " +
                                    " / ".join([f"Team {i+1}: {s:.2f}" for i, s in enumerate(new_strengths)]))
                        st.markdown(f"**New variance:** {new_var:.4f} (improved by {base_var - new_var:.4f})")
                else:
                    st.markdown("No beneficial single swap found.")

        # WhatsApp message
        msg_lines = []
        for i, team in enumerate(st.session_state.teams):
            prefix = "🎽 " if i == st.session_state.bib_team_idx else ""
            msg_lines.append(f"{prefix}*Team {i+1}*")
            for p in team:
                role = "GK" if p.get("is_gk") else ""
                line = f"- {p['name']} ({role})" if role else f"- {p['name']}"
                msg_lines.append(line)
            msg_lines.append("")
        whatsapp_msg = "\n".join(msg_lines)

        st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sep" style="margin:6px 0 4px;"></div>', unsafe_allow_html=True)
        st.markdown("**📲 WhatsApp Message**")
        st.text_area("WhatsApp message", whatsapp_msg, height=200, label_visibility="hidden", key="wa_msg")

# ---------- RESET + FOOTER ----------
st.markdown('<div class="sep" style="margin:14px 0 6px;"></div>', unsafe_allow_html=True)
if st.button("Reset All (Click Me Twice)"):
    st.session_state.players = []
    st.session_state.teams = []
    st.session_state.setup_confirmed = False
    st.session_state.pop("bib_team_idx", None)

year = datetime.now().year
st.markdown(f'<div class="footer">Powered by FOFA.gpt © {year}</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)