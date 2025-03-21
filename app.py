from flask import Flask, render_template, request, redirect, url_for, flash
import facebook
import logging
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

# Set up logging
logging.basicConfig(level=logging.INFO)

class FacebookAgent:
    def __init__(self, access_token):
        self.graph = facebook.GraphAPI(access_token)
        self.keyword_list = set()

    # Add all methods from the original FacebookAgent class here
    # (get_profile_info, get_recent_posts, create_post, etc.)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        access_token = request.form.get('access_token')
        if access_token:
            agent = FacebookAgent(access_token)
            profile = agent.get_profile_info()
            if profile:
                flash(f"Connected as: {profile['name']}", 'success')
            else:
                flash("Failed to connect!", 'error')
        else:
            flash("Please enter an access token!", 'error')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)