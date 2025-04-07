from gemini_llm import search, generate
from name_to_case import get_case_name

def get_profile_from_name(name: str) -> str:
    case_name = get_case_name(name)
    case_info = search(f"Get me the general information about the case named {case_name}, including the involved parties and their profiles.")
    print(f"Case Info: {case_info}")  # For debugging, to see the case information
    return None
    
print(get_profile_from_name("Sophia Jaeger"))  # Example usage, replace with actual name to test