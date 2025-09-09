# from pydantic import BaseModel, Field
# from typing import Optional, List

# class QueryRequest(BaseModel):
#     """
#     Request model for user queries
#     """
#     query: str = Field(..., description="User's input message")
#     session_id: str = Field(..., description="Unique identifier for the conversation session")

# class ToolInput(BaseModel):
#     """
#     Generic model for tool inputs
#     """
#     name: str
#     parameters: dict

# class WeatherToolInput(BaseModel):
#     """
#     Input model for weather tool
#     """
#     city: str

# class DealershipAddressInput(BaseModel):
#     """
#     Input model for dealership address tool
#     """
#     dealership_id: str

# class AppointmentAvailabilityInput(BaseModel):
#     """
#     Input model for checking appointment availability
#     """
#     dealership_id: str
#     date: str  # YYYY-MM-DD format

# class ScheduleAppointmentInput(BaseModel):
#     """
#     Input model for scheduling an appointment
#     """
#     user_id: str
#     dealership_id: str
#     date: str  # YYYY-MM-DD format
#     time: str  # HH:MM format
#     car_model: str


from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    query: str
    session_id: str

class WeatherData(BaseModel):
    temperature: str
    city: str
    conditions: Optional[str] = None

class DealershipAddress(BaseModel):
    dealership_id: str
    name: str
    address: str
    phone: Optional[str] = None

class AppointmentSlot(BaseModel):
    time: str
    available: bool = True

class AppointmentRequest(BaseModel):
    user_id: str
    dealership_id: str
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    car_model: str

class AppointmentConfirmation(BaseModel):
    confirmation_id: str
    status: str
    details: Dict[str, Any]

class ToolResponse(BaseModel):
    name: str
    output: Dict[str, Any]