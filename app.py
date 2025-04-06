# 1. Import the Flask class
from flask import Flask

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

# 5. Run the application
if __name__ == '__main__':
    app.run(debug=True)