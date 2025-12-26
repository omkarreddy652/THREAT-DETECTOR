import os
import json
import requests
from urllib.parse import urlencode
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from database.database import Database

class OAuthHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, auth_manager=None, **kwargs):
        self.auth_manager = auth_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path.startswith('/oauth/callback'):
            # Extract authorization code from URL
            from urllib.parse import parse_qs, urlparse
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            if 'code' in params:
                code = params['code'][0]
                self.auth_manager.oauth_code = code
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                response = """
                <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h2 style="color: #4CAF50;">Authentication Successful!</h2>
                    <p>You can close this window and return to the application.</p>
                    <script>setTimeout(function(){ window.close(); }, 2000);</script>
                </body>
                </html>
                """
                self.wfile.write(response.encode())
            else:
                # Send error response
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                response = """
                <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h2 style="color: #f44336;">Authentication Failed!</h2>
                    <p>Please try again.</p>
                    <script>setTimeout(function(){ window.close(); }, 2000);</script>
                </body>
                </html>
                """
                self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

class AuthManager:
    def __init__(self):
        self.db = Database()
        self.oauth_code = None
        self.config = self.load_config()
    
    def load_config(self):
        """Load OAuth configuration"""
        config_path = "auth/oauth_config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration (you'll need to add your own OAuth credentials)
            return {
                "google": {
                    "client_id": "YOUR_GOOGLE_CLIENT_ID",
                    "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
                    "redirect_uri": "http://localhost:8080/oauth/callback",
                    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo"
                },
                "github": {
                    "client_id": "YOUR_GITHUB_CLIENT_ID",
                    "client_secret": "YOUR_GITHUB_CLIENT_SECRET",
                    "redirect_uri": "http://localhost:8080/oauth/callback",
                    "auth_url": "https://github.com/login/oauth/authorize",
                    "token_url": "https://github.com/login/oauth/access_token",
                    "userinfo_url": "https://api.github.com/user"
                }
            }
    
    def register_user(self, username, email, password):
        """Register a new user"""
        return self.db.register_user(username, email, password)
    
    def login_user(self, username_or_email, password):
        """Login user with username/email and password"""
        success, result = self.db.authenticate_user(username_or_email, password)
        if success:
            session_token = self.db.create_session(result['user_id'])
            return True, {'user': result, 'session_token': session_token}
        return False, result
    
    def google_login(self):
        """Initiate Google OAuth login"""
        try:
            google_config = self.config['google']
            
            # Build authorization URL
            params = {
                'client_id': google_config['client_id'],
                'redirect_uri': google_config['redirect_uri'],
                'response_type': 'code',
                'scope': 'openid email profile',
                'access_type': 'offline'
            }
            
            auth_url = f"{google_config['auth_url']}?{urlencode(params)}"
            
            # Start local server to handle callback
            self.start_oauth_server()
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Wait for authorization code
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while not self.oauth_code and (time.time() - start_time) < timeout:
                time.sleep(1)
            
            if self.oauth_code:
                return self.handle_google_callback(self.oauth_code)
            else:
                return False, "Authentication timeout"
                
        except Exception as e:
            return False, f"Google login failed: {str(e)}"
    
    def github_login(self):
        """Initiate GitHub OAuth login"""
        try:
            github_config = self.config['github']
            
            # Build authorization URL
            params = {
                'client_id': github_config['client_id'],
                'redirect_uri': github_config['redirect_uri'],
                'scope': 'read:user user:email'
            }
            
            auth_url = f"{github_config['auth_url']}?{urlencode(params)}"
            
            # Start local server to handle callback
            self.start_oauth_server()
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Wait for authorization code
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while not self.oauth_code and (time.time() - start_time) < timeout:
                time.sleep(1)
            
            if self.oauth_code:
                return self.handle_github_callback(self.oauth_code)
            else:
                return False, "Authentication timeout"
                
        except Exception as e:
            return False, f"GitHub login failed: {str(e)}"
    
    def google_signup(self):
        """Initiate Google OAuth signup (works for both new and existing users)"""
        try:
            google_config = self.config['google']
            
            # Build authorization URL
            params = {
                'client_id': google_config['client_id'],
                'redirect_uri': google_config['redirect_uri'],
                'response_type': 'code',
                'scope': 'openid email profile',
                'access_type': 'offline'
            }
            
            auth_url = f"{google_config['auth_url']}?{urlencode(params)}"
            
            # Start local server to handle callback
            self.start_oauth_server()
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Wait for authorization code
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while not self.oauth_code and (time.time() - start_time) < timeout:
                time.sleep(1)
            
            if self.oauth_code:
                return self.handle_google_callback(self.oauth_code)
            else:
                return False, "Authentication timeout"
                
        except Exception as e:
            return False, f"Google signup failed: {str(e)}"
    
    def github_signup(self):
        """Initiate GitHub OAuth signup (works for both new and existing users)"""
        try:
            github_config = self.config['github']
            
            # Build authorization URL
            params = {
                'client_id': github_config['client_id'],
                'redirect_uri': github_config['redirect_uri'],
                'scope': 'read:user user:email'
            }
            
            auth_url = f"{github_config['auth_url']}?{urlencode(params)}"
            
            # Start local server to handle callback
            self.start_oauth_server()
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Wait for authorization code
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while not self.oauth_code and (time.time() - start_time) < timeout:
                time.sleep(1)
            
            if self.oauth_code:
                return self.handle_github_callback(self.oauth_code)
            else:
                return False, "Authentication timeout"
                
        except Exception as e:
            return False, f"GitHub signup failed: {str(e)}"
    
    def start_oauth_server(self):
        """Start local server to handle OAuth callback"""
        def run_server():
            server = HTTPServer(('localhost', 8080), 
                              lambda *args, **kwargs: OAuthHandler(*args, auth_manager=self, **kwargs))
            server.handle_request()
        
        thread = threading.Thread(target=run_server)
        thread.daemon = True
        thread.start()
    
    def handle_google_callback(self, code):
        """Handle Google OAuth callback"""
        try:
            google_config = self.config['google']
            
            # Exchange code for access token
            token_data = {
                'client_id': google_config['client_id'],
                'client_secret': google_config['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': google_config['redirect_uri']
            }
            
            response = requests.post(google_config['token_url'], data=token_data)
            token_info = response.json()
            
            if 'access_token' not in token_info:
                return False, "Failed to get access token"
            
            # Get user info
            headers = {'Authorization': f"Bearer {token_info['access_token']}"}
            user_response = requests.get(google_config['userinfo_url'], headers=headers)
            user_info = user_response.json()
            
            # Check if user exists, if not create account
            conn = self.db.db_path
            import sqlite3
            db_conn = sqlite3.connect(conn)
            cursor = db_conn.cursor()
            
            cursor.execute("SELECT id, username, email FROM users WHERE google_id = ? OR email = ?", 
                         (user_info['id'], user_info['email']))
            user = cursor.fetchone()
            
            if user:
                # User exists, update google_id if needed
                user_id, username, email = user
                cursor.execute("UPDATE users SET google_id = ? WHERE id = ?", (user_info['id'], user_id))
                db_conn.commit()
            else:
                # Create new user
                username = user_info.get('name', user_info['email'].split('@')[0])
                email = user_info['email']
                
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, salt, google_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, email, '', '', user_info['id']))
                
                user_id = cursor.lastrowid
                db_conn.commit()
            
            db_conn.close()
            
            # Create session
            session_token = self.db.create_session(user_id)
            
            return True, {
                'user': {
                    'user_id': user_id,
                    'username': username,
                    'email': email
                },
                'session_token': session_token
            }
            
        except Exception as e:
            return False, f"Google callback failed: {str(e)}"
    
    def handle_github_callback(self, code):
        """Handle GitHub OAuth callback"""
        try:
            github_config = self.config['github']
            
            # Exchange code for access token
            token_data = {
                'client_id': github_config['client_id'],
                'client_secret': github_config['client_secret'],
                'code': code
            }
            
            headers = {'Accept': 'application/json'}
            response = requests.post(github_config['token_url'], data=token_data, headers=headers)
            token_info = response.json()
            
            if 'access_token' not in token_info:
                return False, "Failed to get access token"
            
            # Get user info
            headers = {
                'Authorization': f"token {token_info['access_token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            user_response = requests.get(github_config['userinfo_url'], headers=headers)
            user_info = user_response.json()
            
            # Check if user exists, if not create account
            conn = self.db.db_path
            import sqlite3
            db_conn = sqlite3.connect(conn)
            cursor = db_conn.cursor()
            
            cursor.execute("SELECT id, username, email FROM users WHERE github_id = ? OR username = ?", 
                         (user_info['id'], user_info['login']))
            user = cursor.fetchone()
            
            if user:
                # User exists, update github_id if needed
                user_id, username, email = user
                cursor.execute("UPDATE users SET github_id = ? WHERE id = ?", (user_info['id'], user_id))
                db_conn.commit()
            else:
                # Create new user
                username = user_info['login']
                email = user_info.get('email', f"{username}@github.com")
                
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, salt, github_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, email, '', '', user_info['id']))
                
                user_id = cursor.lastrowid
                db_conn.commit()
            
            db_conn.close()
            
            # Create session
            session_token = self.db.create_session(user_id)
            
            return True, {
                'user': {
                    'user_id': user_id,
                    'username': username,
                    'email': email
                },
                'session_token': session_token
            }
            
        except Exception as e:
            return False, f"GitHub callback failed: {str(e)}"
    
    def validate_session(self, session_token):
        """Validate session token"""
        return self.db.validate_session(session_token)
    
    def logout_user(self, session_token):
        """Logout user"""
        return self.db.logout_user(session_token)
    
    def microsoft_signup(self):
        """Initiate Microsoft OAuth signup (works for both new and existing users)"""
        try:
            ms_config = self.config['microsoft']
            params = {
                'client_id': ms_config['client_id'],
                'response_type': 'code',
                'redirect_uri': ms_config['redirect_uri'],
                'response_mode': 'query',
                'scope': 'User.Read email openid profile',
            }
            auth_url = f"{ms_config['auth_url']}?{urlencode(params)}"
            self.start_oauth_server()
            webbrowser.open(auth_url)
            timeout = 60
            start_time = time.time()
            while not self.oauth_code and (time.time() - start_time) < timeout:
                time.sleep(1)
            if self.oauth_code:
                return self.handle_microsoft_callback(self.oauth_code)
            else:
                return False, "Authentication timeout"
        except Exception as e:
            return False, f"Microsoft signup failed: {str(e)}"

    def handle_microsoft_callback(self, code):
        try:
            ms_config = self.config['microsoft']
            token_data = {
                'client_id': ms_config['client_id'],
                'client_secret': ms_config['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': ms_config['redirect_uri'],
            }
            response = requests.post(ms_config['token_url'], data=token_data)
            token_info = response.json()
            if 'access_token' not in token_info:
                return False, "Failed to get access token"
            headers = {'Authorization': f"Bearer {token_info['access_token']}"}
            user_response = requests.get(ms_config['userinfo_url'], headers=headers)
            user_info = user_response.json()
            # User DB logic (similar to Google/GitHub)
            # ...
            return False, "Microsoft OAuth not fully implemented yet"
        except Exception as e:
            return False, f"Microsoft callback failed: {str(e)}"

    def facebook_signup(self):
        """Initiate Facebook OAuth signup (works for both new and existing users)"""
        try:
            fb_config = self.config['facebook']
            params = {
                'client_id': fb_config['client_id'],
                'redirect_uri': fb_config['redirect_uri'],
                'scope': 'email public_profile',
                'response_type': 'code',
            }
            auth_url = f"{fb_config['auth_url']}?{urlencode(params)}"
            self.start_oauth_server()
            webbrowser.open(auth_url)
            timeout = 60
            start_time = time.time()
            while not self.oauth_code and (time.time() - start_time) < timeout:
                time.sleep(1)
            if self.oauth_code:
                return self.handle_facebook_callback(self.oauth_code)
            else:
                return False, "Authentication timeout"
        except Exception as e:
            return False, f"Facebook signup failed: {str(e)}"

    def handle_facebook_callback(self, code):
        try:
            fb_config = self.config['facebook']
            token_data = {
                'client_id': fb_config['client_id'],
                'client_secret': fb_config['client_secret'],
                'redirect_uri': fb_config['redirect_uri'],
                'code': code,
            }
            response = requests.get(fb_config['token_url'], params=token_data)
            token_info = response.json() if hasattr(response, 'json') else {}
            if 'access_token' not in token_info:
                return False, "Failed to get access token"
            user_response = requests.get(fb_config['userinfo_url'], params={'access_token': token_info['access_token']})
            user_info = user_response.json()
            # User DB logic (similar to Google/GitHub)
            # ...
            return False, "Facebook OAuth not fully implemented yet"
        except Exception as e:
            return False, f"Facebook callback failed: {str(e)}" 