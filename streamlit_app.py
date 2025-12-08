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
                ### Start:
                1. Indtast selvvalgt brugernavn. Genbrug det fra sidst.
                2. Indtast den aktivitetsbeskrivelse du er nået til. Appen holder ikke pt. styr på det for dig, desværre.
                
                ### Evaluering:
                Der vises en nummereret aktivitetsbeskrivelse samt en række forslag.  
                Man kan klikke i feltet og skrive for at filtrere med kode eller tekst (f.eks. "10." eller "behandli").
                1. Fjern forkerte forslag.
                2. Tilføj rigtige forslag.
                3. Gem.
                4. Næste præsenteres.
                
                Du kan vælge at springe sag en over. 
                
                ### Stop:
                Du kan bare lukke fanen når du har gemt, men skriv gerne ned til næste gang hvilken sag du er nået til.
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
    
        st.markdown(f"## Aktivitetsbeskrivelse {case}:")
        st.markdown(f"### {aktivitet}")

        user_selection = st.multiselect(
            "Hvilke(n) branchekode(r) passer?",
            codes_with_titles,
           default=model_suggestion,
        )
        st.write("Valgt(e):", user_selection)
    
        st.markdown("Du kan tilføje flere. Hvis du er tilfreds kan du gemme og forsætte. Eller du kan springe denne over og forsætte til næste.")

        with st.form("Gem?"):
            saved = st.form_submit_button("Gem og gå til næste")
            skipped = st.form_submit_button("Gem ikke og gå til næste")

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
            
        elif skipped:
            now = datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
            user_selection_gcs_path = f"branchekode-selector-bucket/user_responses/{name}_{case}_{now}.csv"
            user_selection_df = pd.DataFrame({
                'case': [case],
                'user_selection': ['skipped'],
                'model_suggetion': [model_suggestion]
                })
            user_selection_csv = user_selection_df.to_csv(index=False).encode("utf-8")
            with conn.open(user_selection_gcs_path, mode="wb") as f:
                f.write(user_selection_csv)        
            st.write("Gemt! vi er videre!")
            st.session_state.case += 1
            st.rerun(scope="fragment")
            
    return

evaluate_case()