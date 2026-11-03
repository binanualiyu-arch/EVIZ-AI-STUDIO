export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).json({
      error: "Method not allowed"
    });
  }

  const key = process.env.OPENROUTER_API_KEY;

  if (!key) {
    return res.status(500).json({
      error: "OpenRouter API key is not configured."
    });
  }

  try {
    const response = await fetch(
      "https://openrouter.ai/api/v1/models",
      {
        headers: {
          Authorization: `Bearer ${key}`
        }
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error:
          data?.error?.message ||
          "Unable to load OpenRouter models."
      });
    }

    const models = (data.data || [])
      .filter(model => {
        if (!model.id || !model.name) {
          return false;
        }

        const inputPrice = Number(model.pricing?.prompt);
        const outputPrice = Number(model.pricing?.completion);

        return (
          model.id.endsWith(":free") ||
          (
            Number.isFinite(inputPrice) &&
            Number.isFinite(outputPrice) &&
            inputPrice === 0 &&
            outputPrice === 0
          )
        );
      })
      .map(model => ({
        id: model.id,
        name: model.name
      }))
      .sort((a, b) =>
        a.name.localeCompare(b.name)
      );

    return res.status(200).json({
      models,
      count: models.length
    });

  } catch (error) {
    return res.status(502).json({
      error: "Could not connect to OpenRouter."
    });
  }
}
