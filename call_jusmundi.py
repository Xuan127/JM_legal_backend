import requests
import json, pickle
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

def list_cases(page):
    url = f"https://api.jusmundi.com/stanford/cases?page={page}&count=10"

    headers = {
        "accept": "application/json",
        "X-API-Key": os.environ.get("JUSMUNDI_API_KEY")  # Make sure to set this in your .env file or environment
    }

    response = requests.get(url, headers=headers)

    return response.json()  # Parse the JSON response and return it

def parse_case(case_data):
    # Dictionary to store case-specific decisions and parties
    case_details = {}

    # Parse each case entry
    for case in case_data["data"]:
        case_id = case.get("id")
        attributes = case.get("attributes", {})

        # Initialize lists for this specific case
        case_details[case_id] = {
            "title": attributes.get("title", ""),
            "commencement_date": attributes.get("commencement_date", ""),
            "arbitral_institution": attributes.get("organization", ""),
            "outcome": attributes.get("outcome", ""),
            "decision_ids": [],
            "party_ids": []
        }
        
        # Extract decisions
        decisions = case.get("relationships", {}).get("decisions", {}).get("data", [])
        for decision in decisions:
            decision_id = decision.get("id")
            if decision_id:
                case_details[case_id]["decision_ids"].append(decision_id)

        # Extract parties
        parties = case.get("relationships", {}).get("parties", {}).get("data", [])
        for party in parties:
            party_id = party.get("id")
            if party_id:
                case_details[case_id]["party_ids"].append(party_id)

    return case_details  # Return the parsed case details for further processing

def get_decision(id):
    url = f"https://api.jusmundi.com/stanford/decisions/{id}"

    headers = {
        "accept": "application/json",
        "X-API-Key": os.environ.get("JUSMUNDI_API_KEY")  # Make sure to set this in your .env file or environment
    }

    response = requests.get(url, headers=headers)

    data = response.json()  # Parse the JSON response and return it
    decision = data["data"]

    # Extract attributes
    decision_id = decision.get("id")
    attributes = decision.get("attributes", {})
    content = attributes.get("content", "")  # In case content is needed for further processing
    decision_date = attributes.get("date", "")
    organization = attributes.get("organization", "")
    reference = attributes.get("reference", "")
    title = attributes.get("title", "")


    # Extract list of individual IDs
    individuals_data = decision.get("relationships", {}).get("individuals", {}).get("data", [])
    individual_ids = [ind.get("id") for ind in individuals_data]

    decisition_data = {
        "decision_id": decision_id,
        "content": content,
        "decision_date": decision_date,
        "organization": organization,
        "reference": reference,
        "title": title,
        "individual_ids": individual_ids
    }
    return decisition_data  # Return the decision data for further processing

def get_individual(id):
    url = f"https://api.jusmundi.com/stanford/individuals/{id}"

    headers = {
        "accept": "application/json",
        "X-API-Key": os.environ.get("JUSMUNDI_API_KEY")  # Make sure to set this in your .env file or environment
    }

    response = requests.get(url, headers=headers)

    data = response.json()  # Parse the JSON response and return it
    individual = data["data"]

    # Extract attributes
    decision_id = individual.get("id")
    attributes = individual.get("attributes", {})
    name = attributes.get("name", "")  # In case content is needed for further processing
    nationality = attributes.get("nationality", "")
    firm = attributes.get("firm", "")  # Optional, if you need to display the firm associated with the individual
    role = attributes.get("role", "")  # Optional, if you need to display the role of the individual
    type_ = attributes.get("type", "")  # Optional, if you need to display the type of the individual (e.g., judge, arbitrator)

    individual_data = {
        "id": decision_id,
        "name": name,
        "nationality": nationality,
        "firm": firm,
        "role": role,
        "type": type_
    }
    return individual_data  # Return the individual data for further processing

def get_party(id):
    url = f"https://api.jusmundi.com/stanford/parties/{id}"

    headers = {
        "accept": "application/json",
        "X-API-Key": os.environ.get("JUSMUNDI_API_KEY")  # Make sure to set this in your .env file or environment
    }

    response = requests.get(url, headers=headers)

    data = response.json()  # Parse the JSON response and return it
    party = data["data"]

    # Extract attributes
    party_id = party.get("id")
    attributes = party.get("attributes", {})
    name = attributes.get("name", "")  # In case content is needed for further processing
    nationality = attributes.get("nationality", "")
    role = attributes.get("role", "")  # Optional, if you need to display the role of the party (e.g., claimant, respondent)
    type_ = attributes.get("type")

    party_data = {
        "id": party_id,
        "name": name,
        "nationality": nationality,
        "role": role,
        "type": type_
    }
    return party_data  # Return the party data for further processing

cases = {}
decisions = {}
individuals = {}
parties = {}
for i in range(10):
    print(f"Processing page {i + 1}...")  # Print the current page being processed for debugging
    case = parse_case(list_cases(i))  # Loop through the first 5 pages to get cases
    cases.update(case)  # Merge the parsed cases into the main cases dictionary

    case_ids = list(case.keys())  # Get the case IDs for this batch of cases
    for case_id in case_ids:
        # For each decision ID in the case, fetch the decision details
        decision_ids = case[case_id]["decision_ids"]
        for decision_id in decision_ids:
            decision_data = get_decision(decision_id)  # Fetch and print decision details
            decision_data["case_id"] = case_id  # Link the decision to its case
            decisions[decision_id] = decision_data
            individual_ids = decision_data.get("individual_ids", [])
            for individual_id in individual_ids:
                individual_data = get_individual(individual_id)  # Fetch and print individual details
                individual_data["decision_id"] = decision_id  # Link the individual to its decision
                individuals[individual_id] = individual_data    

        # For each party ID in the case, fetch the party details
        party_ids = case[case_id]["party_ids"]
        for party_id in party_ids:
            party_data = get_party(party_id)  # Fetch and print party details
            party_data["case_id"] = case_id
            parties[party_id] = party_data

names = []
for person in individuals.values():
    if 'name' in person:
        names.append(person['name'])

# Extract names from parties
for party in parties.values():
    if 'name' in party:
        names.append(party['name'])

# Save as JSON files
with open('cases.json', 'w') as f:
    json.dump(cases, f, indent=4)

# with open('cases.pkl', 'wb') as f:
#     pickle.dump(cases, f)

with open('decisions.json', 'w') as f:
    json.dump(decisions, f, indent=4)

# with open('decisions.pkl', 'wb') as f:
#     pickle.dump(decisions, f)

with open('individuals.json', 'w') as f:
    json.dump(individuals, f, indent=4)

# with open('individuals.pkl', 'wb') as f:
#     pickle.dump(individuals, f)

with open('parties.json', 'w') as f:
    json.dump(parties, f, indent=4)

# with open('parties.pkl', 'wb') as f:
#     pickle.dump(parties, f)

with open('names.json', 'w') as f:
    json.dump(names, f, indent=4)