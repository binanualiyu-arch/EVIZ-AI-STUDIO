# EVIZ AI Studio

A mobile-first AI creator workspace with:
- OpenRouter model chat
- Creator workflows: documentary scripts, cinematic shot lists, storyboard prompts, YouTube packaging
- Video Studio UI for text-to-video and image-to-video requests

## Deploy

1. Revoke any API key previously pasted into a chat or public place. Create a fresh OpenRouter key at https://openrouter.ai/settings/keys.
2. Upload the contents of this folder to a GitHub repository.
3. Import the repository into Vercel.
4. Add `OPENROUTER_API_KEY` in Vercel → Project → Settings → Environment Variables.
5. Deploy and open the URL on iPhone Safari. Use Share → Add to Home Screen.

## Video rendering is a separate integration

The Video Studio screen is included, but it does not magically render video through OpenRouter. To enable rendering, choose a video provider that offers an API and adapt `api/video.js` to its documented request, job polling, and output response format. Add provider credentials only as Vercel environment variables:
- `VIDEO_API_URL`
- `VIDEO_API_KEY`

Do not place API keys in `public/index.html` or commit them to GitHub. Different video providers have different API schemas, model access, pricing, duration limits and image-upload requirements. This starter deliberately does not pretend that a generic endpoint can work with every provider.

Chat conversations are stored in the browser's local storage and are not synced between devices. The current video endpoint is a generic adapter placeholder; a production integration should include provider-specific job polling, upload handling, rate limits, usage caps and error handling.
