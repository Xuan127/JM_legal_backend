import json
from collections import deque
from rapidfuzz import process, fuzz
from itertools import combinations # Needed for pairwise iteration

def fuzzy_search(name_search):
    with open('names.json', 'r') as f:
        names = json.load(f)  # Load the list of names from the JSON file

    matches = process.extract(name_search, names, scorer=fuzz.token_set_ratio, limit=5)
    return matches[0][0]

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
            'id': str(next_id),
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
            'id': str(next_id),
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
            edges.append({'source': str(key[0]), 
                          'target': str(key[1]),
                          'id': str(key[0]) + '_' + str(key[1])})
    
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
    Only includes edges that were actually traversed during the BFS.
    """
    # Find the node id(s) for the given name.
    target_ids = [node['id'] for node in graph['nodes'] if node['data']['name'] == target_name]
    if not target_ids:
        print(f"No node found with name: {target_name}")
        return None
    
    target_id = target_ids[0]  # Use the first match if there are multiple
    
    # Build an adjacency list from the graph's edges with edge references
    edge_map = {}  # (node1, node2) -> edge object
    for edge in graph['edges']:
        source, target = edge['source'], edge['target']
        edge_map[(source, target)] = edge
        edge_map[(target, source)] = edge  # Add both directions for undirected graph
    
    adj = {node['id']: set() for node in graph['nodes']}
    for edge in graph['edges']:
        source = edge['source']
        target = edge['target']
        adj[source].add(target)
        adj[target].add(source)
    
    # BFS to find nodes within k degrees
    visited = {target_id: 0}
    queue = deque([target_id])
    # Track parent nodes to reconstruct the traversal path
    parents = {target_id: None}
    
    while queue:
        current = queue.popleft()
        current_depth = visited[current]
        if current_depth < k:
            for neighbor in adj[current]:
                if neighbor not in visited:
                    visited[neighbor] = current_depth + 1
                    parents[neighbor] = current
                    queue.append(neighbor)
    
    # Collect nodes in the visited set
    sub_nodes = [node for node in graph['nodes'] if node['id'] in visited]
    
    # Only include edges that were traversed during BFS
    sub_edges = []
    traversed_edges = set()
    
    # For each node (except the start node), add the edge from its parent
    for node_id, parent_id in parents.items():
        if parent_id is not None:  # Skip the start node
            # Create a unique key for this edge
            edge_key = tuple(sorted([parent_id, node_id]))
            if edge_key not in traversed_edges:
                traversed_edges.add(edge_key)
                # Find the actual edge object
                edge = edge_map.get((parent_id, node_id)) or edge_map.get((node_id, parent_id))
                if edge:
                    sub_edges.append(edge)
    
    subgraph = {'nodes': sub_nodes, 'edges': sub_edges}
    return subgraph

def get_union_subgraph_by_names(graph, target_names, k):
    """
    Returns a subgraph containing the union of nodes and edges found within 
    k degrees of separation from any node with a name in target_names.
    
    Parameters:
      graph: dict with keys 'nodes' and 'edges'
      target_names: list of names to search for
      k: degrees of separation
      
    Returns:
      A dictionary representing the union subgraph with keys 'nodes' and 'edges'.
      If no starting node is found for any name, those names are skipped.
    """
    # Initialize empty union subgraph
    union_subgraph = {'nodes': [], 'edges': []}
    node_ids_in_union = set()
    edge_ids_in_union = set()
    
    # For each target name, get its subgraph and add to the union
    for name in target_names:
        subgraph = get_subgraph_by_name(graph, name, k)
        if subgraph:
            # Add new nodes
            for node in subgraph['nodes']:
                if node['id'] not in node_ids_in_union:
                    node_ids_in_union.add(node['id'])
                    union_subgraph['nodes'].append(node)
            
            # Add new edges
            for edge in subgraph['edges']:
                edge_id = edge['id']
                if edge_id not in edge_ids_in_union:
                    edge_ids_in_union.add(edge_id)
                    union_subgraph['edges'].append(edge)
    
    if not union_subgraph['nodes']:
        print("No valid nodes found for any of the given names.")
        return None
        
    return union_subgraph

def get_connecting_paths_subgraph(graph, target_names, k):
    """
    Identifies shortest paths (up to length k) between all pairs of nodes
    corresponding to target_names. Returns a subgraph containing only the nodes
    and edges lying on these paths. Performs fuzzy matching on names.
    """
    # --- Preprocessing ---
    # Build adjacency list
    adj = {node['id']: set() for node in graph['nodes']}
    for edge in graph['edges']:
        adj[edge['source']].add(edge['target'])
        adj[edge['target']].add(edge['source'])

    # Build efficient lookup for edge objects based on pairs of nodes
    edge_lookup = {}
    for edge in graph['edges']:
        key = tuple(sorted((edge['source'], edge['target'])))
        edge_lookup[key] = edge

    # Find node IDs for target names, performing fuzzy matching
    target_node_ids = set()
    # Use precomputed map if available, otherwise create it
    name_to_id_map = graph.get('name_to_id', {node['data']['name']: node['id'] for node in graph['nodes']})

    valid_target_names_found = [] # Store the names corresponding to the found IDs

    print("Attempting to find nodes for target names:")
    for name in target_names:
        node_id = None
        name_that_worked = None
        potential_fuzzy_name = name # Initialize potential fuzzy name

        # 1. Try exact match first
        exact_node_id = name_to_id_map.get(name)
        if exact_node_id:
            node_id = exact_node_id
            name_that_worked = name
            print(f" - Found exact match for '{name}' -> ID: {node_id}")
        else:
            # 2. Try fuzzy match if exact failed
            print(f" - No exact match for '{name}', trying fuzzy search...")
            potential_fuzzy_name = fuzzy_search(name) # Perform fuzzy search
            # Check if fuzzy search found something different AND it's in the map
            if potential_fuzzy_name != name:
                fuzzy_node_id = name_to_id_map.get(potential_fuzzy_name)
                if fuzzy_node_id:
                    node_id = fuzzy_node_id
                    name_that_worked = potential_fuzzy_name
                    print(f"   - Found fuzzy match: '{name}' -> '{name_that_worked}' -> ID: {node_id}")
                # else: # Fuzzy name found, but not in map (should be rare if names.json is from graph)
                #    print(f"   - Fuzzy match '{potential_fuzzy_name}' found, but not present in graph nodes.")

        # 3. Process the result for this name
        if node_id:
            target_node_ids.add(node_id)
            if name_that_worked not in valid_target_names_found: # Avoid duplicates in the list message
                valid_target_names_found.append(name_that_worked)
        else:
            # Only print warning if both exact and fuzzy failed
            print(f"   - Warning: Could not find node for target name: '{name}' (tried fuzzy: '{potential_fuzzy_name}')")


    print(f"Proceeding with found nodes for: {valid_target_names_found}")

    if len(target_node_ids) < 2:
        print("Need at least two valid target nodes to find connecting paths.")
        # Return only the found target nodes, if any, with no edges
        final_nodes = [node for node in graph['nodes'] if node['id'] in target_node_ids]
        return {'nodes': final_nodes, 'edges': []}

    # --- Path Finding (BFS for each pair) ---
    nodes_on_paths = set(target_node_ids) # Start with target nodes
    edges_on_paths = set() # Store edge IDs (or unique edge keys)

    # Iterate through all unique pairs of target node IDs
    for start_node_id, end_node_id in combinations(target_node_ids, 2):
        # Perform BFS from start_node_id to find end_node_id within k steps
        queue = deque([(start_node_id, [start_node_id])]) # (current_node, path_list)
        # Visited optimization: Keep track of nodes visited *per BFS pair* and their distance
        visited_bfs = {start_node_id: 0} # node_id -> distance from start_node_id

        shortest_path_found = None

        while queue:
            current_id, path = queue.popleft()
            current_depth = len(path) - 1 # = distance from start_node_id

            # Check if we reached the target
            if current_id == end_node_id:
                 # Found a path. Since BFS guarantees shortest path first, store it and break.
                 shortest_path_found = path
                 break

            # Stop exploring if path length exceeds k
            if current_depth >= k:
                continue

            # Explore neighbors
            for neighbor_id in adj.get(current_id, set()):
                # Add neighbor only if it's unvisited in this BFS or offers a shorter path (unlikely in basic BFS but good practice)
                # and the new path length does not exceed k
                if neighbor_id not in visited_bfs or visited_bfs[neighbor_id] > current_depth + 1:
                    if current_depth + 1 <= k:
                        visited_bfs[neighbor_id] = current_depth + 1
                        new_path = list(path)
                        new_path.append(neighbor_id)
                        queue.append((neighbor_id, new_path))

        # If a path was found for this pair, add its nodes and edges
        if shortest_path_found:
            # print(f"  - Found path (k={len(shortest_path_found)-1}) between {start_node_id} and {end_node_id}: {' -> '.join(shortest_path_found)}") # Debugging paths
            nodes_on_paths.update(shortest_path_found)
            for i in range(len(shortest_path_found) - 1):
                u, v = shortest_path_found[i], shortest_path_found[i+1]
                edge_key = tuple(sorted((u, v)))
                edge_object = edge_lookup.get(edge_key)
                if edge_object:
                    # Ensure the edge object has an ID before adding
                    edge_id = edge_object.get('id')
                    if not edge_id: # Fallback if somehow ID was missing
                         edge_id = f"e_{edge_key[0]}_{edge_key[1]}"
                         edge_object['id'] = edge_id # Assign ID back for consistency
                    edges_on_paths.add(edge_id)
                else:
                     # This indicates an inconsistency between adj list and edge_lookup
                     print(f"Warning: Edge between {u} and {v} expected from BFS path but not found in edge_lookup.")

    # --- Construct Final Subgraph ---
    final_nodes = [node for node in graph['nodes'] if node['id'] in nodes_on_paths]
    final_edges = [edge for edge in graph['edges'] if edge.get('id') in edges_on_paths] # Use .get() for safety

    return {'nodes': final_nodes, 'edges': final_edges}

if __name__ == '__main__':
    
    # Example usage of the functions in this module.
    graph = generate_relationship_graph('cases.json', 'decisions.json', 'individuals.json', 'parties.json')
    
    # Test single name subgraph
    # subgraph = get_subgraph_by_name(graph, 'Egypt', 2)
    # print(json.dumps(subgraph, indent=4))

    # Test union of multiple names
    subgraph_union = get_connecting_paths_subgraph(graph, ["Sophia Jaeger", "United Operations Limited", "Jacqueline J. Bronsdon", "Bellwether International, Inc"], 2)
    print(f"Number of nodes: {len(subgraph_union['nodes'])}")
    print(f"Number of edges: {len(subgraph_union['edges'])}")
    print(json.dumps(subgraph_union, indent=4))
