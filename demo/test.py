import requests

def test_profile_api():
    # First, login to get the token
    login_url = 'http://127.0.0.1:8000/user/login/'
    login_data = {
        'phone_number': 'your_phone_number',  # Replace with actual phone number
        'password': 'your_password'           # Replace with actual password
    }

    # Make login request
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code == 200:
        # Extract token from login response
        token = login_response.json().get('token')
        
        # Set up headers with the token
        headers = {
            'Authorization': f'Token {token}'
        }
        
        # Make request to profile endpoint
        profile_url = 'http://127.0.0.1:8000/api/user/profile/'
        profile_response = requests.get(profile_url, headers=headers)
        
        if profile_response.status_code == 200:
            print("Profile Data:", profile_response.json())
        else:
            print("Error getting profile:", profile_response.json())
    else:
        print("Login failed:", login_response.json())

if __name__ == "__main__":
    test_profile_api()
