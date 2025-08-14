import datetime
from flask import Flask, request, render_template_string
from markupsafe import Markup

# Initialize the Flask application
app = Flask(__name__)

# In-memory storage for captured requests.
# For a production app, you would use a database.
requests_log = []

# HTML Template with embedded CSS for styling.
# This makes the app a single, self-contained file.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTTP Request Catcher</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            margin: 0;
            padding: 2rem;
        }
        .container {
            max-width: 900px;
            margin: auto;
        }
        h1, h2 {
            color: #4a90e2;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        .info-box {
            background-color: #2a2a2a;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            word-wrap: break-word;
        }
        .info-box code {
            background-color: #333;
            color: #lightgreen;
            padding: 2px 5px;
            border-radius: 4px;
        }
        .request-card {
            background-color: #252525;
            border: 1px solid #444;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        .request-header {
            background-color: #333;
            padding: 0.75rem 1rem;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .request-header .method {
            color: #ffc107;
        }
        .request-header .timestamp {
            font-size: 0.8em;
            color: #aaa;
        }
        .request-body {
            padding: 1rem;
        }
        .request-body h3 {
            margin-top: 0;
            color: #4a90e2;
        }
        pre {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 5px;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #d4d4d4;
            font-family: "Fira Code", "Courier New", monospace;
        }
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>&#128225; HTTP Request Catcher</h1>
        <div class="info-box">
            <p>Send any HTTP request (GET, POST, etc.) to this URL to capture it:</p>
            <code>{{ request_url }}</code>
            <p>The captured requests will appear below, with the newest one at the top.</p>
        </div>

        <h2>Captured Requests ({{ requests_log|length }})</h2>
        
        {% if requests_log %}
            {% for req in requests_log %}
            <div class="request-card">
                <div class="request-header">
                    <span><span class="method">{{ req.method }}</span> {{ req.path }}</span>
                    <span class="timestamp">{{ req.timestamp }}</span>
                </div>
                <div class="request-body">
                    <h3>Source</h3>
                    <pre>IP: {{ req.ip }}\nUser-Agent: {{ req.user_agent }}</pre>

                    <h3>Headers</h3>
                    <pre>{{ req.headers }}</pre>

                    <h3>Body / Query Params</h3>
                    <pre>{{ req.body or 'No body or query parameters received.' }}</pre>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="request-card empty-state">
                <p>No requests captured yet. Send a request to the URL above to get started.</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all(path):
    """
    This single route captures all incoming requests, logs their details,
    and then displays the list of all captured requests.
    """
    # 1. Capture request details
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get the request body
    body = ""
    if request.method == 'POST' or request.method == 'PUT' or request.method == 'PATCH':
        # Try to get JSON, then form data, then raw data
        if request.is_json:
            body = request.get_json(silent=True)
            if body is None:
                body = request.get_data(as_text=True) # Fallback for malformed JSON
        else:
            # Check for form data first
            form_data = request.form.to_dict()
            if form_data:
                body = form_data
            else:
                # Fallback to raw data
                body = request.get_data(as_text=True)
    elif request.method == 'GET':
        # For GET requests, the "body" is the query parameters
        body = request.args.to_dict()

    # Format headers for nice printing
    headers_str = "\n".join(f"{key}: {value}" for key, value in request.headers.items())

    # Create a dictionary for the current request
    current_request_data = {
        'timestamp': now,
        'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
        'user_agent': request.headers.get('User-Agent', 'N/A'),
        'method': request.method,
        'path': f"/{path}",
        'headers': headers_str,
        'body': body
    }

    # 2. Log the request by adding it to the top of our list
    requests_log.insert(0, current_request_data)

    # To prevent the log from growing indefinitely in memory, cap it at 50 requests.
    if len(requests_log) > 50:
        requests_log.pop()

    # 3. Render the page, showing all captured requests
    return render_template_string(
        HTML_TEMPLATE, 
        requests_log=requests_log,
        request_url=request.host_url
    )

if __name__ == '__main__':
    # To run this app:
    # 1. Save the code as a Python file (e.g., app.py).
    # 2. Make sure you have Flask installed (`pip install Flask`).
    # 3. Run from your terminal: `python app.py`
    # 4. Open your browser to http://127.0.0.1:5000
    app.run(debug=True, port=5000)
