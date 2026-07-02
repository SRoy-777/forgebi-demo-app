from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.api.clients.bc_client import BusinessCentralClient

router = APIRouter(prefix="/api/tags", tags=["tags"])
bc_client = BusinessCentralClient()

@router.get("/{tag_no:path}")
def get_tag_by_no(tag_no: str) -> Dict[str, Any]:
    """
    Strictly READ-ONLY chatbot endpoint.
    Retrieves live real-time tag information directly from Business Central by Tag Number.
    """
    try:
        # Fetch tag using OData filtering ($filter)
        endpoint = "ACXTagHeadersAPIJRS"
        params = {"$filter": f"tagNo eq '{tag_no}'"}
        
        records = bc_client.get_all_records(endpoint, params=params)
        if not records:
            raise HTTPException(status_code=404, detail=f"Tag '{tag_no}' not found in Business Central.")
            
        return records[0]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error querying live Tag details: {str(e)}")
