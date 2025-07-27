#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for NovaZone Educational Platform
Tests all authentication, dashboard, course, teacher, progress, quiz, community, and file endpoints
"""

import requests
import json
import base64
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://995d213b-3c3a-4487-a43f-18261ca54f2c.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class NovaZoneAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.student_token = None
        self.teacher_token = None
        self.student_id = None
        self.teacher_id = None
        self.course_id = None
        self.progress_id = None
        self.quiz_id = None
        self.post_id = None
        self.file_id = None
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, files: Dict = None, auth_token: str = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                if files:
                    # Remove content-type for file uploads
                    headers.pop("Content-Type", None)
                    response = requests.post(url, headers=headers, files=files)
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return False, {"error": "Unsupported method"}, 400
                
            return response.status_code < 400, response.json() if response.content else {}, response.status_code
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}, 0
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}, response.status_code if 'response' in locals() else 0

    def test_seed_data(self):
        """Seed database with sample data"""
        print("🌱 Seeding database with sample data...")
        success, data, status = self.make_request("POST", "/seed-data")
        self.log_test("Database Seeding", success, f"Status: {status}")
        return success

    def test_auth_register_student(self):
        """Test student registration"""
        student_data = {
            "email": "emma.watson@student.com",
            "password": "SecurePass123!",
            "full_name": "Emma Watson",
            "role": "student"
        }
        
        success, data, status = self.make_request("POST", "/auth/register", student_data)
        
        if success and "access_token" in data:
            self.student_token = data["access_token"]
            self.student_id = data["user"]["id"]
            self.log_test("Student Registration", True, f"Token received, User ID: {self.student_id}")
        else:
            self.log_test("Student Registration", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_auth_register_teacher(self):
        """Test teacher registration"""
        teacher_data = {
            "email": "john.smith@teacher.com",
            "password": "TeacherPass456!",
            "full_name": "John Smith",
            "role": "teacher"
        }
        
        success, data, status = self.make_request("POST", "/auth/register", teacher_data)
        
        if success and "access_token" in data:
            self.teacher_token = data["access_token"]
            self.teacher_id = data["user"]["id"]
            self.log_test("Teacher Registration", True, f"Token received, User ID: {self.teacher_id}")
        else:
            self.log_test("Teacher Registration", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_auth_login(self):
        """Test login with valid credentials"""
        login_data = {
            "email": "emma.watson@student.com",
            "password": "SecurePass123!"
        }
        
        success, data, status = self.make_request("POST", "/auth/login", login_data)
        
        if success and "access_token" in data:
            self.log_test("Student Login", True, f"Login successful")
        else:
            self.log_test("Student Login", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_auth_login_invalid(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "emma.watson@student.com",
            "password": "WrongPassword"
        }
        
        success, data, status = self.make_request("POST", "/auth/login", login_data)
        
        # Should fail with 401
        if not success and status == 401:
            self.log_test("Invalid Login (Expected Failure)", True, "Correctly rejected invalid credentials")
        else:
            self.log_test("Invalid Login (Expected Failure)", False, f"Should have failed with 401, got {status}")
            
        return not success and status == 401

    def test_auth_me(self):
        """Test protected route with valid token"""
        if not self.student_token:
            self.log_test("Get Current User", False, "No student token available")
            return False
            
        success, data, status = self.make_request("GET", "/auth/me", auth_token=self.student_token)
        
        if success and "id" in data:
            self.log_test("Get Current User", True, f"User data retrieved: {data['full_name']}")
        else:
            self.log_test("Get Current User", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_dashboard_student(self):
        """Test student dashboard data"""
        if not self.student_id:
            self.log_test("Student Dashboard", False, "No student ID available")
            return False
            
        success, data, status = self.make_request("GET", f"/dashboard/student/{self.student_id}")
        
        if success and "learning_path" in data:
            self.log_test("Student Dashboard", True, f"Dashboard data includes learning path, courses, progress")
        else:
            self.log_test("Student Dashboard", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_dashboard_teacher(self):
        """Test teacher dashboard data"""
        if not self.teacher_id:
            self.log_test("Teacher Dashboard", False, "No teacher ID available")
            return False
            
        success, data, status = self.make_request("GET", f"/dashboard/teacher/{self.teacher_id}")
        
        if success and "analytics" in data:
            self.log_test("Teacher Dashboard", True, f"Dashboard includes analytics and courses")
        else:
            self.log_test("Teacher Dashboard", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_courses_list(self):
        """Test course listing"""
        success, data, status = self.make_request("GET", "/courses")
        
        if success and isinstance(data, list):
            self.log_test("Course Listing", True, f"Retrieved {len(data)} courses")
        else:
            self.log_test("Course Listing", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_courses_filter(self):
        """Test course listing with filters"""
        success, data, status = self.make_request("GET", "/courses?subject=Programming&difficulty=beginner")
        
        if success and isinstance(data, list):
            self.log_test("Course Filtering", True, f"Filtered courses retrieved")
        else:
            self.log_test("Course Filtering", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_course_create(self):
        """Test course creation (teacher only)"""
        if not self.teacher_token:
            self.log_test("Course Creation", False, "No teacher token available")
            return False
            
        course_data = {
            "title": "Advanced JavaScript Concepts",
            "description": "Deep dive into modern JavaScript features and patterns",
            "subject": "Programming",
            "difficulty_level": "advanced",
            "duration_hours": 35,
            "total_lessons": 15
        }
        
        success, data, status = self.make_request("POST", "/courses", course_data, auth_token=self.teacher_token)
        
        if success and "id" in data:
            self.course_id = data["id"]
            self.log_test("Course Creation", True, f"Course created with ID: {self.course_id}")
        else:
            self.log_test("Course Creation", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_course_enroll(self):
        """Test course enrollment"""
        if not self.student_token or not self.course_id:
            self.log_test("Course Enrollment", False, "Missing student token or course ID")
            return False
            
        success, data, status = self.make_request("POST", f"/courses/{self.course_id}/enroll", auth_token=self.student_token)
        
        if success and "message" in data:
            self.log_test("Course Enrollment", True, "Successfully enrolled in course")
        else:
            self.log_test("Course Enrollment", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_teachers_list(self):
        """Test teacher listing"""
        success, data, status = self.make_request("GET", "/teachers")
        
        if success and isinstance(data, list):
            self.log_test("Teacher Listing", True, f"Retrieved {len(data)} teachers")
        else:
            self.log_test("Teacher Listing", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_teachers_filter(self):
        """Test teacher listing with subject filtering"""
        success, data, status = self.make_request("GET", "/teachers?subject=Programming")
        
        if success and isinstance(data, list):
            self.log_test("Teacher Subject Filtering", True, f"Filtered teachers retrieved")
        else:
            self.log_test("Teacher Subject Filtering", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_teacher_recommendations(self):
        """Test AI teacher recommendations"""
        if not self.student_token:
            self.log_test("Teacher Recommendations", False, "No student token available")
            return False
            
        success, data, status = self.make_request("GET", "/teachers/recommendations/Programming", auth_token=self.student_token)
        
        if success and "recommendations" in data:
            self.log_test("Teacher Recommendations", True, f"AI recommendations retrieved")
        else:
            self.log_test("Teacher Recommendations", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_teacher_profile_update(self):
        """Test teacher profile updates"""
        if not self.teacher_token:
            self.log_test("Teacher Profile Update", False, "No teacher token available")
            return False
            
        profile_data = {
            "subjects": ["Programming", "Web Development", "JavaScript"],
            "experience_years": 8,
            "bio": "Experienced full-stack developer and educator",
            "hourly_rate": 65.0
        }
        
        success, data, status = self.make_request("PUT", "/teachers/profile", profile_data, auth_token=self.teacher_token)
        
        if success and "message" in data:
            self.log_test("Teacher Profile Update", True, "Profile updated successfully")
        else:
            self.log_test("Teacher Profile Update", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_progress_get(self):
        """Test student progress data"""
        if not self.student_id:
            self.log_test("Get Student Progress", False, "No student ID available")
            return False
            
        success, data, status = self.make_request("GET", f"/progress/{self.student_id}")
        
        if success and "stats" in data:
            self.log_test("Get Student Progress", True, f"Progress data with AI analysis retrieved")
        else:
            self.log_test("Get Student Progress", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_progress_update(self):
        """Test progress updates"""
        # First, get progress to find a progress_id
        if not self.student_id:
            self.log_test("Update Progress", False, "No student ID available")
            return False
            
        # Get progress first
        success, data, status = self.make_request("GET", f"/progress/{self.student_id}")
        if success and data.get("courses") and len(data["courses"]) > 0:
            self.progress_id = data["courses"][0]["id"]
        else:
            self.log_test("Update Progress", False, "No progress records found to update")
            return False
            
        # Update progress
        success, data, status = self.make_request("PUT", f"/progress/{self.progress_id}?completion_percentage=75.5&time_spent_hours=12.5")
        
        if success and "message" in data:
            self.log_test("Update Progress", True, "Progress updated successfully")
        else:
            self.log_test("Update Progress", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_quiz_get(self):
        """Test quiz retrieval/generation"""
        if not self.course_id:
            # Use a sample course ID from seeded data
            self.course_id = "course_1"
            
        success, data, status = self.make_request("GET", f"/quiz/{self.course_id}")
        
        if success and "questions" in data:
            self.quiz_id = data["id"]
            self.log_test("Quiz Retrieval", True, f"Quiz with {len(data['questions'])} questions retrieved")
        else:
            self.log_test("Quiz Retrieval", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_quiz_submit(self):
        """Test quiz submission and scoring"""
        if not self.quiz_id or not self.student_token:
            self.log_test("Quiz Submission", False, "Missing quiz ID or student token")
            return False
            
        submission_data = {
            "quiz_id": self.quiz_id,
            "student_id": self.student_id,
            "answers": [1, 2]  # Sample answers
        }
        
        success, data, status = self.make_request("POST", "/quiz/submit", submission_data, auth_token=self.student_token)
        
        if success and "score" in data:
            self.log_test("Quiz Submission", True, f"Quiz scored: {data['score']}%")
        else:
            self.log_test("Quiz Submission", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_community_posts_list(self):
        """Test community post listing"""
        success, data, status = self.make_request("GET", "/community/posts")
        
        if success and isinstance(data, list):
            self.log_test("Community Posts Listing", True, f"Retrieved {len(data)} posts")
        else:
            self.log_test("Community Posts Listing", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_community_posts_filter(self):
        """Test community post listing with category filter"""
        success, data, status = self.make_request("GET", "/community/posts?category=question")
        
        if success and isinstance(data, list):
            self.log_test("Community Posts Filtering", True, f"Filtered posts retrieved")
        else:
            self.log_test("Community Posts Filtering", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_community_post_create(self):
        """Test post creation"""
        if not self.student_token:
            self.log_test("Community Post Creation", False, "No student token available")
            return False
            
        post_data = {
            "title": "How to improve coding skills?",
            "content": "I'm looking for advice on how to become a better programmer. Any tips?",
            "category": "question"
        }
        
        success, data, status = self.make_request("POST", "/community/posts", post_data, auth_token=self.student_token)
        
        if success and "id" in data:
            self.post_id = data["id"]
            self.log_test("Community Post Creation", True, f"Post created with ID: {self.post_id}")
        else:
            self.log_test("Community Post Creation", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_file_upload(self):
        """Test file upload"""
        # Create a simple test file
        test_content = "This is a test file for NovaZone platform"
        
        files = {
            'file': ('test_document.txt', test_content, 'text/plain')
        }
        
        success, data, status = self.make_request("POST", "/upload", files=files)
        
        if success and "file_id" in data:
            self.file_id = data["file_id"]
            self.log_test("File Upload", True, f"File uploaded with ID: {self.file_id}")
        else:
            self.log_test("File Upload", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_file_download(self):
        """Test file download"""
        if not self.file_id:
            self.log_test("File Download", False, "No file ID available")
            return False
            
        success, data, status = self.make_request("GET", f"/files/{self.file_id}")
        
        if success and "content" in data:
            self.log_test("File Download", True, f"File downloaded: {data['filename']}")
        else:
            self.log_test("File Download", False, f"Status: {status}, Response: {data}")
            
        return success

    def test_role_based_access(self):
        """Test role-based access control"""
        print("🔐 Testing Role-Based Access Control...")
        
        # Test student trying to create course (should fail)
        if self.student_token:
            course_data = {
                "title": "Unauthorized Course",
                "description": "This should fail",
                "subject": "Test",
                "difficulty_level": "beginner",
                "duration_hours": 10,
                "total_lessons": 5
            }
            
            success, data, status = self.make_request("POST", "/courses", course_data, auth_token=self.student_token)
            
            if not success and status == 403:
                self.log_test("Student Course Creation (Expected Failure)", True, "Correctly blocked student from creating course")
            else:
                self.log_test("Student Course Creation (Expected Failure)", False, f"Should have failed with 403, got {status}")
        
        # Test student trying to update teacher profile (should fail)
        if self.student_token:
            profile_data = {
                "subjects": ["Hacking"],
                "experience_years": 1,
                "bio": "Unauthorized access"
            }
            
            success, data, status = self.make_request("PUT", "/teachers/profile", profile_data, auth_token=self.student_token)
            
            if not success and status == 403:
                self.log_test("Student Teacher Profile Update (Expected Failure)", True, "Correctly blocked student from updating teacher profile")
            else:
                self.log_test("Student Teacher Profile Update (Expected Failure)", False, f"Should have failed with 403, got {status}")

    def test_ai_placeholder_functions(self):
        """Test AI placeholder functions return proper mock data"""
        print("🤖 Testing AI Placeholder Functions...")
        
        # Test learning path (via student dashboard)
        if self.student_id:
            success, data, status = self.make_request("GET", f"/dashboard/student/{self.student_id}")
            if success and "learning_path" in data and "ai_insights" in data:
                learning_path = data["learning_path"]
                ai_insights = data["ai_insights"]
                
                # Check learning path structure
                if ("current_level" in learning_path and 
                    "recommended_courses" in learning_path and 
                    "learning_goals" in learning_path):
                    self.log_test("AI Learning Path", True, f"Learning path with {len(learning_path['recommended_courses'])} recommendations")
                else:
                    self.log_test("AI Learning Path", False, "Learning path missing required fields")
                
                # Check AI insights structure
                if ("overall_performance" in ai_insights and 
                    "strengths" in ai_insights and 
                    "recommendations" in ai_insights):
                    self.log_test("AI Progress Analysis", True, f"AI insights with {len(ai_insights['recommendations'])} recommendations")
                else:
                    self.log_test("AI Progress Analysis", False, "AI insights missing required fields")
            else:
                self.log_test("AI Functions via Dashboard", False, f"Status: {status}")
        
        # Test teacher recommendations
        if self.student_token:
            success, data, status = self.make_request("GET", "/teachers/recommendations/Programming", auth_token=self.student_token)
            if success and "recommendations" in data:
                recommendations = data["recommendations"]
                if len(recommendations) > 0 and "match_score" in recommendations[0]:
                    self.log_test("AI Teacher Recommendations", True, f"{len(recommendations)} teacher recommendations with match scores")
                else:
                    self.log_test("AI Teacher Recommendations", False, "Recommendations missing required fields")
            else:
                self.log_test("AI Teacher Recommendations", False, f"Status: {status}")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting NovaZone Backend API Testing")
        print("=" * 60)
        
        # Initialize with sample data
        self.test_seed_data()
        
        # Authentication Tests
        print("🔐 AUTHENTICATION TESTS")
        print("-" * 30)
        self.test_auth_register_student()
        self.test_auth_register_teacher()
        self.test_auth_login()
        self.test_auth_login_invalid()
        self.test_auth_me()
        
        # Dashboard Tests
        print("📊 DASHBOARD TESTS")
        print("-" * 30)
        self.test_dashboard_student()
        self.test_dashboard_teacher()
        
        # Course Tests
        print("📚 COURSE TESTS")
        print("-" * 30)
        self.test_courses_list()
        self.test_courses_filter()
        self.test_course_create()
        self.test_course_enroll()
        
        # Teacher Tests
        print("👨‍🏫 TEACHER TESTS")
        print("-" * 30)
        self.test_teachers_list()
        self.test_teachers_filter()
        self.test_teacher_recommendations()
        self.test_teacher_profile_update()
        
        # Progress Tests
        print("📈 PROGRESS TESTS")
        print("-" * 30)
        self.test_progress_get()
        self.test_progress_update()
        
        # Quiz Tests
        print("❓ QUIZ TESTS")
        print("-" * 30)
        self.test_quiz_get()
        self.test_quiz_submit()
        
        # Community Tests
        print("💬 COMMUNITY TESTS")
        print("-" * 30)
        self.test_community_posts_list()
        self.test_community_posts_filter()
        self.test_community_post_create()
        
        # File Tests
        print("📁 FILE TESTS")
        print("-" * 30)
        self.test_file_upload()
        self.test_file_download()
        
        # Security Tests
        self.test_role_based_access()
        
        # AI Tests
        self.test_ai_placeholder_functions()
        
        print("=" * 60)
        print("🏁 Testing Complete!")

if __name__ == "__main__":
    tester = NovaZoneAPITester()
    tester.run_all_tests()