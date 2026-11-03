export default async function handler(req,res){
 if(req.method!=="POST")return res.status(405).json({error:"Method not allowed"});
 const key=process.env.OPENROUTER_API_KEY;if(!key)return res.status(500).json({error:"OpenRouter key is not configured."});
 const {model,messages}=req.body||{};
 if(typeof model!=="string"||!Array.isArray(messages)||!messages.length||messages.length>40||
 messages.some(m=>!m||!["user","assistant"].includes(m.role)||typeof m.content!=="string"||m.content.length>20000))
 return res.status(400).json({error:"Invalid conversation."});
 try{
  const r=await fetch("https://openrouter.ai/api/v1/chat/completions",{method:"POST",headers:{Authorization:`Bearer ${key}`,"Content-Type":"application/json","HTTP-Referer":process.env.SITE_URL||"http://localhost:3000","X-Title":"AI Creative Studio"},body:JSON.stringify({model,messages,stream:false,max_tokens:2048})
  const d=await r.json();if(!r.ok)return res.status(r.status).json({error:d?.error?.message||"OpenRouter request failed"});
  const reply=d?.choices?.[0]?.message?.content;if(typeof reply!=="string")return res.status(502).json({error:"Model returned no text."});
  res.status(200).json({reply});
 }catch{res.status(502).json({error:"Could not reach OpenRouter."})}
}
