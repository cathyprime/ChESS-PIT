import {useMemo,useState} from 'react';
import {Chess} from 'chess.js';
import {Chessboard,defaultPieces,type ChessboardOptions,type PieceRenderObject} from 'react-chessboard';
import {assetUrl} from './api';
import type {AvatarStyle} from './types';

type Props={fen:string;orientation:'white'|'black';interactive?:boolean;lastMove?:string;whiteAvatarUrl?:string;blackAvatarUrl?:string;whiteAvatarStyle?:AvatarStyle;blackAvatarStyle?:AvatarStyle;onMove?:(uci:string)=>void};

export function ArenaBoard({fen,orientation,interactive=false,lastMove,whiteAvatarUrl,blackAvatarUrl,whiteAvatarStyle='mask',blackAvatarStyle='mask',onMove}:Props){
 const [selected,setSelected]=useState<string>();
 const [promotion,setPromotion]=useState<{from:string,to:string}>();
 const chess=useMemo(()=>new Chess(fen),[fen]);
 const destinations=selected?chess.moves({square:selected as any,verbose:true}).map(move=>move.to):[];
 const submit=(from:string,to:string,piece?:string)=>{
  const candidates=chess.moves({square:from as any,verbose:true}).filter(move=>move.to===to);
  if(!candidates.length)return false;
  if(candidates.some(move=>move.promotion)&&!piece){setPromotion({from,to});return false}
  onMove?.(from+to+(piece||''));setSelected(undefined);return true;
 };
 const squareStyles:Record<string,React.CSSProperties>={};
 if(selected)squareStyles[selected]={boxShadow:'inset 0 0 0 4px #e7b84b'};
 for(const square of destinations)squareStyles[square]={background:'radial-gradient(circle, rgba(34,75,48,.48) 0 18%, transparent 20%)'};
 if(lastMove && lastMove.length>=4){squareStyles[lastMove.slice(0,2)]={background:'rgba(236,190,64,.48)'};squareStyles[lastMove.slice(2,4)]={background:'rgba(236,190,64,.58)'}}
 const pieces=useMemo<PieceRenderObject>(()=>Object.fromEntries(Object.entries(defaultPieces).map(([pieceType,DefaultPiece])=>[pieceType,(props:any)=>{
  const white=pieceType.startsWith('w');
  const avatar=assetUrl(white?whiteAvatarUrl:blackAvatarUrl);
  const avatarStyle=white?whiteAvatarStyle:blackAvatarStyle;
  return <div className="piece-with-mask"><DefaultPiece {...props}/>{avatar&&<span className={`piece-mask ${avatarStyle}`}><img src={avatar} alt="" draggable={false}/></span>}</div>
 }])),[whiteAvatarUrl,blackAvatarUrl,whiteAvatarStyle,blackAvatarStyle]);
 const options:ChessboardOptions={
  id:'deathpit-board',position:fen,boardOrientation:orientation,showNotation:true,animationDurationInMs:0,pieces,
  darkSquareStyle:{backgroundColor:'#3b2827'},lightSquareStyle:{backgroundColor:'#e2d1ad'},squareStyles,
  allowDragging:interactive,allowDrawingArrows:!interactive,
  canDragPiece:({piece})=>interactive&&piece.pieceType[0].toLowerCase()===(chess.turn()==='w'?'w':'b'),
  onPieceDrop:({sourceSquare,targetSquare})=>targetSquare?submit(sourceSquare,targetSquare):false,
  onSquareClick:({piece,square})=>{if(!interactive)return;if(selected&&submit(selected,square))return;if(piece&&piece.pieceType[0].toLowerCase()===(chess.turn()==='w'?'w':'b'))setSelected(square);else setSelected(undefined)},
  boardStyle:{borderRadius:'2px',boxShadow:'0 0 0 2px #120908, 0 8px 24px rgba(0,0,0,.64)'},
 };
 return <div className="arena-board"><Chessboard options={options}/>{promotion&&<div className="promotion"><span>Promote to</span>{[['q','♛'],['r','♜'],['b','♝'],['n','♞']].map(([code,glyph])=><button key={code} onClick={()=>{submit(promotion.from,promotion.to,code);setPromotion(undefined)}}>{glyph}</button>)}<button className="cancel" onClick={()=>setPromotion(undefined)}>Cancel</button></div>}</div>
}
