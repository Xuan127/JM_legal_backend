import json
import pickle
import os
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from functools import partial

# Import functions from original script
from call_jusmundi import (
    list_cases,
    parse_case, 
    get_decision,
    get_individual,
    get_party
)

# Worker functions for parallel processing

def process_individual(individual_id, decision_id, shared_individuals):
    """Process an individual and store in shared dictionary"""
    try:
        individual_data = get_individual(individual_id)
        individual_data["decision_id"] = decision_id
        shared_individuals[individual_id] = individual_data
        return True
    except Exception as e:
        print(f"Error processing individual {individual_id}: {e}")
        return False

def process_decision(decision_id, case_id, shared_decisions, shared_individuals):
    """Process a decision and its individuals, store in shared dictionaries"""
    try:
        decision_data = get_decision(decision_id)
        decision_data["case_id"] = case_id
        shared_decisions[decision_id] = decision_data
        
        individual_ids = decision_data.get("individual_ids", [])
        
        # Process individuals in parallel within this worker
        with ProcessPoolExecutor(max_workers=3) as executor:
            func = partial(process_individual, decision_id=decision_id, shared_individuals=shared_individuals)
            results = list(executor.map(func, individual_ids))
            
        return True
    except Exception as e:
        print(f"Error processing decision {decision_id}: {e}")
        return False

def process_party(party_id, case_id, shared_parties):
    """Process a party and store in shared dictionary"""
    try:
        party_data = get_party(party_id)
        party_data["case_id"] = case_id
        shared_parties[party_id] = party_data
        return True
    except Exception as e:
        print(f"Error processing party {party_id}: {e}")
        return False

def process_case(case_id, case_info, shared_decisions, shared_individuals, shared_parties):
    """Process a case and its related data"""
    try:
        # Process decisions and their individuals
        decision_ids = case_info["decision_ids"]
        with ProcessPoolExecutor(max_workers=3) as executor:
            func = partial(
                process_decision,
                case_id=case_id,
                shared_decisions=shared_decisions,
                shared_individuals=shared_individuals
            )
            decision_results = list(executor.map(func, decision_ids))
        
        # Process parties
        party_ids = case_info["party_ids"]
        with ProcessPoolExecutor(max_workers=3) as executor:
            func = partial(
                process_party,
                case_id=case_id,
                shared_parties=shared_parties
            )
            party_results = list(executor.map(func, party_ids))
            
        return True
    except Exception as e:
        print(f"Error processing case {case_id}: {e}")
        return False

def main():
    # Create manager for shared dictionaries between processes
    with Manager() as manager:
        # Shared dictionaries to store data
        shared_cases = manager.dict()
        shared_decisions = manager.dict()
        shared_individuals = manager.dict()
        shared_parties = manager.dict()
        
        start_time = time.time()
        
        # Number of pages to process (set to 1 for testing, can be increased)
        num_pages = 200
        
        # Get cases from API
        for page in range(num_pages):
            print(f"Processing page {page+1}/{num_pages}...")
            
            # Get and parse cases
            case_data = list_cases(page)
            cases_batch = parse_case(case_data)
            shared_cases.update(cases_batch)
            
            case_ids = list(cases_batch.keys())
            
            # Process all cases in parallel
            with ProcessPoolExecutor(max_workers=3) as executor:
                func = partial(
                    process_case,
                    shared_decisions=shared_decisions,
                    shared_individuals=shared_individuals,
                    shared_parties=shared_parties
                )
                
                # Map each case_id and its info to the process_case function
                case_args = [(case_id, cases_batch[case_id]) for case_id in case_ids]
                results = list(executor.map(lambda args: func(*args), case_args))
        
        # Convert shared dictionaries to regular dictionaries for saving
        cases_dict = dict(shared_cases)
        decisions_dict = dict(shared_decisions)
        individuals_dict = dict(shared_individuals)
        parties_dict = dict(shared_parties)
        
        end_time = time.time()
        print(f"Total processing time: {end_time - start_time:.2f} seconds")
        
        # Save results to files
        print("Saving results to files...")
        
        # Save as pickle files
        with open('cases_mp.pkl', 'wb') as f:
            pickle.dump(cases_dict, f)
        
        with open('decisions_mp.pkl', 'wb') as f:
            pickle.dump(decisions_dict, f)
        
        with open('individuals_mp.pkl', 'wb') as f:
            pickle.dump(individuals_dict, f)
        
        with open('parties_mp.pkl', 'wb') as f:
            pickle.dump(parties_dict, f)
        
        print("Done!")

if __name__ == "__main__":
    # Set the number of processes to use
    num_cpu = min(4, os.cpu_count())
    print(f"Using {num_cpu} CPU cores for processing")
    main()
