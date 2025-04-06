import json
from collections import deque
from rapidfuzz import process, fuzz

def fuzzy_search(name_search):
    with open('names.json', 'r') as f:
        names = json.load(f)  # Load the list of names from the JSON file

    matches = process.extract(name_search, names, scorer=fuzz.token_set_ratio, limit=5)
    return matches[0]

def generate_relationship_graph(cases_file, decisions_file, individuals_file, parties_file):
    # Load JSON files
    with open(cases_file, 'r') as f:
        cases = json.load(f)
    with open(decisions_file, 'r') as f:
        decisions = json.load(f)
    with open(individuals_file, 'r') as f:
        individuals = json.load(f)
    with open(parties_file, 'r') as f:
        parties = json.load(f)
    
    # Create a mapping for nodes (unique numeric id) and lists for nodes and edges.
    # We use a key prefix ("individual_" or "party_") to avoid id collisions.
    node_map = {}  # key: "individual_{id}" or "party_{id}" -> numeric node id
    nodes = []
    edges = []
    next_id = 0

    # Add nodes for individuals (always use type 'person')
    for ind_id, ind in individuals.items():
        key = f"individual_{ind_id}"
        node_map[key] = next_id
        nodes.append({
            'id': next_id,
            'type': 'profileNode',
            'data': {
                'name': ind['name'],
                'type': 'person'
            }
        })
        next_id += 1

    # Add nodes for parties (use party's own type from JSON)
    for party_id, party in parties.items():
        key = f"party_{party_id}"
        node_map[key] = next_id
        nodes.append({
            'id': next_id,
            'type': 'profileNode',
            'data': {
                'name': party['name'],
                'type': party.get('type', 'party').lower()  # Default to 'party' if no type is provided
            }
        })
        next_id += 1

    # Helper set to avoid duplicate edges (treated as undirected)
    edge_set = set()
    def add_edge(source, target):
        key = tuple(sorted((source, target)))
        if key not in edge_set:
            edge_set.add(key)
            edges.append({'source': key[0], 'target': key[1]})
    
    # 1. Party ↔ Party via Case (entity A -> case_id -> entity B)
    for case in cases.values():
        party_ids = case.get("party_ids", [])
        for i in range(len(party_ids)):
            for j in range(i + 1, len(party_ids)):
                key1 = f"party_{party_ids[i]}"
                key2 = f"party_{party_ids[j]}"
                if key1 in node_map and key2 in node_map:
                    add_edge(node_map[key1], node_map[key2])
    
    # 2. Individual ↔ Individual via Decision (entity A -> decision_id -> entity B)
    for decision in decisions.values():
        individual_ids = decision.get("individual_ids", [])
        for i in range(len(individual_ids)):
            for j in range(i + 1, len(individual_ids)):
                key1 = f"individual_{individual_ids[i]}"
                key2 = f"individual_{individual_ids[j]}"
                if key1 in node_map and key2 in node_map:
                    add_edge(node_map[key1], node_map[key2])
    
    # 3 & 4. Party ↔ Individual via Case–Decision Chain:
    # For each decision, use its associated case to connect each individual (from decision)
    # with each party (from the case)
    for decision in decisions.values():
        case_id = decision.get("case_id")
        individual_ids = decision.get("individual_ids", [])
        if case_id in cases:
            party_ids = cases[case_id].get("party_ids", [])
            for ind in individual_ids:
                for party in party_ids:
                    key1 = f"individual_{ind}"
                    key2 = f"party_{party}"
                    if key1 in node_map and key2 in node_map:
                        add_edge(node_map[key1], node_map[key2])
    
    # Return the final graph
    graph = {
        'nodes': nodes,
        'edges': edges
    }
    return graph

def get_subgraph_by_name(graph, target_name, k):
    """
    Returns a subgraph containing all nodes within k degrees of separation from the node
    with the specified name (target_name). Uses a breadth-first search (BFS) from the target node.
    """
    # Find the node id(s) for the given name.
    target_ids = [node['id'] for node in graph['nodes'] if node['data']['name'] == target_name]
    if not target_ids:
        print(f"No node found with name: {target_name}")
        return None
    
    target_id = target_ids[0]  # Use the first match if there are multiple
    
    # Build an adjacency list from the graph's edges.
    adj = {node['id']: set() for node in graph['nodes']}
    for edge in graph['edges']:
        source = edge['source']
        target = edge['target']
        adj[source].add(target)
        adj[target].add(source)
    
    # BFS to find nodes within k degrees
    visited = {target_id: 0}
    queue = deque([target_id])
    
    while queue:
        current = queue.popleft()
        current_depth = visited[current]
        if current_depth < k:
            for neighbor in adj[current]:
                if neighbor not in visited:
                    visited[neighbor] = current_depth + 1
                    queue.append(neighbor)
    
    # Collect nodes and edges in the visited set.
    sub_nodes = [node for node in graph['nodes'] if node['id'] in visited]
    visited_ids = set(visited.keys())
    sub_edges = [edge for edge in graph['edges']
                 if edge['source'] in visited_ids and edge['target'] in visited_ids]
    
    subgraph = {'nodes': sub_nodes, 'edges': sub_edges}
    return subgraph

if __name__ == '__main__':
    cases_path = 'cases.json'
    decisions_path = 'decisions.json'
    individuals_path = 'individuals.json'
    parties_path = 'parties.json'
    
    graph = generate_relationship_graph(cases_path, decisions_path, individuals_path, parties_path)
    
    target_name = 'United Operations Limited'
    k = 2  # Adjust k as needed
    
    subgraph = get_subgraph_by_name(graph, target_name, k)
    if subgraph:
        print(json.dumps(subgraph, indent=4))
