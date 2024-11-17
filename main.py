from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import os
from bson import ObjectId
# Imported every module which are required for the project


app = FastAPI()
# Created the app

# Mongodb database part
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.schoolblog  #  my Database name


posts_collection = db.posts  # Collection for blog posts

# Pydantic 
class Post(BaseModel):
    title: str
    content: str
    author: str
    created_at: Optional[str] = None
    
# Pydantic Extended for id
class PostInResponse(Post):
    _id: str

# Dependency to fetch all blog posts from MongoDB
async def get_all_posts():
    posts_cursor = posts_collection.find()
    posts = await posts_cursor.to_list(length=100)
    return posts

# API route to fetch all blog posts
@app.get("/posts", response_model=List[PostInResponse])
async def get_posts():
    posts = await get_all_posts()
    return posts
# API route to fetch a single post by ID
@app.get("/posts/{post_id}", response_model=PostInResponse)
async def get_post(post_ids: str):
    try:
        post_id = ObjectId(post_ids)  # Convert the string to an ObjectId
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID format")
    post = await posts_collection.find_one({"_id": post_id})
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return PostInResponse(_id=str(post["_id"]), title=post["title"], content=post["content"], author=post["author"])

# API route to create a new post
@app.post("/posts", response_model=PostInResponse)
async def create_post(post: Post):
    new_post = {
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "created_at": post.created_at or "2024-01-01"  # Set a default date if none provided
    }
    result = await posts_collection.insert_one(new_post)
    created_post = await posts_collection.find_one({"_id": result.inserted_id})
    return PostInResponse(_id=str(created_post["_id"]), **created_post)

# API route to delete a post
@app.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    result = await posts_collection.delete_one({"_id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}

# API route to update a post
@app.put("/posts/{post_id}", response_model=PostInResponse)
async def update_post(post_id: str, post: Post):
    update_data = {key: value for key, value in post.dict().items() if value is not None}
    result = await posts_collection.update_one({"_id": post_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    updated_post = await posts_collection.find_one({"_id": post_id})
    return PostInResponse(id=str(updated_post["_id"]), **updated_post)
