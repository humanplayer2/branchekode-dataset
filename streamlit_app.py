import ast
import datetime
import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items
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

st.set_page_config(layout="wide")

# titel
st.markdown("# :sparkles::sparkles: Gyldne Branchekoder :sparkles::sparkles:")

# lav en expander så instruktioner blive skjult ved evalueringsstart, med kan vises senere:
with st.expander("Vis instruktioner og startvalg", expanded=st.session_state.expander_expanded):
    st.markdown("""
### Opgaven
Der vises en nummereret aktivitetsbeskrivelse samt en række forslag.  

For hver skal udføres to skridt:                

#### Skridt A: Vælg relevant(e) branchekode(r)    
Feltet under beskrivelsen er til at vælge branchekoder. 
- Det indeholder forslag: Fjern de irrelevante på deres kryds.
- Det er både en (meget lang) drop-down menu, men også et *tekstsøgefelt*.
- Tryk under forslagene og skriv f.eks. `10 fisk`. :fish:

#### Skridt B: Sortér branchekoder efter relevans.
Feltet i skridt B indeholder hvad der pt. er valgt i skridt A.
- Branchekoderne kan her trækkes op og ned (beklager at man ikke kan i skridt A).
- Træk koderne så de står ordnet efter relevans, med de mest relevante først.
                
Når du er tilfreds, så `Gem og gå til næste`.
                
### Kom i gang
1. Indtast udleveret brugernavn.
2. Hvis du forsætter fra tidligere, så indtast den aktivitetsbeskrivelse du er nået til. Appen holder ikke pt. styr på det for dig, desværre.
                
### Afslut / hold pause
Notér nummeret over aktivitetsbeskrivelsen så du kan forsætte derfra næste gang.
""")

    with st.form("user_info"):
        name = st.text_input("Bruger ID")
        start = st.number_input(f"Start ved aktivitetsbeskrivelse (1 -- {len(evalueringsdata)}):", min_value=1, max_value=5648, value=1)
        st.markdown("Notér gerne hvor langt du når til næste gang. Appen kan desværre ikke huske det.")
        started = st.form_submit_button("OK, jeg er klar.")

# opdater session state efter knap-tryk:
if started:
    st.session_state.started = True # vis evaluering
    st.session_state.case = start # sæt første evaluering til brugervalg
    st.session_state.expander_expanded = False # skjul instruktioner
    st.rerun() # for at skjule expander ved knap-tryk

custom_style = """
.sortable-component {
    border: 1px solid white;
    background-color: white;
    border-radius: 20px;
    padding: 4px;
    width: 780px;
}
.sortable-container {
    background-color: white;
    counter-reset: item;
    width: 780px;
}
.sortable-container-header {
    background-color: red;
    padding-left: 1rem;
}
.sortable-container-body {
    background-color: lavender;
    border-radius: 20px;
    padding: 10px;
    min-width: 780px;
    max-width: 780px;
}
.sortable-item, .sortable-item:hover {
    background-color: white;
    font-weight: normal;
    font-size: 0.95rem;
    color: black;
    width: 740px;
    height: 2.4em;
    text-align: start;
}
"""

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
        # Bold koder: Måske man kan bruge noget format_func: https://discuss.streamlit.io/t/format-func-function-examples-please/11295
        st.markdown("""
            <style>
                /* multiselect container */
                div[data-baseweb="select"] > div {
                    width: 780px !important;
                    max-height: 1600px !important;
                    overflow: auto;
                    padding-bottom: 40px !important;
                }

                /* items in multiselect container */
                .stMultiSelect [data-baseweb=select] span{
                    white-space: normal !important;  /* allows line breaks */
                    min-width: 99%;
                    max-width: 99%;
                    height: 2.4em;
                    font-size: 1rem;
                    line-height: 1 !important;
                    padding-right: 20px !important;
                    padding-top: 2px !important;
                    padding-bottom: 2px !important;
                    background-color: white;
                    color: black;
                }
            </style>
            """, unsafe_allow_html=True)

        # ---- Custom CSS end ----
        
        
        st.markdown("#### Skridt A. Vælg branchekode(r)")
        st.write("Tilføj/fjern. Skriv nederst for at filtrere. Prøv `10 fisk`.")

        user_selection = st.multiselect(
            "",
            codes_with_titles,
           default=model_suggestion,
        )
        
        st.markdown("#### Skridt B. Sortér branchekoder")
        st.write("Træk for at sortere: mest passende i top, mindst passende i bund.")
        
        user_sorting = sort_items(user_selection, custom_style=custom_style)

        with st.form("Gem?"):
            saved = st.form_submit_button("Gem og gå til næste")

        if saved:
            now = datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
            user_response_gcs_path = f"branchekode-selector-bucket/user_responses/{name}_{case}_{now}.csv"
            user_response_df = pd.DataFrame({
                'case': [case],
                'user_response': [user_sorting],
                'model_suggetion': [model_suggestion]
                })
            user_response_csv = user_response_df.to_csv(index=False).encode("utf-8")
            with conn.open(user_response_gcs_path, mode="wb") as f:
                f.write(user_response_csv)        
            st.session_state.case += 1
            st.write("Gemt! Vi er videre!")
            st.rerun(scope="fragment")                        
    return

evaluate_case()