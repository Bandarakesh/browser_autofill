import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from core.llm import get_llm, model
from core.profile_manager import ProfileManager
from agent.state import AgentState

llm = get_llm()
llm_json = llm.bind(response_format={"type": "json_object"})
profile_manager = ProfileManager()

def analyze_form(state: AgentState) -> AgentState:
    """Analyze the page screenshot and DOM to identify form fields."""
    if not state.get("page_screenshot") and not state.get("page_dom"):
        return state

    prompt = f"""You are an expert web scraping AI.
Analyze the following HTML DOM snippet and the provided screenshot to identify all input fields, radio buttons, checkboxes, selects, and buttons in the form.
DOM:
{state['page_dom']}

Return a JSON object with a single key 'fields' containing a list of objects. Each object must have:
- 'id': the id or name attribute of the field (use a descriptive name if missing)
- 'type': 'text', 'email', 'radio', 'checkbox', 'button', 'select', 'file', 'submit', etc.
- 'label': the human-readable label for this field
- 'required': true or false

Reply STRICTLY in JSON format with no extra text outside the JSON.
"""
    # Build message — vision if screenshot available, text-only fallback
    if state.get("page_screenshot"):
        # IMPORTANT: The image URL MUST include the full data URI prefix.
        # background.js strips "data:image/jpeg;base64," before sending, so we re-add it here.
        image_data_url = f"data:image/jpeg;base64,{state['page_screenshot']}"
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url,
                            "detail": "auto"  # let OpenAI choose resolution
                        },
                    },
                ]
            )
        ]
        print(f"[analyze_form] Sending vision request. Image data URL length: {len(image_data_url)}")
    else:
        messages = [HumanMessage(content=prompt)]
        print("[analyze_form] No screenshot available, using DOM-only analysis.")

    # Use plain llm (NOT llm_json) for vision — response_format=json_object
    # can conflict with vision inputs in some LangChain/OpenAI versions.
    # We parse the JSON manually from the text response instead.
    response = llm.invoke(messages)
    print(f"[analyze_form] Raw LLM response: {response.content[:300]}")

    try:
        # Strip markdown code fences if the model wraps in ```json ... ```
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        state["form_fields"] = data.get("fields", [])
        print(f"[analyze_form] Identified {len(state['form_fields'])} form fields.")
    except Exception as e:
        print(f"[analyze_form] JSON parse error: {e}. Raw: {response.content[:200]}")
        state["form_fields"] = []

    return state


def process_user_response(state: AgentState) -> AgentState:
    """If there's a user response, extract info and update profile."""
    if state.get("user_response"):
        prompt = f"""The user answered the question: "{state.get('question_for_user')}"
Answer: "{state['user_response']}"

Extract the key-value pairs of information from this answer to add to their profile.
Return a JSON object with a single key 'profile_data' containing the key-value pairs.
"""
        response = llm_json.invoke([HumanMessage(content=prompt)])
        try:
            data = json.loads(response.content)
            new_data = data.get("profile_data", {})
            profile_manager.update_profile(new_data)
            state["user_profile"] = profile_manager.load_profile()
        except:
            pass
        # Clear the response after processing
        state["user_response"] = None
        state["question_for_user"] = None
        
    return state

def map_data(state: AgentState) -> AgentState:
    """Map known user profile data to the form fields."""
    prompt = f"""You are mapping a user's profile to web form fields.
User Profile: {json.dumps(state['user_profile'])}
Form Fields: {json.dumps(state['form_fields'])}

Determine which fields can be filled using the user's profile, and which fields are missing required information.
Return a JSON object with two keys:
'mapped_data': a list of objects, each containing 'id' (the field id/selector) and 'value' (the value to fill).
'missing_fields': a list of field objects that require information not found in the profile.
"""
    response = llm_json.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(response.content)
        state["mapped_data"] = data.get("mapped_data", [])
        state["missing_fields"] = data.get("missing_fields", [])
    except:
        state["mapped_data"] = []
        state["missing_fields"] = state.get("form_fields", [])
        
    if state["missing_fields"]:
        state["status"] = "ask"
    else:
        state["status"] = "fill"
        
    return state

def generate_question(state: AgentState) -> AgentState:
    """Generate a question for the user to get missing info."""
    missing = state.get("missing_fields", [])
    if not missing:
        state["status"] = "fill"
        return state
        
    # Just ask about the first few missing fields to not overwhelm
    fields_to_ask = missing[:3]
    prompt = f"""You need to ask the user for information to fill out a form.
The following fields are missing: {json.dumps(fields_to_ask)}

Generate a friendly, concise question to ask the user for this information. The user can reply via voice or text.
Return a JSON object with a key 'question' containing the string.
"""
    response = llm_json.invoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(response.content)
        state["question_for_user"] = data.get("question", "I need some more information to complete this form. Can you provide it?")
    except:
         state["question_for_user"] = "Please provide the missing information."
         
    return state

def generate_actions(state: AgentState) -> AgentState:
    """Generate browser actions to fill the form."""
    actions = []
    for item in state.get("mapped_data", []):
        actions.append({
            "action": "type",
            "selector": f"[id='{item['id']}'], [name='{item['id']}']",
            "value": item['value']
        })
    
    # We could also look for a submit button in form_fields
    for field in state.get("form_fields", []):
        if field.get("type") in ["submit", "button"] and "submit" in str(field.get("label", "")).lower():
            # Don't auto-submit for safety during testing, but here's how:
            # actions.append({"action": "click", "selector": f"[id='{field['id']}'], [name='{field['id']}']"})
            pass
            
    state["actions_to_take"] = actions
    state["status"] = "fill"
    return state
