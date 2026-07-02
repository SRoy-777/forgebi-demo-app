import time
import requests
from typing import List, Dict, Any
from backend.api.config import settings

class BusinessCentralClient:
    """
    Strictly READ-ONLY client for interacting with Microsoft Business Central 365 OData APIs.
    Enforces authentication via OAuth 2.0 Client Credentials and handles paginated requests.
    """
    def __init__(self) -> None:
        self.client_id: str = settings.BC_CLIENT_ID
        self.client_secret: str = settings.BC_CLIENT_SECRET
        self.token_url: str = settings.BC_ACCESS_TOKEN_URL
        self.scope: str = settings.BC_SCOPE
        self.base_url: str = settings.BC_BASE_URL

        self._access_token: str = ""
        self._token_expires_at: float = 0.0

    def _get_access_token(self) -> str:
        """
        Retrieves a valid access token from Microsoft, using in-memory caching and automatic refresh.
        """
        # If the token is still valid (with a 60-second buffer), return it
        if self._access_token and time.time() < (self._token_expires_at - 60):
            return self._access_token

        print("[BC Gateway] Refreshing OAuth 2.0 Access Token...")
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope
        }
        
        try:
            response = requests.post(self.token_url, data=payload, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in
            print(f"[BC Gateway] Token refreshed successfully. Expires in {expires_in} seconds.")
            return self._access_token
        except Exception as e:
            print(f"[BC Gateway] Error retrieving access token: {e}")
            raise ConnectionError("Authentication with Business Central failed.") from e

    def get_all_records(self, endpoint_set: str, params: dict = None) -> List[Dict[str, Any]]:
        """
        Strictly READ-ONLY query.
        Fetches all records for the given endpoint set, recursively following OData pagination links (@odata.nextLink).
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Clean endpoint set if it has leading slash
        endpoint_set = endpoint_set.lstrip('/')
        url = f"{self.base_url}/{endpoint_set}"
        
        all_records: List[Dict[str, Any]] = []
        page_count = 1

        print(f"[BC Gateway] Starting data extraction from: {endpoint_set}")
        
        while url:
            retries = 3
            success = False
            while retries > 0 and not success:
                try:
                    print(f"[BC Gateway] Fetching page {page_count} (Retries left: {retries - 1})...")
                    # Use params only on the first page; nextLink already contains all parameters
                    current_params = params if page_count == 1 else None
                    response = requests.get(url, headers=headers, params=current_params, timeout=90)
                    response.raise_for_status()
                    data = response.json()
                    
                    records = data.get("value", [])
                    all_records.extend(records)
                    
                    # Check for next page URL
                    url = data.get("@odata.nextLink", "")
                    success = True
                    if url:
                        page_count += 1
                except (requests.Timeout, requests.ConnectionError) as e:
                    retries -= 1
                    print(f"[BC Gateway] Network warning page {page_count}: {e}. Retrying...")
                    if retries == 0:
                        raise ConnectionError(f"OData retrieval failed for endpoint '{endpoint_set}' on page {page_count} after 3 attempts.") from e
                    time.sleep(5)  # Wait 5 seconds before retrying
                except Exception as e:
                    # Non-transient error, raise immediately
                    print(f"[BC Gateway] Fatal error fetching page {page_count}: {e}")
                    raise ConnectionError(f"OData retrieval failed for endpoint '{endpoint_set}' on page {page_count}.") from e


        print(f"[BC Gateway] Extraction complete. Total records retrieved: {len(all_records)}")
        return all_records
