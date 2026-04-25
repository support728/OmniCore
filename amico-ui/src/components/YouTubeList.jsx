import { useEffect, useState } from "react";

const API_KEY = import.meta.env.VITE_YOUTUBE_API_KEY;

export default function YouTubeList() {
  const [videos, setVideos] = useState([]);

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        const res = await fetch(
          `https://www.googleapis.com/youtube/v3/search?part=snippet&q=motivation&maxResults=6&type=video&key=${API_KEY}`
        );
        const data = await res.json();
        console.log("YT DATA:", data);
        setVideos(data.items || []);
      } catch (err) {
        console.error("YouTube fetch error:", err);
      }
    };

    fetchVideos();
  }, []);

  return (
    <div>
      <h3>YouTube</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px" }}>
        {videos.map((video) => (
          <div key={video.id.videoId}>
            <img
              src={video.snippet.thumbnails.medium.url}
              alt={video.snippet.title}
              style={{ width: "100%" }}
            />
            <p>{video.snippet.title}</p>
          </div>
        ))}
      </div>
    </div>
  );
}