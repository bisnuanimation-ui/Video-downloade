import os
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI(title="ClipRelay Python Server", version="1.0.0")

# CORS এনাবল করা যাতে যেকোনো ফ্রন্টএন্ড থেকে রিকোয়েস্ট গ্রহণ করতে পারে
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# অপশনাল সিকিউরিটি টোকেন (অ্যাপে দেওয়া কী-র সাথে মিলতে হবে)
SERVER_API_KEY = os.environ.get("SERVER_API_KEY", "cliprelay-secure-key")


def verify_key(x_api_key: str = Header(None)):
  if SERVER_API_KEY and x_api_key != SERVER_API_KEY:
    raise HTTPException(status_code=401, detail="Invalid API Key")


@app.get("/health")
def health_check():
  return {
      "status": "online",
      "message": "ClipRelay Python Server is running smoothly!",
  }


@app.get("/api/info")
def get_video_info(
    url: str = Query(..., description="Video URL"),
    x_api_key: str = Header(None),
):
  verify_key(x_api_key)
  try:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=False)

      formats_list = []
      for f in info.get("formats", []):
        if f.get("url"):
          formats_list.append({
              "format_id": f.get("format_id"),
              "ext": f.get("ext"),
              "resolution": f.get("resolution")
              or f"{f.get('height', 'audio')}p",
              "filesize": f.get("filesize") or f.get("filesize_approx", 0),
              "url": f.get("url"),
              "vcodec": f.get("vcodec", "none"),
              "acodec": f.get("acodec", "none"),
          })

      return {
          "title": info.get("title"),
          "duration": info.get("duration"),
          "thumbnail": info.get("thumbnail"),
          "uploader": info.get("uploader"),
          "formats": formats_list,
      }
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
  import uvicorn

  uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
