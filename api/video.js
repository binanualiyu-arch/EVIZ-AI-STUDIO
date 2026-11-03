// Generic adapter for a provider offering an async text/image-to-video REST API.
// Configure VIDEO_API_URL and VIDEO_API_KEY for the specific provider.
// The provider's request/response schema may differ; adapt this file to that provider's docs.
export default async function handler(req,res){
 if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
 const endpoint=process.env.VIDEO_API_URL, key=process.env.VIDEO_API_KEY;
 if(!endpoint||!key)return res.status(501).json({error:"Video generation is not connected yet. Add a supported provider's VIDEO_API_URL and VIDEO_API_KEY in Vercel, then adapt api/video.js to its documented API."});
 const {prompt,imageUrl,mode="text-to-video"}=req.body||{};
 if(typeof prompt!=="string"||!prompt.trim()||prompt.length>5000)return res.status(400).json({error:"Enter a prompt (maximum 5,000 characters)."});
 if(!["text-to-video","image-to-video"].includes(mode))return res.status(400).json({error:"Unsupported mode."});
 if(mode==="image-to-video"&&typeof imageUrl!=="string")return res.status(400).json({error:"Image-to-video requires an image URL."});
 try{
  const payload={prompt:prompt.trim(),mode,...(imageUrl?{image_url:imageUrl}:{})};
  const r=await fetch(endpoint,{method:"POST",headers:{"Authorization":`Bearer ${key}`,"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const d=await r.json();if(!r.ok)return res.status(r.status).json({error:d?.error?.message||d?.message||"Video provider request failed."});
  res.status(200).json({result:d});
 }catch{return res.status(502).json({error:"Could not reach the configured video provider."})}
}