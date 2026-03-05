from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from orchestrator.streaming.stream_manager import generate_frames
import urllib.parse
import logging

router = APIRouter(tags=["streaming"])

logger = logging.getLogger(__name__)

@router.get("/stream/proxy")
async def stream_proxy(url: str = Query(..., description="RTSP URL to stream"), camera_id: str = Query("unknown")):
    """
    Proxy an RTSP stream to MJPEG.
    URL should be URL-encoded if it contains special characters.
    """
    # In case the URL is double encoded or needs decoding
    # decoded_url = urllib.parse.unquote(url)
    # We trust FastAPI to decode the query param
    
    logger.info(f"Requesting stream for camera {camera_id}: {url}")
    
    return StreamingResponse(
        generate_frames(camera_id, url),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
