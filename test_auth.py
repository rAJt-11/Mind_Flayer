import httpx
import uuid

def test_auth_flow():
    base_url = "http://127.0.0.1:8000"
    
    # Generate unique test data
    unique_id = str(uuid.uuid4())[:8]
    test_username = f"testuser_{unique_id}"
    test_password = "Password123!"
    test_name = "Test User"
    
    print(f"--- Testing Signup for {test_username} ---")
    
    # Signup Data
    signup_data = {
        "name": test_name,
        "username": test_username,
        "email": f"{test_username}@example.com",
        "password": test_password,
        "confirm_password": test_password
    }
    
    with httpx.Client(follow_redirects=False) as client:
        response = client.post(f"{base_url}/signup", data=signup_data)
        
        print(f"Signup Response Status: {response.status_code}")
        if response.status_code == 302:
            print(f"Signup Redirect Location: {response.headers.get('Location')}")
            # Get the session cookie
            cookies = client.cookies
            print(f"Signup Cookies Set: {bool(cookies.get('mf_session'))}")
        else:
            print(f"Signup Failed: {response.text}")
            return
            
    print(f"\n--- Testing Login for {test_username} ---")
    
    login_data = {
        "username": test_username,
        "password": test_password
    }
    
    # Start a new client session to simulate a clean login attempt
    with httpx.Client(follow_redirects=False) as client:
        response = client.post(f"{base_url}/login", data=login_data)
        
        print(f"Login Response Status: {response.status_code}")
        if response.status_code == 302:
            print(f"Login Redirect Location: {response.headers.get('Location')}")
            # Get the session cookie
            cookies = client.cookies
            print(f"Login Cookies Set: {bool(cookies.get('mf_session'))}")
        else:
            print(f"Login Failed: {response.text}")
            return

    print("\nAuth flow completed successfully!")

if __name__ == "__main__":
    test_auth_flow()
