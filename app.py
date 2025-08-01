import streamlit as st
import random
import math
from datetime import datetime

# ---------- CONFIG & STYLING ----------
st.set_page_config(page_title="FOFA Team Generator", layout="centered")
st.markdown(
    """
    <style>
    body { background:#0f111a; color:#f1f3f8; font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
    .flow-container { max-width: 900px; margin:auto; padding-top:8px; }
    .title-container { background:#1f242b; padding:12px 16px; border-radius:8px; margin-bottom:8px; display:flex; align-items:center; gap:12px; }
    .title-text { font-size:1.9rem; font-weight:700; margin:0; }
    .step-header { font-size:1.35rem; font-weight:700; margin-bottom:6px; }
    .subtle { color:#aaa; font-size:0.85rem; }
    .thin-sep { height:4px; background:#d1d5db; border-radius:2px; margin:16px 0; }
    .center-reset { display:flex; flex-direction:column; align-items:center; gap:8px; margin-top:16px; }
    .footer { margin-top:12px; font-size:0.7rem; color:#777; text-align:center; }
    .stButton>button { padding:6px 14px; }
    ::selection { background: transparent; }
    textarea::selection { background: #555; color: #f1f3f8; }

    /* tighter expander spacing */
    [data-testid="stExpander"] > div:first-child { padding: 6px 10px; }
    .stExpander { margin-bottom: 4px; }

    /* eliminate gap between WhatsApp heading and text area */
    [data-testid="stMarkdown"] strong, [data-testid="stMarkdown"] b { margin-bottom:0 !important; line-height:1.1 !important; }
    textarea { margin-top:0 !important; }

    /* reduce top padding of widget container just below WhatsApp heading */
    .stMarkdown + .stTextArea { padding-top:2px !important; }

    .stTextArea textarea { padding:8px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HEADER ----------
st.markdown('<div class="flow-container">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="title-container">
      <div style="font-size:2rem;">⚽</div>
      <div class="title-text">FOFA Team Generator</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- DATA ----------
SAVED_PLAYERS = [
    {"name": "Bell", "rating": 9, "is_gk": False, "position": "MID"},
    {"name": "Ky", "rating": 10, "is_gk": False, "position": "MID"},
    {"name": "Jon C", "rating": 7, "is_gk": False, "position": "DEF"},
    {"name": "Ross", "rating": 8, "is_gk": False, "position": "MID"},
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

# ---------- SESSION ----------
st.session_state.setdefault("players", [])
st.session_state.setdefault("teams", [])
st.session_state.setdefault("setup_confirmed", False)
st.session_state.setdefault("saved_select_idx", 0)

# ---------- UTILITIES ----------
def team_strengths(teams):
    return [
        (sum(p["rating"] for p in team) / len(team)) if team else 0
        for team in teams
    ]

def total_variance(strengths):
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
    remaining = others + gks[num_teams:]
    idx = 0
    for p in remaining:
        while len(teams[idx]) >= players_per_team:
            idx = (idx + 1) % num_teams
        teams[idx].append(p)
        idx = (idx + 1) % num_teams
    return teams

def simulated_annealing_optimize(initial_teams, players_per_team, iterations=1000, T0=0.5, cooling_rate=0.995):
    best_teams = [list(t) for t in initial_teams]
    current_teams = [list(t) for t in initial_teams]
    best_var = total_variance(team_strengths(best_teams))
    current_var = best_var
    T = T0

    for _ in range(iterations):
        i, j = random.sample(range(len(current_teams)), 2)
        if not current_teams[i] or not current_teams[j]:
            continue
        idx_i = random.randrange(len(current_teams[i]))
        idx_j = random.randrange(len(current_teams[j]))

        new_teams = [list(t) for t in current_teams]
        new_teams[i][idx_i], new_teams[j][idx_j] = current_teams[j][idx_j], current_teams[i][idx_i]
        new_var = total_variance(team_strengths(new_teams))

        delta = new_var - current_var
        if delta < 0 or random.random() < math.exp(-delta / T):
            current_teams = new_teams
            current_var = new_var
            if new_var < best_var:
                best_var = new_var
                best_teams = [list(t) for t in new_teams]
        T *= cooling_rate
        if T < 1e-4:
            T = 1e-4

    return best_teams, best_var

def find_best_single_swap(teams, players_per_team):
    base_strengths = team_strengths(teams)
    base_var = total_variance(base_strengths)
    best = {
        "new_variance": base_var,
        "team_i": None,
        "team_j": None,
        "player_i": None,
        "player_j": None,
        "reduction": 0.0,
    }

    n = len(teams)
    for i in range(n):
        for j in range(i + 1, n):
            for pi_idx, pi in enumerate(teams[i]):
                for pj_idx, pj in enumerate(teams[j]):
                    new_teams = [list(t) for t in teams]
                    new_teams[i][pi_idx], new_teams[j][pj_idx] = pj, pi
                    new_strengths = team_strengths(new_teams)
                    new_var = total_variance(new_strengths)
                    reduction = base_var - new_var
                    if new_var < best["new_variance"]:
                        best.update({
                            "new_variance": new_var,
                            "team_i": i,
                            "team_j": j,
                            "player_i": pi,
                            "player_j": pj,
                            "reduction": reduction,
                        })
    return best, base_var

# ---------- STEP 1: MATCH SETUP ----------
st.markdown('<div class="step-header">Step 1: Match Setup</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2, gap="small")
with col1:
    mode = st.radio("Match format", ["5-a-side", "7-a-side", "8-a-side", "11-a-side", "Custom"], horizontal=True)
    if mode == "5-a-side":
        players_per_team = 5
        st.markdown("<div class='subtle'>Players per team: 5</div>", unsafe_allow_html=True)
    elif mode == "7-a-side":
        players_per_team = 7
        st.markdown("<div class='subtle'>Players per team: 7</div>", unsafe_allow_html=True)
    elif mode == "8-a-side":
        players_per_team = 8
        st.markdown("<div class='subtle'>Players per team: 8</div>", unsafe_allow_html=True)
    elif mode == "11-a-side":
        players_per_team = 11
        st.markdown("<div class='subtle'>Players per team: 11</div>", unsafe_allow_html=True)
    else:
        players_per_team = st.number_input("Players per team (custom)", min_value=3, value=7, step=1, key="custom_ppt")
with col2:
    number_of_teams = st.number_input("Number of teams", min_value=2, value=2, step=1, key="not")

total_needed = players_per_team * number_of_teams

if not st.session_state.setup_confirmed:
    if st.button("✅ Confirm Setup"):
        st.session_state.setup_confirmed = True
else:
    st.markdown("<div class='subtle'>Setup confirmed. Proceed to Step 2.</div>", unsafe_allow_html=True)

st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)

# ---------- STEP 2: ADD PLAYERS ----------
st.markdown('<div class="step-header">Step 2: Add Players</div>', unsafe_allow_html=True)
if not st.session_state.setup_confirmed:
    st.info("✅ Complete Step 1 to unlock adding players.")
else:
    st.markdown(
        f"<div class='subtle'>Add exactly {total_needed} players (goalkeeper presence is optional; if there are GKs they’ll be distributed one per team when possible).</div>",
        unsafe_allow_html=True,
    )

    remaining = total_needed - len(st.session_state.players)
    if remaining <= 0:
        st.success("✅ Required players added. You cannot add more.")
    else:
        available = [
            p["name"] for p in SAVED_PLAYERS if p["name"] not in [x["name"] for x in st.session_state.players]
        ]
        sel_col, btn_col = st.columns([6, 1], gap="small")
        with sel_col:
            multiselect_key = f"saved_players_select_{st.session_state.saved_select_idx}"
            selected_saved = st.multiselect(
                "Choose Players",
                options=available,
                key=multiselect_key,
                help="Select from saved pool; capped to remaining when you add.",
            )
        if selected_saved and len(selected_saved) > remaining:
            st.error(f"Max number of players exceeded: only {remaining} slot(s) left.")
        with btn_col:
            if selected_saved:
                to_add = selected_saved[:remaining]
                if st.button(f"Add ({len(to_add)})"):
                    for name in to_add:
                        player = next(p for p in SAVED_PLAYERS if p["name"] == name)
                        st.session_state.players.append(player)
                    st.session_state.saved_select_idx += 1

    with st.expander("➕ Add Player Manually", expanded=False):
        if len(st.session_state.players) < total_needed:
            with st.form("manual_form"):
                name = st.text_input("Name")
                pos_col, rating_col, gk_col = st.columns(3, gap="small")
                position = pos_col.selectbox("Position", ["DEF", "MID", "ATT", "GK", "Any"])
                rating_val = rating_col.selectbox("Rating (1–10)", list(range(1, 11)), index=6)
                is_gk_flag = gk_col.checkbox("GK", value=(position == "GK"))
                submitted = st.form_submit_button("Add")
                if submitted and name:
                    if len(st.session_state.players) < total_needed:
                        st.session_state.players.append({
                            "name": name,
                            "rating": rating_val,
                            "is_gk": is_gk_flag,
                            "position": position
                        })
                        st.success(f"Added {name}")
                    else:
                        st.warning("Player limit reached; cannot add more.")
        else:
            st.info("Manual add disabled: target number of players reached.")

    if st.session_state.players:
        st.markdown("**Current Players**")
        for p in st.session_state.players:
            st.markdown(f"- {p['name']} ({'GK' if p.get('is_gk') else p.get('position','')})")

st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)

# ---------- STEP 3: GENERATE TEAMS ----------
st.markdown('<div class="step-header">Step 3: Generate Teams</div>', unsafe_allow_html=True)
required = players_per_team * number_of_teams

if not st.session_state.setup_confirmed:
    st.info("✅ Complete Step 2 before proceeding.")
elif len(st.session_state.players) < required:
    missing = required - len(st.session_state.players)
    st.info(f"🧍 Need {missing} more player(s) to generate teams.")
else:
    if st.button("Generate Teams"):
        selected = random.sample(st.session_state.players, required)
        initial = assign_teams_with_gks(selected, number_of_teams, players_per_team)
        optimized, _ = simulated_annealing_optimize(
            initial, players_per_team, iterations=1000, T0=0.5, cooling_rate=0.995
        )
        st.session_state.teams = optimized
        st.success("✅ Teams generated!")

if st.session_state.teams:
    strengths = team_strengths(st.session_state.teams)
    variance = total_variance(strengths)
    cols = st.columns(len(strengths) + 1, gap="small")
    for i, s in enumerate(strengths):
        cols[i].metric(f"Team {i+1} Avg", f"{s:.2f}")
    cols[-1].markdown(f"**Variance:** {variance:.3f}")

    if "bib_team_idx" not in st.session_state:
        st.session_state.bib_team_idx = random.randrange(len(st.session_state.teams))

    for i, team in enumerate(st.session_state.teams):
        prefix = "🎽 " if i == st.session_state.bib_team_idx else ""
        st.markdown(f"### {prefix}Team {i+1}")
        for p in team:
            role = "GK" if p.get("is_gk") else ""
            line = f"- {p['name']} ({role})" if role else f"- {p['name']}"
            st.write(line)

    st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)

    with st.expander("🔍 Suggested Best Swap", expanded=False):
        best_swap, base_var = find_best_single_swap(st.session_state.teams, players_per_team)
        if best_swap["team_i"] is not None:
            ti = best_swap["team_i"]
            tj = best_swap["team_j"]
            pi = best_swap["player_i"]["name"]
            pj = best_swap["player_j"]["name"]
            st.markdown(
                f"Swap **{pi}** (Team {ti+1}) with **{pj}** (Team {tj+1}) reduces variance "
                f"from {base_var:.4f} → {best_swap['new_variance']:.4f} (Δ {best_swap['reduction']:.4f})"
            )
            if st.button("Apply suggested swap"):
                idx_i = next(i for i, p in enumerate(st.session_state.teams[ti]) if p["name"] == pi)
                idx_j = next(j for j, p in enumerate(st.session_state.teams[tj]) if p["name"] == pj)
                st.session_state.teams[ti][idx_i], st.session_state.teams[tj][idx_j] = (
                    st.session_state.teams[tj][idx_j],
                    st.session_state.teams[ti][idx_i],
                )
                st.success("Suggested swap applied.")
        else:
            st.markdown("No improving single-player swap found; current allocation is locally optimal.")

    if len(st.session_state.teams) >= 2:
        with st.expander("🛠 Manual Swap Between Any Two Teams", expanded=False):
            team_choices = [f"Team {i+1}" for i in range(len(st.session_state.teams))]
            t1 = st.selectbox("From team", team_choices, key="manual_swap_t1")
            t2 = st.selectbox("With team", [c for c in team_choices if c != t1], key="manual_swap_t2")
            ti = team_choices.index(t1)
            tj = team_choices.index(t2)
            col1, col2 = st.columns(2)
            with col1:
                player_i_name = st.selectbox(f"Player from {t1}", [p["name"] for p in st.session_state.teams[ti]], key="manual_swap_pi")
            with col2:
                player_j_name = st.selectbox(f"Player from {t2}", [p["name"] for p in st.session_state.teams[tj]], key="manual_swap_pj")

            if st.button("Preview manual swap"):
                pi_idx = next(i for i, p in enumerate(st.session_state.teams[ti]) if p["name"] == player_i_name)
                pj_idx = next(j for j, p in enumerate(st.session_state.teams[tj]) if p["name"] == player_j_name)
                new_teams = [list(t) for t in st.session_state.teams]
                new_teams[ti][pi_idx], new_teams[tj][pj_idx] = new_teams[tj][pj_idx], new_teams[ti][pi_idx]
                new_strengths = team_strengths(new_teams)
                new_var = total_variance(new_strengths)
                st.markdown(f"Current variance: {variance:.4f}")
                st.markdown(f"Post-swap variance: {new_var:.4f}")
                reduction = variance - new_var
                st.markdown(f"Reduction: {reduction:.4f}")
                if st.button("Apply manual swap"):
                    st.session_state.teams[ti][pi_idx], st.session_state.teams[tj][pj_idx] = (
                        st.session_state.teams[tj][pj_idx],
                        st.session_state.teams[ti][pi_idx],
                    )
                    st.success("Manual swap applied.")

    message_lines = []
    for i, team in enumerate(st.session_state.teams):
        prefix = "🎽 " if i == st.session_state.bib_team_idx else ""
        message_lines.append(f"{prefix}*Team {i+1}*")
        for p in team:
            role = "GK" if p.get("is_gk") else ""
            line = f"- {p['name']} ({role})" if role else f"- {p['name']}"
            message_lines.append(line)
        message_lines.append("")

    whatsapp_msg = "\n".join(message_lines)

    st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)
    st.markdown("**📲 WhatsApp Message**")
    st.text_area("WhatsApp message (for accessibility)", whatsapp_msg, height=220, label_visibility="hidden")
    st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)

# ---------- RESET & FOOTER ----------
st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)
st.markdown('<div class="center-reset">', unsafe_allow_html=True)
st.markdown("<div style='font-size:1rem; font-weight:500;'>Need a fresh start?</div>", unsafe_allow_html=True)
if st.button("Reset All (Click Me Twice)"):
    st.session_state.players = []
    st.session_state.teams = []
    st.session_state.setup_confirmed = False
    st.session_state.saved_select_idx = 0
    if "bib_team_idx" in st.session_state:
        del st.session_state["bib_team_idx"]
    st.markdown(
        """
        <script>
        window.location.replace(window.location.pathname);
        </script>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

year = datetime.now().year
st.markdown(f"<div class='footer'>Powered by FOFA.gpt © {year}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)