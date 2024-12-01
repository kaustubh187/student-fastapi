import uuid
from fastapi import FastAPI, HTTPException, Path, Query
from typing import List, Optional
from pydantic import BaseModel
from pymongo import MongoClient


app = FastAPI()


client = MongoClient(connection_string)

db = client["studentdb"]
db.students.create_index("id", unique=True)

class Address(BaseModel):
    city: str
    country: str


class StudentCreate(BaseModel):
    name: str
    age: int
    address: Address


class StudentResponse(BaseModel):
    id: str
    name: str
    age: int
    address: Address


class StudentUpdate(BaseModel):
    name: Optional[str]
    age: Optional[int]
    address: Optional[Address]


# Routes
@app.post("/students", status_code=201, response_model=dict)
def create_student(student: StudentCreate):
    student_dict = student.model_dump()
    student_id = str(uuid.uuid4())  
    student_dict["id"] = student_id
    db.students.insert_one(student_dict)
    return {"id": student_id}


@app.get("/students", response_model=List[StudentResponse], status_code=200)
def list_students(
    country: Optional[str] = Query(None, description="Filter by country"),
    age: Optional[int] = Query(None, description="Filter by age >= value"),
):
    query = {}
    if country:
        query["address.country"] = country
    if age:
        query["age"] = {"$gte": age}

    students = db.students.find(query)
    return [
        {**student, "_id": None} for student in students
    ]  


@app.get("/students/{id}", response_model=StudentResponse, status_code=200)
def fetch_student(id: str = Path(..., description="The ID of the student")):
    student = db.students.find_one({"id": id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.pop("_id", None) 
    return student


@app.patch("/students/{id}", status_code=204)
def update_student(
    student_update: StudentUpdate,
    id: str = Path(..., description="The ID of the student"),
):
    update_data = {k: v for k, v in student_update.model_dump(exclude_unset=True).items()}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.students.update_one({"id": id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return


@app.delete("/students/{id}", status_code=200)
def delete_student(id: str = Path(..., description="The ID of the student")):
    result = db.students.delete_one({"id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"detail": "Student deleted successfully"}
