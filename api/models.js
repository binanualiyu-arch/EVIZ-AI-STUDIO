export default async function handler(req,res){
 if(req.method!=="GET"){res.setHeader("Allow","GET");return res.status(405).json({error:"Method not allowed"});}
 const key=process.env.OPENROUTER_API_KEY;if(!key)return res.status(500).json({error:"OPENROUTER_API_KEY is not configured in Vercel."});
 try{const r=await fetch("https://openrouter.ai/api/v1/models",{headers:{Authorization:`Bearer ${key}`}});const d=await r.json();if(!r.ok)return res.status(r.status).json({error:d?.error?.message||"Could not load models."});return res.status(200).json({models:(d.data||[]).map(m=>({id:m.id,name:m.name||m.id}))});}
 catch{return res.status(502).json({error:"Could not reach OpenRouter."});}
}