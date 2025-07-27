from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import base64
import json
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

# =======================
# MODELS
# =======================

# User Models
class UserRole(str):
    STUDENT = "student"
    TEACHER = "teacher"

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str  # "student" or "teacher"
    
class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_image: Optional[str] = None
    bio: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    profile_image: Optional[str] = None
    bio: Optional[str] = None

# Course Models
class Course(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    teacher_id: str
    teacher_name: str
    subject: str
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    duration_hours: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    image: Optional[str] = None
    enrolled_students: List[str] = []
    rating: float = 4.5
    total_lessons: int = 0

class CourseCreate(BaseModel):
    title: str
    description: str
    subject: str
    difficulty_level: str
    duration_hours: int
    image: Optional[str] = None
    total_lessons: int = 0

# Teacher Models
class Teacher(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    full_name: str
    email: str
    subjects: List[str]
    experience_years: int
    rating: float = 4.5
    total_students: int = 0
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    hourly_rate: Optional[float] = None

class TeacherCreate(BaseModel):
    subjects: List[str]
    experience_years: int
    bio: Optional[str] = None
    hourly_rate: Optional[float] = None

# Progress Models
class Progress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    course_id: str
    course_title: str
    completion_percentage: float = 0.0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    time_spent_hours: float = 0.0
    quiz_scores: List[float] = []

# Quiz Models
class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    options: List[str]
    correct_answer: int  # index of correct option
    explanation: Optional[str] = None

class Quiz(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    course_id: str
    title: str
    questions: List[QuizQuestion]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class QuizSubmission(BaseModel):
    quiz_id: str
    student_id: str
    answers: List[int]  # indices of selected options
    score: float
    completed_at: datetime = Field(default_factory=datetime.utcnow)

# Community Models
class CommunityPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str
    author_name: str
    title: str
    content: str
    category: str  # "discussion", "question", "announcement"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes: int = 0
    replies: List[str] = []

class PostCreate(BaseModel):
    title: str
    content: str
    category: str

# Token Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# =======================
# UTILITY FUNCTIONS
# =======================

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_doc = await db.users.find_one({"id": user_id})
        if user_doc is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return UserResponse(**user_doc)
    except jwt.PyJSONError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =======================
# AI PLACEHOLDER FUNCTIONS
# =======================

def get_learning_path(student_id: str) -> Dict[str, Any]:
    """Placeholder for OpenAI integration"""
    # TODO: Replace with OpenAI GPT call later
    mock_learning_path = {
        "current_level": "Intermediate",
        "recommended_courses": [
            {
                "course_id": "course_1",
                "title": "Advanced Python Programming",
                "priority": "high",
                "reason": "Based on your progress in basic Python, this is the next logical step"
            },
            {
                "course_id": "course_2", 
                "title": "Data Structures & Algorithms",
                "priority": "medium",
                "reason": "Will strengthen your programming foundation"
            }
        ],
        "learning_goals": [
            "Master object-oriented programming",
            "Understand algorithm complexity",
            "Build real-world projects"
        ],
        "estimated_completion": "6 weeks"
    }
    return mock_learning_path

def recommend_teachers(subject: str, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Placeholder for OpenAI integration"""
    # TODO: Replace with OpenAI GPT call later
    mock_recommendations = [
        {
            "teacher_id": "teacher_1",
            "name": "Dr. Sarah Chen",
            "match_score": 95,
            "reason": "Expert in " + subject + " with 10+ years experience",
            "specialties": [subject, "Project-based learning"],
            "rating": 4.9
        },
        {
            "teacher_id": "teacher_2",
            "name": "Prof. Michael Rodriguez", 
            "match_score": 88,
            "reason": "Excellent track record with beginner to intermediate students",
            "specialties": [subject, "Hands-on approach"],
            "rating": 4.7
        }
    ]
    return mock_recommendations

def generate_quiz_questions(course_id: str, topic: str) -> List[QuizQuestion]:
    """Placeholder for OpenAI integration"""
    # TODO: Replace with OpenAI GPT call later
    mock_questions = [
        QuizQuestion(
            question="What is the main purpose of object-oriented programming?",
            options=[
                "To make code run faster",
                "To organize code into reusable objects", 
                "To use less memory",
                "To write shorter programs"
            ],
            correct_answer=1,
            explanation="OOP helps organize code into reusable, maintainable objects."
        ),
        QuizQuestion(
            question="Which principle of OOP allows hiding internal implementation?",
            options=[
                "Inheritance",
                "Polymorphism",
                "Encapsulation",
                "Abstraction"
            ],
            correct_answer=2,
            explanation="Encapsulation hides the internal state and implementation details."
        )
    ]
    return mock_questions

def analyze_progress(student_id: str) -> Dict[str, Any]:
    """Placeholder for OpenAI integration"""
    # TODO: Replace with OpenAI GPT call later
    mock_analysis = {
        "overall_performance": "Good",
        "strengths": ["Problem solving", "Code implementation"],
        "areas_for_improvement": ["Algorithm optimization", "Code documentation"],
        "recommendations": [
            "Focus more on time complexity analysis",
            "Practice writing clean, documented code",
            "Take on more challenging projects"
        ],
        "next_milestone": "Complete advanced algorithms course",
        "motivation_message": "You're making excellent progress! Keep up the great work."
    }
    return mock_analysis

# =======================
# AUTHENTICATION ROUTES
# =======================

@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    # Store user with hashed password
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    await db.users.insert_one(user_dict)
    
    # Create teacher profile if role is teacher
    if user_data.role == "teacher":
        teacher = Teacher(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            subjects=[],
            experience_years=0
        )
        await db.teachers.insert_one(teacher.dict())
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    user_response = UserResponse(**user.dict())
    
    return Token(access_token=access_token, user=user_response)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"email": user_data.email})
    if not user_doc or not verify_password(user_data.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = create_access_token(data={"sub": user_doc["id"]})
    user_response = UserResponse(**user_doc)
    
    return Token(access_token=access_token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# =======================
# DASHBOARD ROUTES
# =======================

@api_router.get("/dashboard/student/{student_id}")
async def get_student_dashboard(student_id: str):
    # Get learning path from AI
    learning_path = get_learning_path(student_id)
    
    # Get enrolled courses
    enrolled_courses = await db.courses.find({"enrolled_students": student_id}, {"_id": 0}).to_list(10)
    
    # Get progress
    progress_docs = await db.progress.find({"student_id": student_id}, {"_id": 0}).to_list(10)
    
    # Get recent community posts
    recent_posts = await db.community_posts.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "learning_path": learning_path,
        "enrolled_courses": enrolled_courses,
        "progress": progress_docs,
        "recent_posts": recent_posts,
        "ai_insights": analyze_progress(student_id)
    }

@api_router.get("/dashboard/teacher/{teacher_id}")
async def get_teacher_dashboard(teacher_id: str):
    # Get teacher's courses
    teacher_courses = await db.courses.find({"teacher_id": teacher_id}).to_list(20)
    
    # Get student progress for teacher's courses
    course_ids = [course["id"] for course in teacher_courses]
    student_progress = await db.progress.find({"course_id": {"$in": course_ids}}).to_list(100)
    
    # Mock analytics
    analytics = {
        "total_students": len(set([p["student_id"] for p in student_progress])),
        "total_courses": len(teacher_courses),
        "average_completion": 75.5,
        "total_hours_taught": 120.5
    }
    
    return {
        "courses": teacher_courses,
        "student_progress": student_progress,
        "analytics": analytics
    }

# =======================
# COURSE ROUTES
# =======================

@api_router.get("/courses", response_model=List[Course])
async def get_courses(subject: Optional[str] = None, difficulty: Optional[str] = None):
    filter_query = {}
    if subject:
        filter_query["subject"] = subject
    if difficulty:
        filter_query["difficulty_level"] = difficulty
    
    courses = await db.courses.find(filter_query).to_list(50)
    return [Course(**course) for course in courses]

@api_router.post("/courses", response_model=Course)
async def create_course(
    course_data: CourseCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create courses")
    
    course = Course(
        **course_data.dict(),
        teacher_id=current_user.id,
        teacher_name=current_user.full_name
    )
    
    await db.courses.insert_one(course.dict())
    return course

@api_router.post("/courses/{course_id}/enroll")
async def enroll_in_course(
    course_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can enroll in courses")
    
    # Update course enrollment
    await db.courses.update_one(
        {"id": course_id},
        {"$addToSet": {"enrolled_students": current_user.id}}
    )
    
    # Create progress entry
    course = await db.courses.find_one({"id": course_id})
    if course:
        progress = Progress(
            student_id=current_user.id,
            course_id=course_id,
            course_title=course["title"]
        )
        await db.progress.insert_one(progress.dict())
    
    return {"message": "Successfully enrolled in course"}

# =======================
# TEACHER ROUTES
# =======================

@api_router.get("/teachers", response_model=List[Teacher])
async def get_teachers(subject: Optional[str] = None):
    filter_query = {}
    if subject:
        filter_query["subjects"] = {"$in": [subject]}
    
    teachers = await db.teachers.find(filter_query).to_list(50)
    return [Teacher(**teacher) for teacher in teachers]

@api_router.get("/teachers/recommendations/{subject}")
async def get_teacher_recommendations(
    subject: str,
    current_user: UserResponse = Depends(get_current_user)
):
    recommendations = recommend_teachers(subject, current_user.id)
    return {"recommendations": recommendations}

@api_router.put("/teachers/profile")
async def update_teacher_profile(
    profile_data: TeacherCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update profile")
    
    await db.teachers.update_one(
        {"user_id": current_user.id},
        {"$set": profile_data.dict()}
    )
    
    return {"message": "Profile updated successfully"}

# =======================
# PROGRESS ROUTES
# =======================

@api_router.get("/progress/{student_id}")
async def get_student_progress(student_id: str):
    progress_docs = await db.progress.find({"student_id": student_id}).to_list(50)
    
    # Calculate overall stats
    total_courses = len(progress_docs)
    avg_completion = sum([p["completion_percentage"] for p in progress_docs]) / max(total_courses, 1)
    total_time = sum([p["time_spent_hours"] for p in progress_docs])
    
    return {
        "courses": progress_docs,
        "stats": {
            "total_courses": total_courses,
            "average_completion": avg_completion,
            "total_time_hours": total_time
        },
        "ai_analysis": analyze_progress(student_id)
    }

@api_router.put("/progress/{progress_id}")
async def update_progress(
    progress_id: str,
    completion_percentage: float,
    time_spent_hours: float
):
    await db.progress.update_one(
        {"id": progress_id},
        {
            "$set": {
                "completion_percentage": completion_percentage,
                "time_spent_hours": time_spent_hours,
                "last_accessed": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Progress updated successfully"}

# =======================
# QUIZ ROUTES
# =======================

@api_router.get("/quiz/{course_id}")
async def get_course_quiz(course_id: str):
    quiz = await db.quizzes.find_one({"course_id": course_id})
    if not quiz:
        # Generate quiz using AI placeholder
        questions = generate_quiz_questions(course_id, "General")
        quiz = Quiz(
            course_id=course_id,
            title="Course Assessment",
            questions=questions
        )
        await db.quizzes.insert_one(quiz.dict())
    
    return Quiz(**quiz)

@api_router.post("/quiz/submit")
async def submit_quiz(
    submission: QuizSubmission,
    current_user: UserResponse = Depends(get_current_user)
):
    # Calculate score
    quiz = await db.quizzes.find_one({"id": submission.quiz_id})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    correct_answers = 0
    total_questions = len(quiz["questions"])
    
    for i, answer in enumerate(submission.answers):
        if i < len(quiz["questions"]) and answer == quiz["questions"][i]["correct_answer"]:
            correct_answers += 1
    
    score = (correct_answers / total_questions) * 100
    
    # Save submission
    submission.score = score
    submission.student_id = current_user.id
    await db.quiz_submissions.insert_one(submission.dict())
    
    return {
        "score": score,
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "percentage": score
    }

# =======================
# COMMUNITY ROUTES
# =======================

@api_router.get("/community/posts")
async def get_community_posts(category: Optional[str] = None):
    filter_query = {}
    if category:
        filter_query["category"] = category
    
    posts = await db.community_posts.find(filter_query).sort("created_at", -1).to_list(50)
    return posts

@api_router.post("/community/posts")
async def create_community_post(
    post_data: PostCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    post = CommunityPost(
        **post_data.dict(),
        author_id=current_user.id,
        author_name=current_user.full_name
    )
    
    await db.community_posts.insert_one(post.dict())
    return post

# =======================
# FILE UPLOAD ROUTES
# =======================

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Read file content
    content = await file.read()
    
    # Convert to base64 for storage
    file_data = {
        "id": str(uuid.uuid4()),
        "filename": file.filename,
        "content_type": file.content_type,
        "content": base64.b64encode(content).decode(),
        "uploaded_at": datetime.utcnow()
    }
    
    await db.files.insert_one(file_data)
    
    return {
        "file_id": file_data["id"],
        "filename": file.filename,
        "message": "File uploaded successfully"
    }

@api_router.get("/files/{file_id}")
async def get_file(file_id: str):
    file_doc = await db.files.find_one({"id": file_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "filename": file_doc["filename"],
        "content_type": file_doc["content_type"],
        "content": file_doc["content"]  # base64 encoded
    }

# =======================
# DATA SEEDING ROUTE
# =======================

@api_router.post("/seed-data")
async def seed_database():
    """Populate database with sample data for testing"""
    
    # Sample courses
    sample_courses = [
        {
            "id": "course_1",
            "title": "Introduction to Python Programming",
            "description": "Learn Python from scratch with hands-on projects",
            "teacher_id": "teacher_1",
            "teacher_name": "Dr. Sarah Chen",
            "subject": "Programming",
            "difficulty_level": "beginner",
            "duration_hours": 40,
            "total_lessons": 20,
            "rating": 4.8,
            "enrolled_students": ["student_1", "student_2"],
            "created_at": datetime.utcnow()
        },
        {
            "id": "course_2",
            "title": "Data Structures & Algorithms",
            "description": "Master fundamental CS concepts",
            "teacher_id": "teacher_2", 
            "teacher_name": "Prof. Michael Rodriguez",
            "subject": "Computer Science",
            "difficulty_level": "intermediate",
            "duration_hours": 60,
            "total_lessons": 30,
            "rating": 4.7,
            "enrolled_students": ["student_1"],
            "created_at": datetime.utcnow()
        },
        {
            "id": "course_3",
            "title": "Web Development with React",
            "description": "Build modern web applications",
            "teacher_id": "teacher_1",
            "teacher_name": "Dr. Sarah Chen", 
            "subject": "Web Development",
            "difficulty_level": "intermediate",
            "duration_hours": 50,
            "total_lessons": 25,
            "rating": 4.9,
            "enrolled_students": ["student_2"],
            "created_at": datetime.utcnow()
        }
    ]
    
    # Sample teachers
    sample_teachers = [
        {
            "id": "teacher_1",
            "user_id": "teacher_1",
            "full_name": "Dr. Sarah Chen",
            "email": "sarah.chen@novazone.edu",
            "subjects": ["Programming", "Web Development", "Data Science"],
            "experience_years": 12,
            "rating": 4.9,
            "total_students": 150,
            "bio": "Passionate educator with 12+ years of experience in software engineering and education.",
            "hourly_rate": 75.0
        },
        {
            "id": "teacher_2", 
            "user_id": "teacher_2",
            "full_name": "Prof. Michael Rodriguez",
            "email": "michael.rodriguez@novazone.edu",
            "subjects": ["Computer Science", "Algorithms", "Mathematics"],
            "experience_years": 15,
            "rating": 4.7,
            "total_students": 200,
            "bio": "Computer Science professor specializing in algorithms and theoretical CS.",
            "hourly_rate": 80.0
        }
    ]
    
    # Sample community posts
    sample_posts = [
        {
            "id": "post_1",
            "author_id": "student_1",
            "author_name": "Alex Johnson",
            "title": "Best practices for Python coding?",
            "content": "I'm new to Python and wondering what are some best practices I should follow from the beginning?",
            "category": "question",
            "created_at": datetime.utcnow(),
            "likes": 5,
            "replies": []
        },
        {
            "id": "post_2",
            "author_id": "teacher_1", 
            "author_name": "Dr. Sarah Chen",
            "title": "New React Course Available!",
            "content": "I'm excited to announce my new React course is now live. Perfect for those wanting to learn modern web development!",
            "category": "announcement",
            "created_at": datetime.utcnow(),
            "likes": 12,
            "replies": []
        }
    ]
    
    # Insert sample data
    await db.courses.delete_many({})  # Clear existing
    await db.courses.insert_many(sample_courses)
    
    await db.teachers.delete_many({})
    await db.teachers.insert_many(sample_teachers)
    
    await db.community_posts.delete_many({})
    await db.community_posts.insert_many(sample_posts)
    
    return {"message": "Database seeded with sample data successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()