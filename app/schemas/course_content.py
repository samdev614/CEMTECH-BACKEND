from pydantic import BaseModel, ConfigDict
from typing import List, Optional # Import Optional
from datetime import datetime

# Lesson Schemas
class CourseLessonBase(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    order: int = 0

class CourseLessonCreate(CourseLessonBase):
    uploaded_video_index: Optional[int] = None # Index to link with uploaded file

class CourseLessonUpdate(CourseLessonBase):
    id: Optional[int] = None # ID is optional for updates (new lessons won't have one)
    title: Optional[str] = None # Make title optional for partial updates
    order: Optional[int] = None # Make order optional for partial updates
    uploaded_video_index: Optional[int] = None # Index to link with uploaded file

class CourseLessonOut(CourseLessonBase):
    id: int
    section_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Section Schemas
class CourseSectionBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int = 0

class CourseSectionCreate(CourseSectionBase):
    lessons: List[CourseLessonCreate] = [] # Allow creating lessons nested within sections

class CourseSectionUpdate(CourseSectionBase):
    id: Optional[int] = None # ID is optional for updates (new sections won't have one)
    title: Optional[str] = None # Make title optional for partial updates
    order: Optional[int] = None # Make order optional for partial updates
    lessons: Optional[List[CourseLessonUpdate]] = None # Nested lessons for update

class CourseSectionOut(CourseSectionBase):
    id: int
    course_id: int
    lessons: List[CourseLessonOut] = [] # Output lessons nested within sections
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)