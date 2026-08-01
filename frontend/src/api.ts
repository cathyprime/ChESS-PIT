const base=import.meta.env.VITE_API_URL||'';
export async function api<T=any>(path:string,init:RequestInit={}):Promise<T>{
 const response=await fetch(base+path,{...init,credentials:'include',headers:{...(init.body instanceof FormData?{}:{'Content-Type':'application/json'}),...init.headers}});
 if(!response.ok){let message=response.statusText;try{message=(await response.json()).detail||message}catch{}throw new Error(message)}
 return response.json();
}
