import React from "react";
import WeatherCard from "./WeatherCard";
import YouTubeList from "./YouTubeList";
import NewsList from "./NewsList";

export default function InAppBrowser() {
  return (
    <div style={{ padding: "24px", fontFamily: "Arial, sans-serif" }}>
      <h1 style={{ marginBottom: "20px" }}>OmniCore Dashboard</h1>
      <div style={{ display: "grid", gap: "20px" }}>
        <WeatherCard />
        <YouTubeList />
        <NewsList />
      </div>
    </div>
  );
}
