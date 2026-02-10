import requests
import sys
import json
from datetime import datetime

class AthenaVisionAPITester:
    def __init__(self, base_url="https://bookbridge-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                if response.text:
                    try:
                        error_data = response.json()
                        details += f" - {error_data.get('detail', response.text[:100])}"
                    except:
                        details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {"status": "success"}
            return None

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return None

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "name": f"Test User {timestamp}"
        }
        
        response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        if not self.user_data:
            return False
            
        login_data = {
            "email": self.user_data['email'],
            "password": "TestPass123!"
        }
        
        response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        return response and 'access_token' in response

    def test_get_current_user(self):
        """Test getting current user info"""
        response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        
        return response and 'email' in response

    def test_isbn_validation_valid(self):
        """Test ISBN search with valid ISBN"""
        # Pride and Prejudice ISBN
        isbn = "9780141439518"
        
        response = self.run_test(
            "ISBN Search - Valid",
            "GET",
            f"books/search/{isbn}",
            200
        )
        
        return response and 'title' in response and 'authors' in response

    def test_isbn_validation_invalid(self):
        """Test ISBN search with invalid ISBN"""
        invalid_isbn = "1234567890"
        
        response = self.run_test(
            "ISBN Search - Invalid",
            "GET",
            f"books/search/{invalid_isbn}",
            400
        )
        
        return response is None  # Should fail with 400

    def test_book_content_fetch(self):
        """Test fetching book content"""
        isbn = "9780141439518"
        
        response = self.run_test(
            "Book Content Fetch",
            "GET",
            f"books/content/{isbn}",
            200
        )
        
        return response and 'content' in response

    def test_progress_save_and_retrieve(self):
        """Test saving and retrieving reading progress"""
        isbn = "9780141439518"
        progress_data = {
            "isbn": isbn,
            "position": 25.5
        }
        
        # Save progress
        save_response = self.run_test(
            "Save Reading Progress",
            "POST",
            "progress",
            200,
            data=progress_data
        )
        
        if not save_response:
            return False
        
        # Retrieve progress
        get_response = self.run_test(
            "Get Reading Progress",
            "GET",
            f"progress/{isbn}",
            200
        )
        
        return get_response and get_response.get('position') == 25.5

    def test_bookmark_operations(self):
        """Test bookmark creation, retrieval, and deletion"""
        isbn = "9780141439518"
        bookmark_data = {
            "isbn": isbn,
            "position": 15.0,
            "text": "It is a truth universally acknowledged..."
        }
        
        # Create bookmark
        create_response = self.run_test(
            "Create Bookmark",
            "POST",
            "bookmarks",
            200,
            data=bookmark_data
        )
        
        if not create_response:
            return False
        
        # Get bookmarks
        get_response = self.run_test(
            "Get Bookmarks",
            "GET",
            f"bookmarks/{isbn}",
            200
        )
        
        if not get_response or len(get_response) == 0:
            return False
        
        # Delete bookmark
        delete_response = self.run_test(
            "Delete Bookmark",
            "DELETE",
            f"bookmarks/{isbn}/{bookmark_data['position']}",
            200
        )
        
        return delete_response is not None

    def test_highlight_operations(self):
        """Test highlight creation and retrieval"""
        isbn = "9780141439518"
        highlight_data = {
            "isbn": isbn,
            "text": "universally acknowledged",
            "color": "yellow"
        }
        
        # Create highlight
        create_response = self.run_test(
            "Create Highlight",
            "POST",
            "highlights",
            200,
            data=highlight_data
        )
        
        if not create_response:
            return False
        
        # Get highlights
        get_response = self.run_test(
            "Get Highlights",
            "GET",
            f"highlights/{isbn}",
            200
        )
        
        return get_response and len(get_response) > 0

    def test_user_library(self):
        """Test user library retrieval"""
        response = self.run_test(
            "Get User Library",
            "GET",
            "library",
            200
        )
        
        return response is not None

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting AthenaVision API Tests")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 50)
        
        # Authentication tests
        if not self.test_user_registration():
            print("❌ Registration failed - stopping tests")
            return False
        
        if not self.test_user_login():
            print("❌ Login failed - stopping tests")
            return False
        
        self.test_get_current_user()
        
        # Book search tests
        self.test_isbn_validation_valid()
        self.test_isbn_validation_invalid()
        
        # Book content tests
        self.test_book_content_fetch()
        
        # Progress tracking tests
        self.test_progress_save_and_retrieve()
        
        # Bookmark tests
        self.test_bookmark_operations()
        
        # Highlight tests
        self.test_highlight_operations()
        
        # Library tests
        self.test_user_library()
        
        # Print summary
        print("=" * 50)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = AthenaVisionAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "summary": {
                "total_tests": tester.tests_run,
                "passed_tests": tester.tests_passed,
                "success_rate": (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())