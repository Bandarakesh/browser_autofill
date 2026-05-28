from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    page_screenshot: str  # Base64 string of the image
    page_dom: str         # Text of DOM or representation
    form_fields: List[Dict[str, Any]] # Fields identified on the page
    user_profile: Dict[str, Any] # Data we have about the user
    mapped_data: Dict[str, Any] # Data successfully mapped to form fields
    missing_fields: List[Dict[str, Any]] # Fields we don't have info for
    actions_to_take: List[Dict[str, Any]] # Commands for the extension
    user_response: Optional[str] # Answer from the user (if asked)
    status: str # "analyze", "ask", "fill"
    question_for_user: Optional[str] # The question we want to ask
