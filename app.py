import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Radioactive Decay Lab",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- Physics model -----------------------------
LN2 = math.log(2.0)

def decay_constants(Tp, Td):
    """Return parent and daughter decay constants in inverse time units."""
    return LN2 / Tp, LN2 / Td

def parent_activity(t, Ap0, Tp):
    return Ap0 * np.exp(-LN2 * t / Tp)

def daughter_activity(t, Ap0, Tp, Td, branching=1.0, Ad0=0.0):
    """
    Exact two-member Bateman activity equation.

    Activities are in the same units. Tp and Td use the same time unit.
    branching is the fraction of parent decays that produce this daughter.
    """
    lp, ld = decay_constants(Tp, Td)
    delta = ld - lp

    if abs(delta) < 1e-12:
        # Equal decay constants: limiting form of the Bateman equation.
        produced = branching * Ap0 * lp * t * np.exp(-lp * t)
    else:
        produced = (
            branching * Ap0 * ld / delta
            * (np.exp(-lp * t) - np.exp(-ld * t))
        )

    surviving_initial_daughter = Ad0 * np.exp(-ld * t)
    return produced + surviving_initial_daughter

def daughter_peak_time(Tp, Td):
    """Time of maximum daughter activity for Ad(0)=0, when finite and positive."""
    lp, ld = decay_constants(Tp, Td)
    if abs(ld - lp) < 1e-12:
        return 1.0 / lp
    value = math.log(ld / lp) / (ld - lp)
    return value if value > 0 else None

def classify_equilibrium(Tp, Td):
    """
    Educational classification convention:
      Tp/Td >= 100: secular (practical teaching threshold)
      1 < Tp/Td < 100: transient
      Tp/Td <= 1: no classical parent-daughter equilibrium
    The boundary is a teaching convention, not a universal physical law.
    """
    ratio = Tp / Td
    if ratio >= 100:
        return "Secular equilibrium", "secular"
    if ratio > 1:
        return "Transient equilibrium", "transient"
    return "No equilibrium", "none"

def fmt(x, digits=3):
    return f"{x:.{digits}g}"

# ----------------------------- Styling -----------------------------
st.markdown(
    """
    <style>
    .main {background: #f7f9fc;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .hero {
        background: linear-gradient(115deg, #102c50, #176b87);
        padding: 1.35rem 1.6rem; border-radius: 16px; color: white;
        margin-bottom: 1rem;
    }
    .hero h1 {color:white; margin:0; font-size:2.15rem;}
    .hero p {color:#d8edf5; margin:.35rem 0 0 0;}
    .equation {
        background:#edf6fb; border:1px solid #c6e0ee; border-radius:12px;
        padding: .85rem 1rem; font-size:1.08rem; color:#102c50;
    }
    .small-note {color:#526273; font-size:.88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>⚛️ RADIOACTIVE DECAY LAB</h1>
      <p>Explore parent–daughter decay, activity buildup, and radioactive equilibrium.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Sidebar controls -----------------------------
st.sidebar.title("🧪 Experiment controls")
preset = st.sidebar.selectbox(
    "Start with an example",
    [
        "Custom experiment",
        "Secular: Ra-226 → Rn-222",
        "Transient: Mo-99 → Tc-99m",
        "No equilibrium: Te-131m → I-131",
    ],
)

presets = {
    "Secular: Ra-226 → Rn-222": (1620 * 365.25, 3.8235, "years/days converted to days"),
    "Transient: Mo-99 → Tc-99m": (66.0, 6.0, "hours"),
    "No equilibrium: Te-131m → I-131": (30.0, 8.0 * 24.0, "hours"),
}
if preset == "Secular: Ra-226 → Rn-222":
    default_Tp, default_Td = 1620 * 365.25, 3.8235
    unit_label = "days"
    default_span = 30.0
elif preset == "Transient: Mo-99 → Tc-99m":
    default_Tp, default_Td = 66.0, 6.0
    unit_label = "hours"
    default_span = 240.0
elif preset == "No equilibrium: Te-131m → I-131":
    default_Tp, default_Td = 30.0, 192.0
    unit_label = "hours"
    default_span = 500.0
else:
    unit_label = st.sidebar.selectbox("Time unit", ["hours", "days"])
    default_Tp = 48.0
    default_Td = 6.0
    default_span = 240.0

if preset.startswith("Secular"):
    st.sidebar.caption("Example uses days for both half-lives.")
elif preset != "Custom experiment":
    st.sidebar.caption("Example uses hours for both half-lives.")

Tp = st.sidebar.number_input(
    f"Parent half-life, Tp ({unit_label})",
    min_value=0.001, value=float(default_Tp), step=max(float(default_Tp)/20, 0.001),
    format="%.5g",
)
Td = st.sidebar.number_input(
    f"Daughter half-life, Td ({unit_label})",
    min_value=0.001, value=float(default_Td), step=max(float(default_Td)/20, 0.001),
    format="%.5g",
)
Ap0 = st.sidebar.number_input("Initial parent activity, Ap(0)", min_value=0.001, value=100.0, step=10.0)
Ad0 = st.sidebar.number_input("Initial daughter activity, Ad(0)", min_value=0.0, value=0.0, step=1.0)
branching = st.sidebar.slider("Branching ratio", min_value=0.01, max_value=1.0, value=1.0, step=0.01)
time_span = st.sidebar.number_input(
    f"Observation period ({unit_label})",
    min_value=0.01, value=float(default_span), step=max(float(default_span)/20, 0.01),
)
log_axis = st.sidebar.checkbox("Use logarithmic activity axis", value=False)
show_total = st.sidebar.checkbox("Show total activity (parent + daughter)", value=True)

ratio = Tp / Td
classification, class_key = classify_equilibrium(Tp, Td)
lp, ld = decay_constants(Tp, Td)
t_peak = daughter_peak_time(Tp, Td)

# ----------------------------- Main tabs -----------------------------
tab_explore, tab_compare, tab_theory, tab_quiz, tab_about = st.tabs(
    ["🔬 Explore", "📊 Compare the three states", "📘 Learn the physics", "📝 Knowledge check", "👩‍🔬 About"]
)

with tab_explore:
    st.subheader("Your parent–daughter experiment")
    c1, c2, c3 = st.columns(3)
    c1.metric("Half-life ratio, Tp / Td", fmt(ratio))
    c2.metric("Classification", classification)
    c3.metric("Daughter peak time", "Not calculated" if t_peak is None else f"{t_peak:.3g} {unit_label}")

    if class_key == "secular":
        st.success(
            "The parent is much longer-lived than the daughter. Its activity changes very little "
            "during the daughter buildup, so daughter activity approaches the parent activity "
            "(for a branching ratio near 1)."
        )
    elif class_key == "transient":
        st.info(
            "The parent is longer-lived, but its activity decreases measurably. After buildup, "
            "parent and daughter activities decline with the same exponential slope; their ratio "
            "approaches a constant."
        )
    else:
        st.warning(
            "The daughter half-life is equal to or longer than the parent's. The parent decays "
            "faster, the daughter may build up and reach a maximum, and no sustained classical "
            "equilibrium is established."
        )

    t = np.linspace(0, time_span, 1000)
    Ap = parent_activity(t, Ap0, Tp)
    Ad = daughter_activity(t, Ap0, Tp, Td, branching, Ad0)
    At = Ap + Ad

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=Ap, name="Parent activity, Ap(t)", line=dict(color="#1769aa", width=3)))
    fig.add_trace(go.Scatter(x=t, y=Ad, name="Daughter activity, Ad(t)", line=dict(color="#ef7d22", width=3)))
    if show_total:
        fig.add_trace(go.Scatter(x=t, y=At, name="Total activity", line=dict(color="#15977f", width=2, dash="dash")))
    if t_peak is not None and t_peak <= time_span and Ad0 == 0:
        peak_value = float(daughter_activity(np.array([t_peak]), Ap0, Tp, Td, branching, Ad0)[0])
        fig.add_trace(go.Scatter(
            x=[t_peak], y=[peak_value], mode="markers+text",
            name="Daughter maximum",
            text=[f"Maximum<br>{t_peak:.3g} {unit_label}"],
            textposition="top center",
            marker=dict(size=10, color="#8b3fb0"),
        ))
    fig.update_layout(
        template="plotly_white", height=510,
        xaxis_title=f"Time ({unit_label})",
        yaxis_title="Activity (same units as initial activity)",
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
    )
    if log_axis:
        fig.update_yaxes(type="log", rangemode="tozero")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### What is happening?")
    left, right = st.columns(2)
    with left:
        st.markdown(
            f"""
            **Parent radionuclide**

            - Starts at **{Ap0:g}** activity units.
            - Decays continuously with a half-life of **{Tp:g} {unit_label}**.
            - Decay constant: **{lp:.5g} per {unit_label}**.
            """
        )
    with right:
        st.markdown(
            f"""
            **Daughter radionuclide**

            - Starts at **{Ad0:g}** activity units.
            - Is produced by parent decay with branching ratio **{branching:.0%}**.
            - Decays with a half-life of **{Td:g} {unit_label}**.
            """
        )

    st.markdown("#### Activity values at selected times")
    sample_times = np.array([0, time_span * .25, time_span * .5, time_span * .75, time_span])
    sample_parent = parent_activity(sample_times, Ap0, Tp)
    sample_daughter = daughter_activity(sample_times, Ap0, Tp, Td, branching, Ad0)
    table = pd.DataFrame({
        f"Time ({unit_label})": sample_times,
        "Parent activity": sample_parent,
        "Daughter activity": sample_daughter,
        "Total activity": sample_parent + sample_daughter,
    })
    st.dataframe(table.round(4), use_container_width=True, hide_index=True)

with tab_compare:
    st.subheader("Compare secular, transient, and no-equilibrium behavior")
    st.write(
        "These comparison plots are shown in a textbook-style format to make the "
        "three states easier for students to understand."
    )

    st.info(
        "All three plots are normalized for teaching. The horizontal axis is expressed "
        "in **number of daughter half-lives**, and the vertical axis is shown on a "
        "**logarithmic scale**."
    )

    secular_col, transient_col, none_col = st.columns(3)

    # -------- Secular equilibrium --------
    with secular_col:
        x = np.linspace(0, 10, 500)  # x = number of daughter half-lives
        parent = np.ones_like(x)     # parent is essentially constant
        daughter = 1 - 2 ** (-x)     # buildup toward parent activity

        f = go.Figure()
        f.add_trace(go.Scatter(
            x=x, y=parent, name="Parent activity",
            line=dict(color="#7b3294", width=3, dash="dash")
        ))
        f.add_trace(go.Scatter(
            x=x, y=daughter, name="Daughter activity",
            line=dict(color="#d26a00", width=3)
        ))

        f.update_layout(
            title="Secular",
            template="plotly_white",
            height=320,
            xaxis_title="Number of daughter half-lives",
            yaxis_title="Activity (arbitrary units)",
            margin=dict(l=10, r=10, t=45, b=10),
            showlegend=False,
            annotations=[
                dict(x=4.0, y=1.03, text="Parent activity", showarrow=False,
                     font=dict(size=12, color="#222")),
                dict(x=3.5, y=0.62, text="Daughter activity", showarrow=False,
                     font=dict(size=12, color="#222")),
            ],
        )
        f.update_yaxes(type="log", range=[-1, 0.05], tickvals=[0.1, 1], ticktext=["0.1", "1"])
        f.update_xaxes(range=[0, 10])
        st.plotly_chart(f, use_container_width=True)
        st.caption("Long-lived parent: daughter activity rises and approaches the parent activity.")

    # -------- Transient equilibrium --------
    with transient_col:
        # textbook-style example: parent half-life = 11 daughter half-lives
        x = np.linspace(0, 10, 700)  # x = number of daughter half-lives
        Td_rel = 1.0
        Tp_rel = 11.0
        t = x * Td_rel

        parent = parent_activity(t, 1.0, Tp_rel)
        daughter = daughter_activity(t, 1.0, Tp_rel, Td_rel, 1.0, 0.0)

        f = go.Figure()
        f.add_trace(go.Scatter(
            x=x, y=parent, name="Parent activity",
            line=dict(color="#7b3294", width=3, dash="dash")
        ))
        f.add_trace(go.Scatter(
            x=x, y=daughter, name="Daughter activity",
            line=dict(color="#d26a00", width=3)
        ))

        f.update_layout(
            title="Transient",
            template="plotly_white",
            height=320,
            xaxis_title="Number of daughter half-lives",
            yaxis_title="Activity (arbitrary units)",
            margin=dict(l=10, r=10, t=45, b=10),
            showlegend=False,
            annotations=[
                dict(x=4.5, y=0.92, text="Parent activity", showarrow=False,
                     font=dict(size=12, color="#222")),
                dict(x=5.3, y=0.38, text="Daughter activity", showarrow=False,
                     font=dict(size=12, color="#222")),
            ],
        )
        f.update_yaxes(type="log", range=[-1, 0.05], tickvals=[0.1, 1], ticktext=["0.1", "1"])
        f.update_xaxes(range=[0, 10])
        st.plotly_chart(f, use_container_width=True)
        st.caption("Parent decays measurably; daughter rises, peaks, then both decline with similar slopes.")

    # -------- No equilibrium --------
    with none_col:
        # textbook-style example: parent half-life = 0.1 daughter half-life
        x = np.linspace(0, 1.0, 700)  # x = number of daughter half-lives
        Td_rel = 1.0
        Tp_rel = 0.1
        t = x * Td_rel

        parent = parent_activity(t, 1.0, Tp_rel)
        daughter = daughter_activity(t, 1.0, Tp_rel, Td_rel, 1.0, 0.0)

        f = go.Figure()
        f.add_trace(go.Scatter(
            x=x, y=parent, name="Parent activity",
            line=dict(color="#7b3294", width=3, dash="dash")
        ))
        f.add_trace(go.Scatter(
            x=x, y=daughter, name="Daughter activity",
            line=dict(color="#d26a00", width=3)
        ))

        f.update_layout(
            title="No equilibrium",
            template="plotly_white",
            height=320,
            xaxis_title="Number of daughter half-lives",
            yaxis_title="Activity (arbitrary units)",
            margin=dict(l=10, r=10, t=45, b=10),
            showlegend=False,
            annotations=[
                dict(x=0.48, y=0.38, text="Parent activity", showarrow=False,
                     font=dict(size=12, color="#222")),
                dict(x=0.67, y=0.11, text="Daughter activity", showarrow=False,
                     font=dict(size=12, color="#222")),
            ],
        )
        f.update_yaxes(type="log", range=[-2, 0.05], tickvals=[0.01, 0.1, 1], ticktext=["0.01", "0.1", "1"])
        f.update_xaxes(range=[0, 1.0])
        st.plotly_chart(f, use_container_width=True)
        st.caption("Short-lived parent: daughter activity builds up, reaches a maximum, then decays.")

    st.markdown("#### The key distinction")
    st.markdown(
        """
        | State | Half-life relationship | Typical behavior |
        |---|---|---|
        | **Secular equilibrium** | Parent half-life is much longer than daughter half-life | Parent activity is nearly constant during observation; daughter activity approaches the parent activity. |
        | **Transient equilibrium** | Parent half-life is longer than daughter half-life, but not enormously longer | Daughter builds up, reaches a maximum, and then both parent and daughter decline with nearly the same slope. |
        | **No equilibrium** | Daughter half-life is longer than the parent half-life | Daughter builds up and peaks, but no sustained equilibrium is formed. |
        """
    )

with tab_theory:
    st.subheader("Understand the equations")
    st.markdown("#### 1. Parent activity")
    st.latex(r"A_p(t)=A_p(0)e^{-\lambda_p t}")
    st.latex(r"\lambda_p=\frac{\ln 2}{T_p}")
    st.markdown("#### 2. Daughter activity: Bateman equation")
    st.latex(
        r"A_d(t)=A_d(0)e^{-\lambda_d t}"
        r"+BR\cdot A_p(0)\frac{\lambda_d}{\lambda_d-\lambda_p}"
        r"\left(e^{-\lambda_p t}-e^{-\lambda_d t}\right)"
    )
    st.caption(
        "This expression assumes a two-member decay chain, constant branching ratio, "
        "and no additional production pathways."
    )
    st.markdown("#### 3. Time of maximum daughter activity")
    st.latex(r"t_{\max}=\frac{\ln(\lambda_d/\lambda_p)}{\lambda_d-\lambda_p}")
    st.caption(
        "For initially absent daughter activity and unequal decay constants. "
        "The limiting equal-half-life case is tmax = 1/λ."
    )
    st.markdown("#### 4. How to recognize equilibrium")
    st.markdown(
        """
        - **Secular:** the parent barely changes while the daughter builds up. With a branching ratio of 1, daughter activity approaches the parent activity.
        - **Transient:** the daughter builds up, then both activities have the same long-term exponential slope. The daughter-to-parent activity ratio approaches a constant greater than 1 for a branching ratio of 1.
        - **No equilibrium:** the daughter half-life is not shorter than the parent's. The parent disappears relatively quickly and the daughter later decays according to its own half-life.
        """
    )
    st.info(
        "Teaching convention used by this app: Tp/Td ≥ 100 is labeled secular; "
        "1 < Tp/Td < 100 is labeled transient; Tp/Td ≤ 1 is labeled no equilibrium. "
        "The 100-fold cutoff is a practical classroom rule, not a sharp physical boundary."
    )

with tab_quiz:
    st.subheader("Test your understanding")
    questions = [
        {
            "q": "A parent has a half-life of 100 days and its daughter has a half-life of 1 day. Which state is most appropriate?",
            "options": ["Secular equilibrium", "Transient equilibrium", "No equilibrium"],
            "answer": "Secular equilibrium",
            "why": "The parent is 100 times longer-lived than the daughter, so its activity changes very little during daughter buildup.",
        },
        {
            "q": "For transient equilibrium, what happens after daughter buildup?",
            "options": [
                "Both activities become constant",
                "Both activities decline with approximately the same slope on a semi-log plot",
                "The daughter activity becomes zero immediately",
            ],
            "answer": "Both activities decline with approximately the same slope on a semi-log plot",
            "why": "The daughter-to-parent activity ratio approaches a constant while both continue to decrease.",
        },
        {
            "q": "The parent half-life is 2 hours and the daughter half-life is 20 hours. What is expected?",
            "options": ["Secular equilibrium", "Transient equilibrium", "No equilibrium"],
            "answer": "No equilibrium",
            "why": "The daughter is longer-lived than the parent, so a sustained parent–daughter equilibrium is not established.",
        },
        {
            "q": "What does the branching ratio describe?",
            "options": [
                "The fraction of daughter atoms that decay",
                "The fraction of parent decays that produce the specified daughter",
                "The ratio of parent half-life to daughter half-life",
            ],
            "answer": "The fraction of parent decays that produce the specified daughter",
            "why": "Only this fraction of parent decays feeds the daughter pathway represented in the equation.",
        },
    ]
    for i, q in enumerate(questions, 1):
        st.markdown(f"**Question {i}. {q['q']}**")
        choice = st.radio(
            "Choose one answer:",
            q["options"],
            key=f"quiz_{i}",
            label_visibility="collapsed",
        )
        if st.button("Check answer", key=f"check_{i}"):
            if choice == q["answer"]:
                st.success("Correct! " + q["why"])
            else:
                st.error("Not quite. " + q["why"])
        st.divider()


with tab_about:
    st.subheader("About this educational platform")
    st.markdown(
        """
        <div style="
            background: linear-gradient(120deg, #102c50, #176b87);
            color: white; padding: 1.5rem; border-radius: 16px;
            margin: .5rem 0 1.2rem 0;">
            <div style="font-size: 1.55rem; font-weight: 700;">
                Radioactive Decay Lab
            </div>
            <div style="color: #d8edf5; margin-top: .35rem;">
                An interactive educational platform for parent–daughter decay
                and radioactive equilibrium.
            </div>
        </div>
        <div style="
            background: #f0f6fa; border: 1px solid #c6dce9;
            border-radius: 14px; padding: 1.25rem; color: #17324d;">
            <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: .35rem;">
                Created by
            </div>
            <div style="font-size: 1.15rem; font-weight: 700;">
                Elmira Yazdani, PhD
            </div>
            <div style="margin-top: .35rem; line-height: 1.65;">
                Assistant Professor of Medical Physics<br>
                College of Medicine<br>
                Iran University of Medical Sciences
            </div>
            <hr style="border: 0; border-top: 1px solid #c6dce9; margin: 1rem 0;">
            <div style="margin-bottom: .45rem;">
                <strong>Email:</strong>
                <a href="mailto:yazdani.el@iums.ac.ir">yazdani.el@iums.ac.ir</a>
            </div>
            <div>
                <strong>Google Scholar:</strong>
                <a href="https://scholar.google.com/citations?user=iMlzb9UAAAAJ&hl=en"
                   target="_blank" rel="noopener noreferrer">
                   View academic profile ↗
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "This platform is intended for education and conceptual exploration. "
        "Please verify scientific parameters and equations against authoritative references "
        "before using them in research or clinical work."
    )


st.markdown(
    """
    <p class="small-note">
    Educational simulation only. It models a simple parent → daughter decay chain and does not
    replace a full decay-chain solver, clinical dosimetry system, or measured patient data.
    </p>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div style="
        border-top: 1px solid rgba(128, 150, 170, .35);
        margin-top: 1.5rem; padding-top: .85rem;
        text-align: center; color: #7b8794; font-size: .88rem;">
        Created by <strong>Elmira Yazdani, PhD</strong>
        · Assistant Professor of Medical Physics
        · <a href="mailto:yazdani.el@iums.ac.ir">Contact</a>
        · <a href="https://scholar.google.com/citations?user=iMlzb9UAAAAJ&hl=en"
             target="_blank" rel="noopener noreferrer">Google Scholar</a>
    </div>
    """,
    unsafe_allow_html=True,
)
