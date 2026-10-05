from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Lead:

    business_name: str

    phone: Optional[str] = None

    rating: Optional[float] = None

    category: Optional[str] = None

    website: bool = False

    city: str = ""

    state: str = ""

    keyword: str = ""

    source: str = "Google Maps"

    status: str = "NEW"

    opportunity: str = "HIGH"

    lead_score: int = 0

    valid_phone: bool = False

    email: Optional[str] = None

    address: str = ""

    notes: str = ""

    raw: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)