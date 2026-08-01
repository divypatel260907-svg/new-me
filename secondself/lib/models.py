from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class CaptureMetadata:
    id: str
    timestamp: str
    type: str  # 'note', 'link', 'file'
    source: str
    original_filename: Optional[str] = None
    content_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "source": self.source,
            "original_filename": self.original_filename,
            "content_hash": self.content_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaptureMetadata":
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            type=data["type"],
            source=data["source"],
            original_filename=data.get("original_filename"),
            content_hash=data.get("content_hash")
        )

@dataclass
class CaptureResult:
    id: str
    path: str
    type: str

@dataclass
class WikiNote:
    id: str
    raw_id: str
    para: str  # 'Projects', 'Areas', 'Resources', 'Archives'
    tags: List[str]
    summary: str
    created: str
    links: List[str] = field(default_factory=list)
    body: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "raw_id": self.raw_id,
            "para": self.para,
            "tags": self.tags,
            "summary": self.summary,
            "created": self.created,
            "links": self.links
        }

@dataclass
class GraphNode:
    id: str
    label: str
    para: str
    tags: List[str]
    summary: str
    content_preview: str
    group: str

@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float
    type: str

@dataclass
class AskResult:
    answer: str
    sources: List[Dict[str, Any]]
