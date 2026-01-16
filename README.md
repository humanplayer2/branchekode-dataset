# branchekode-dataset

:sparkles::sparkles: [Open deployed Streamlit](https://branchekode-dataset.streamlit.app/) :sparkles::sparkles:


To run locally
- Fill in `.streamlit/secrets.toml` according to its `.dist`. [Streamlit docs](https://docs.streamlit.io/develop/tutorials/databases/gcs).
- Install the pixi env: `pixi install`
- Run the streamlit in it: `pixi run streamlit run streamlit_app.py`

To download user responses:
- Fill in `.streamlit/secrets.toml` according to its `.dist`. [Streamlit docs](https://docs.streamlit.io/develop/tutorials/databases/gcs).
- Install the pixi env: `pixi install`
- `pixi run download_google_cloud_bucket.py`
