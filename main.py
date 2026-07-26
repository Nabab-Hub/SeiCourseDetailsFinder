from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from course_scrapper import get_course_data

app = FastAPI()
# Define the CORS middleware
origins = [  # Allow frontend running on localhost:5173
    "*"
]

# Add CORSMiddleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Define a Pydantic model to accept the input parameters
class GetCourseDetails(BaseModel):
    url: str

@app.get("/")
async def home():
    return "The API is working"

@app.post("/get-course-details/")
async def get_course_details(request: GetCourseDetails):
    url = request.url
    print(url)
    course_data = get_course_data(url)
    return course_data