import ast
import datetime
import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection

# forbind til google cloud storage og hent branchekoder25 og evalueringsdata
conn = st.connection('gcs', type=FilesConnection)
db25_struktur = conn.read("branchekode-selector-bucket/data_static/db25_struktur.csv", input_format="csv")
evalueringsdata = conn.read("branchekode-selector-bucket/data_static/evalueringsdata_med_titler.csv", input_format="csv")

# valgmuligheder under evaluering:
codes_with_titles = (db25_struktur["kode"] + ": " + db25_struktur["titel"]).tolist()

# setup session state
if "case" not in st.session_state:
    st.session_state.case = 1  # default start
if "started" not in st.session_state:
    st.session_state.started = False # vis først evalueringsform efter "login"
if "expander_expanded" not in st.session_state:
    st.session_state.expander_expanded = True # vis instruktioner fra start

# titel
st.markdown("# :sparkles::sparkles: Gyldne Branchekoder :sparkles::sparkles:")

# lav en expander så instruktioner blive skjult ved evalueringsstart, med kan vises senere:
with st.expander("Vis instruktioner og startvalg", expanded=st.session_state.expander_expanded):
    st.markdown("""
### Kom i gang
1. Indtast udstukket brugernavn.
2. Hvis du forsætter fra tidligere, så indtast den aktivitetsbeskrivelse du er nået til. Appen holder ikke pt. styr på det for dig, desværre.

### Opgaven
Der vises en nummereret aktivitetsbeskrivelse samt en række forslag.  

Under er et felt til at vælge branchekoder.   
    - Det indeholder forslag: Fjern de irrelevante.
    - Feltet er både en (meget lang) drop-down menu, men også et *tekstsøgefelt*.
    - Prøv at klikke efter forslagene og skriv f.eks. `10 fisk`.

Når du er tilfreds, så `Gem og gå til næste`.
                
### Afslut
Notér nummeret over aktivitetsbeskrivelsen så du kan forsætte derfra næste gang.
""")

    with st.form("user_info"):
        name = st.text_input("Bruger ID")
        start = st.number_input(f"Start ved evalueringssag (1 -- {len(evalueringsdata)}):", min_value=1, max_value=5648, value=1)
        st.markdown("Noter gerne hvor langt du når til næste gang. Appen kan desværre ikke huske det.")
        started = st.form_submit_button("OK, jeg er klar.")

# opdater session state efter knap-tryk:
if started:
    st.session_state.started = True # vis evaluering
    st.session_state.case = start # sæt første evaluering til brugervalg
    st.session_state.expander_expanded = False # skjul instruktioner
    st.rerun() # for at skjule expander ved knap-tryk

# Evaluation loop. Genkører ved knap-tryk.
@st.fragment
def evaluate_case():
    if st.session_state.started:
        
        case = st.session_state.case
        aktivitet = evalueringsdata["aktivitet"].iloc[case - 1]
        model_suggestion = ast.literal_eval(evalueringsdata["brancheforslag med titler"].iloc[case - 1])
    
        st.markdown(f"#### {case}:")
        st.markdown(f"### {aktivitet}")

        # ---- Custom CSS ----
        st.markdown("""
        <style>
        /* Make the multiselect container wider */
        div[data-baseweb="select"] > div {
            width: 800px !important;   /* adjust as needed */
        }

        /* Ensure each option uses a full line */
        div[data-baseweb="select"] span {
            white-space: normal !important;  /* allows line breaks */
        }

        </style>
        """, unsafe_allow_html=True)
        # ---- Custom CSS end ----

        user_selection = st.multiselect(
            "Hvilke(n) branchekode(r) passer? Tilføj/Fjern. Skriv for at filtrere, f.eks. '10 fisk'",
            codes_with_titles,
           default=model_suggestion,
        )

        with st.form("Gem?"):
            saved = st.form_submit_button("Gem og gå til næste")

        if saved:
            now = datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
            user_selection_gcs_path = f"branchekode-selector-bucket/user_responses/{name}_{case}_{now}.csv"
            user_selection_df = pd.DataFrame({
                'case': [case],
                'user_selection': [user_selection],
                'model_suggetion': [model_suggestion]
                })
            user_selection_csv = user_selection_df.to_csv(index=False).encode("utf-8")
            with conn.open(user_selection_gcs_path, mode="wb") as f:
                f.write(user_selection_csv)        
            st.session_state.case += 1
            st.write("Gemt! Vi er videre!")
            st.rerun(scope="fragment")                        
    return

evaluate_case()