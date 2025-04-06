# 1. Import the Flask class
from flask import Flask
from flask import request
import json
from draw_graph import generate_relationship_graph, get_subgraph_by_name

# 2. Create an instance of the Flask class
#    __name__ tells Flask where to look for resources like templates and static files.
app = Flask(__name__)

# 3. Define a route and the function to handle requests for that route
#    The @app.route('/') decorator binds the URL '/' (the root) to the hello_world function.
@app.route('/')
def hello_world():
    """This function runs when someone visits the root URL."""
    return 'Hello, World!'

# 4. Add another simple route (optional, but good practice)
@app.route('/about')
def about_page():
    """This function runs when someone visits the /about URL."""
    return 'This is a simple Flask application!'

@app.route('/query_to_graph', methods=['POST'])
def query_to_graph():
    """This function echoes back the request data."""
    query = request.get_json().get('query', '')

    cases_path = 'cases.json'
    decisions_path = 'decisions.json'
    individuals_path = 'individuals.json'
    parties_path = 'parties.json'
    
    graph = generate_relationship_graph(cases_path, decisions_path, individuals_path, parties_path)

    k = 2  # Adjust k as needed
    
    subgraph = get_subgraph_by_name(graph, query, k)
    return json.dumps(subgraph, indent=4)

@app.route('/full_graph', methods=['GET'])
def full_graph():
    cases_path = 'cases.json'
    decisions_path = 'decisions.json'
    individuals_path = 'individuals.json'
    parties_path = 'parties.json'
    
    graph = generate_relationship_graph(cases_path, decisions_path, individuals_path, parties_path)
    return json.dumps(graph, indent=4)

# 5. Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)