export default async function handler(req,res){
 if(req.method!=="GET")return res.status(405).json({error:"Method not allowed"});
 const key=process.env.OPENROUTER_API_KEY;
 if(!key)return res.status(500).json({error:"Add OPENROUTER_API_KEY in Vercel environment variables."});
 try{
  const r=await fetch("https://openrouter.ai/api/v1/models",{headers:{Authorization:`Bearer ${key}`}});
  const d=await r.json();if(!r.ok)return res.status(r.status).json({error:d?.error?.message||"Model list failed"});
  const models=(d.data||[]).filter(x=>x.id&&x.name).map(x=>({id:x.id,name:x.name})).sort((a,b)=>a.name.localeCompare(b.name));
  res.status(200).json({models});
 }catch{res.status(502).json({error:"Could not reach OpenRouter."})}
}