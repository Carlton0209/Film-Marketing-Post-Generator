const express = require("express");
const cors = require("cors");
const path = require("path");
require("dotenv").config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname)); // Serve static files (index.html)

// Root route - serve index.html
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

// Generate film marketing copy using Anthropic API
app.post("/api/generate", async (req, res) => {
  const { prompt } = req.body;

  console.log("Received request:", { prompt });

  // Validate
  if (!prompt) {
    return res.status(400).json({
      success: false,
      error: "Missing prompt",
    });
  }

  // Check for API key
  const API_KEY = process.env.ANTHROPIC_API_KEY;
  if (!API_KEY) {
    console.error("❌ ANTHROPIC_API_KEY not found in environment variables");
    return res.status(500).json({
      success: false,
      error: "Server configuration error: Missing API key",
    });
  }

  try {
    console.log("Calling Anthropic API...");

    // Call Anthropic API
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 1024,
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
      }),
    });

    console.log("API Response status:", response.status);

    if (!response.ok) {
      const errorData = await response.json();
      console.error("API Error:", errorData);
      return res.status(response.status).json({
        success: false,
        error: errorData.error?.message || "API request failed",
      });
    }

    const data = await response.json();
    console.log("API Response received successfully");

    // Extract text from response
    const generatedText = data.content[0].text;

    res.json({
      success: true,
      text: generatedText,
    });
  } catch (error) {
    console.error("Server error:", error);
    res.status(500).json({
      success: false,
      error: error.message || "Internal server error",
    });
  }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✅ Server is running at http://localhost:${PORT}`);
  console.log(`📁 Serving files from: ${__dirname}`);
});