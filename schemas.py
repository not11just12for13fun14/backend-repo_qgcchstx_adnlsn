"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# ArcynForge core schemas

class Project(BaseModel):
    """
    Projects collection schema
    Collection name: "project"
    """
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Short description")
    language: str = Field("javascript", description="Primary language")
    framework: Optional[str] = Field(None, description="Primary framework")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Editor/build settings")

class TuningJob(BaseModel):
    """
    Model tuning jobs schema
    Collection name: "tuningjob"
    """
    project_id: Optional[str] = Field(None, description="Associated project id")
    model: str = Field("arcyn-prime", description="Model name")
    objective: str = Field(..., description="What to optimize for")
    dataset: Optional[str] = Field(None, description="Dataset reference or URL")
    status: str = Field("queued", description="queued|running|completed|failed")
    params: Dict[str, Any] = Field(default_factory=dict, description="Hyperparameters")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
