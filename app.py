from flask import Flask, render_template, request, flash
import facebook
import logging
import os
import tkinter as tk
from tkinter import messagebox

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class FacebookAgent:
    def __init__(self, access_token):
        self.graph = facebook.GraphAPI(access_token)
        self.keyword_list = set()
        self.access_token = access_token

    def get_profile_info(self):
        try:
            profile = self.graph.get_object("me", fields="name,id")
            logging.info(f"Fetched profile info for: {profile['name']}")
            return profile
        except Exception as e:
            logging.error(f"Error fetching profile: {e}")
            messagebox.showerror("Error", f"Failed to fetch profile: {e}")
            return None

    def get_recent_posts(self, limit=10):
        try:
            posts = self.graph.get_connections("me", "posts", limit=limit, fields="message,created_time,id")
            logging.info(f"Fetched {len(posts['data'])} recent posts")
            return posts['data']
        except Exception as e:
            logging.error(f"Error fetching posts: {e}")
            messagebox.showerror("Error", f"Failed to fetch posts: {e}")
            return []

    def create_post(self, message):
        try:
            self.graph.put_object("me", "feed", message=message)
            logging.info(f"Created post: {message}")
            return True
        except Exception as e:
            logging.error(f"Error creating post: {e}")
            messagebox.showerror("Error", f"Failed to create post: {e}")
            return False

    def analyze_engagement(self, post_id):
        try:
            reactions = self.graph.get_connections(post_id, "reactions", summary=True)
            comments = self.graph.get_connections(post_id, "comments", summary=True)
            logging.info(f"Analyzed engagement for post {post_id}")
            return {
                "reactions_count": reactions['summary']['total_count'],
                "comments_count": comments['summary']['total_count']
            }
        except Exception as e:
            logging.error(f"Error analyzing engagement: {e}")
            messagebox.showerror("Error", f"Failed to analyze engagement: {e}")
            return None

    def delete_post(self, post_id):
        try:
            self.graph.delete_object(post_id)
            logging.info(f"Deleted post: {post_id}")
            return True
        except Exception as e:
            logging.error(f"Error deleting post: {e}")
            messagebox.showerror("Error", f"Failed to delete post: {e}")
            return False

    def add_keyword(self, keyword):
        self.keyword_list.add(keyword.lower())
        logging.info(f"Added keyword: {keyword}")

    def remove_keyword(self, keyword):
        self.keyword_list.discard(keyword.lower())
        logging.info(f"Removed keyword: {keyword}")

    def scan_and_delete_posts(self):
        deleted_count = 0
        posts = self.get_recent_posts(limit=50)
        
        for post in posts:
            if 'message' in post:
                message = post['message'].lower()
                if any(keyword in message for keyword in self.keyword_list):
                    if self.delete_post(post['id']):
                        deleted_count += 1
                        
        logging.info(f"Deleted {deleted_count} posts based on keywords")
        return deleted_count

    def exchange_for_long_lived_token(self, app_id, app_secret):
        try:
            response = self.graph.extend_access_token(app_id, app_secret)
            self.access_token = response['access_token']
            logging.info("Exchanged for long-lived access token")
            return True
        except Exception as e:
            logging.error(f"Error exchanging token: {e}")
            messagebox.showerror("Error", f"Failed to exchange token: {e}")
            return False


class FacebookAgentGUI:
    def __init__(self):
        self.agent = None
        self.root = tk.Tk()
        self.root.title("Facebook Profile Manager")
        self.root.geometry("600x400")
        
        # Token Entry
        tk.Label(self.root, text="Access Token:").pack(pady=5)
        self.token_entry = tk.Entry(self.root, width=50)
        self.token_entry.pack(pady=5)
        
        # App ID and Secret (for long-lived token)
        tk.Label(self.root, text="App ID:").pack(pady=5)
        self.app_id_entry = tk.Entry(self.root, width=50)
        self.app_id_entry.pack(pady=5)
        
        tk.Label(self.root, text="App Secret:").pack(pady=5)
        self.app_secret_entry = tk.Entry(self.root, width=50)
        self.app_secret_entry.pack(pady=5)
        
        # Connect Button
        tk.Button(self.root, text="Connect", command=self.connect).pack(pady=5)
        
        # Keyword Management
        tk.Label(self.root, text="Keyword Management").pack(pady=5)
        self.keyword_entry = tk.Entry(self.root, width=30)
        self.keyword_entry.pack(pady=5)
        
        # Keyword Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Add Keyword", command=self.add_keyword).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove Keyword", command=self.remove_keyword).pack(side=tk.LEFT, padx=5)
        
        # Keyword List
        tk.Label(self.root, text="Current Keywords:").pack(pady=5)
        self.keyword_listbox = tk.Listbox(self.root, width=40, height=5)
        self.keyword_listbox.pack(pady=5)
        
        # Scan and Delete Button
        tk.Button(self.root, text="Scan and Delete Posts", command=self.scan_and_delete).pack(pady=10)
        
        # Status Label
        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack(pady=5)

    def connect(self):
        token = self.token_entry.get()
        app_id = self.app_id_entry.get()
        app_secret = self.app_secret_entry.get()
        
        if token and app_id and app_secret:
            self.agent = FacebookAgent(token)
            if self.agent.exchange_for_long_lived_token(app_id, app_secret):
                profile = self.agent.get_profile_info()
                if profile:
                    self.status_label.config(text=f"Connected as: {profile['name']}")
                else:
                    self.status_label.config(text="Connection failed!")
            else:
                self.status_label.config(text="Token exchange failed!")
        else:
            messagebox.showerror("Error", "Please enter access token, app ID, and app secret")

    def add_keyword(self):
        keyword = self.keyword_entry.get()
        if keyword and self.agent:
            self.agent.add_keyword(keyword)
            self.update_keyword_list()
            self.keyword_entry.delete(0, tk.END)

    def remove_keyword(self):
        selection = self.keyword_listbox.curselection()
        if selection and self.agent:
            keyword = self.keyword_listbox.get(selection[0])
            self.agent.remove_keyword(keyword)
            self.update_keyword_list()

    def update_keyword_list(self):
        self.keyword_listbox.delete(0, tk.END)
        for keyword in sorted(self.agent.keyword_list):
            self.keyword_listbox.insert(tk.END, keyword)

    def scan_and_delete(self):
        if self.agent:
            deleted_count = self.agent.scan_and_delete_posts()
            self.status_label.config(text=f"Deleted {deleted_count} posts")
        else:
            messagebox.showerror("Error", "Please connect first")

    def run(self):
        self.root.mainloop()


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
