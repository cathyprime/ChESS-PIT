import {useState} from 'react';
import {assetUrl} from './api';
import type {AvatarStyle} from './types';

export function BotAvatar({src,name,style='mask',className='' }:{src?:string|null;name:string;style?:AvatarStyle;className?:string}){
 const [failed,setFailed]=useState(false);
 const initial=name.trim()[0]?.toUpperCase()||'?';
 return <span className={`bot-avatar ${style} ${className}`} aria-hidden="true">{src&&!failed?<img src={assetUrl(src)} alt="" onError={()=>setFailed(true)}/>:<b>{initial}</b>}</span>
}
