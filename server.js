import express from "express";
import cors from "cors";

const app = express();

app.use(cors());
app.use(express.json());

app.post("/api/amico", async (req, res) => {
  const { message, domain } = req.body || {};

  console.log("Incoming:", message, domain);

  res.json({
    success: true,
    content: `Backend is working. Domain: ${domain}. Message: ${message}`,
  });
});

app.listen(3000, () => {
  console.log("Server running on http://localhost:3000");
});