export type Bot={id:number,name:string,status:string,rating:number,wins:number,draws:number,losses:number,qualificationDone:number,qualificationTotal:number,failureReason?:string,owned:boolean,system:boolean,engineKind:'uploaded'|'stockfish',stockfishSkill?:number};
export type RatingRun={id?:number,status:'idle'|'queued'|'running'|'completed'|'failed',totalPairings:number,completedPairings:number,totalGames:number,completedGames:number,currentPairing?:string,error?:string};
export type Move={uci:string,san:string,fen:string,elapsedMs:number|null};
export type Analysis={eval:number,mate:number|null,best:string|null,pv:string[],depth:number|null}|null;
export type Game={
 id:number;mode:string;status:string;whiteName:string;blackName:string;whiteBotId?:number;blackBotId?:number;
 result:string;termination?:string;timeControl:string;fen:string;turn:'white'|'black';moves:Move[];analysis:Analysis[];
 whiteClockMs:number|null;blackClockMs:number|null;error?:string;canAbort:boolean;humanColor?:'white'|'black';
 moveTimeMs?:number;stockfishSkill?:number;createdAt:string;pgn?:string;analysed?:boolean;
};
