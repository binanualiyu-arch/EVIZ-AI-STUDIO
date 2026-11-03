
export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const key = process.env.OPENROUTER_API_KEY;

  if (!key) {
    return res.status(500).json({
      error: "OpenRouter API key is not configured."
    });
  }

  const { model, messages } = req.body || {};

  if (
    typeof model !== "string" ||
    !Array.isArray(messages) ||
    messages.length === 0 ||
    messages.length > 40 ||
    messages.some(
      m =>
        !m ||
        !["user", "assistant"].includes(m.role) ||
        typeof m.content !== "string"
    )
  ) {
    return res.status(400).json({
      error: "Invalid conversation."
    });
  }

  try {
    const response = await fetch(
      "https://openrouter.ai/api/v1/chat/completions",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${key}`,
          "Content-Type": "application/json",
          "HTTP-Referer":
            process.env.SITE_URL || "https://eviz-ai-studio.vercel.app",
          "X-Title": "EVIZ AI STUDIO"
        },
        body: JSON.stringify({
          model,
          messages,
          stream: false,
          max_tokens: 2048
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error:
          data?.error?.message ||
          "OpenRouter request failed."
      });
    }

    const reply = data?.choices?.[0]?.message?.content;

    if (typeof reply !== "string") {
      return res.status(502).json({
        error: "The AI model returned no text."
      });
    }

    return res.status(200).json({ reply });

  } catch (error) {
    return res.status(502).json({
      error: "Unable to connect to OpenRouter."
    });
  }
}
