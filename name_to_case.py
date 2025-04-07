import json

def load_data():
    """Load data from JSON files."""
    with open("cases.json", "r") as f:
        cases = json.load(f)
    with open("decisions.json", "r") as f:
        decisions = json.load(f)
    with open("individuals.json", "r") as f:
        individuals = json.load(f)
    with open("parties.json", "r") as f:
        parties = json.load(f)
    return cases, decisions, individuals, parties

def get_case_name(name: str) -> str:
    """
    Given the name of an individual or a party (of type person), return the case name.
    
    The function first checks the individuals list by matching the name.
    If found, it retrieves the decision associated with that individual, then looks up the corresponding case.
    If not found, it searches the parties (filtering for type "Person") for the name.
    
    Parameters:
        name (str): The name of the individual or person-type party.
    
    Returns:
        str: The title of the case if found, or an error message.
    """
    # Load our datasets from JSON files
    cases, decisions, individuals, parties = load_data()

    # First, try to find the name in individuals.json
    for ind in individuals.values():
        if ind.get("name") == name:
            decision_id = ind.get("decision_id")
            decision = decisions.get(decision_id)
            if decision:
                case_id = decision.get("case_id")
                case = cases.get(case_id)
                if case:
                    return case.get("title", "Case title not found")
                else:
                    return "Case not found for the given decision."
            else:
                return "Decision not found for the individual."

    # Next, try to find the name in parties.json with type 'Person'
    for party in parties.values():
        if party.get("name") == name and party.get("type", "").lower() == "person":
            case_id = party.get("case_id")
            case = cases.get(case_id)
            if case:
                return case.get("title", "Case title not found")
            else:
                return "Case not found for the party."

    # If no match is found, return an appropriate message.
    return "Name not found in individuals or person-type parties."

# Example usage:
if __name__ == "__main__":
    # Replace 'Your Name Here' with the actual name to search for.
    search_name = "Hüseyin Avni Kiper"  
    result = get_case_name(search_name)
    print(f"Case for '{search_name}': {result}")
