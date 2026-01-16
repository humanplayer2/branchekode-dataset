import os
import json
import datetime
import streamlit as st
from google.cloud import storage
from google.oauth2 import service_account


def get_gcs_credentials_dict():
    """
    Extract Google Cloud Storage service account credentials
    from Streamlit secrets and return as a dict.
    """
    gcs = st.secrets["connections"]["gcs"]

    return {
        "type": gcs["type"],
        "project_id": gcs["project_id"],
        "private_key_id": gcs["private_key_id"],
        # Important: fix escaped newlines
        "private_key": gcs["private_key"].replace("\\n", "\n"),
        "client_email": gcs["client_email"],
        "client_id": gcs["client_id"],
        "auth_uri": gcs["auth_uri"],
        "token_uri": gcs["token_uri"],
        "auth_provider_x509_cert_url": gcs["auth_provider_x509_cert_url"],
        "client_x509_cert_url": gcs["client_x509_cert_url"],
    }


def download_bucket(bucket_name: str, base_local_folder: str = "./data_local"):
    """
    Downloads the entire contents of a Google Cloud Storage bucket
    into a local, date-stamped directory.

    - Skips GCS directory-marker objects
    - Recreates full folder hierarchy
    - Uses in-memory credentials (no temp files)
    """

    # ------------------------------------------------------------------
    # Create GCS client using in-memory service account credentials
    # ------------------------------------------------------------------
    credentials_dict = get_gcs_credentials_dict()
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict
    )

    client = storage.Client(
        project=credentials.project_id,
        credentials=credentials,
    )

    bucket = client.bucket(bucket_name)

    # ------------------------------------------------------------------
    # Prepare local target directory
    # ------------------------------------------------------------------
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    local_root = os.path.join(
        base_local_folder, f"bucket_downloaded_{today}"
    )
    os.makedirs(local_root, exist_ok=True)

    # ------------------------------------------------------------------
    # Iterate over all blobs in bucket
    # ------------------------------------------------------------------
    for blob in bucket.list_blobs():
        # Normalize path (GCS paths are always POSIX-style)
        blob_name = blob.name

        # Skip empty names just in case
        if not blob_name:
            continue

        local_path = os.path.join(local_root, blob_name)

        # --------------------------------------------------------------
        # Handle "directory marker" blobs safely
        # --------------------------------------------------------------
        if blob_name.endswith("/"):
            # Ensure directory exists locally
            os.makedirs(local_path, exist_ok=True)
            continue

        # Ensure parent directories exist
        parent_dir = os.path.dirname(local_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        # --------------------------------------------------------------
        # Download file
        # --------------------------------------------------------------
        print(f"Downloading {blob_name} → {local_path}")
        blob.download_to_filename(local_path)

    print("✅ All files downloaded successfully.")


# ----------------------------------------------------------------------
# Example usage
# ----------------------------------------------------------------------
if __name__ == "__main__":
    BUCKET_NAME = "branchekode-selector-bucket"
    BASE_LOCAL_FOLDER = "./data_local"

    download_bucket(BUCKET_NAME, BASE_LOCAL_FOLDER)
