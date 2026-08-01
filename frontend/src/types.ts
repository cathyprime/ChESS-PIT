export type AvatarStyle='mask'|'legacy';
export type Bot={id:number,name:string,description:string,status:string,rating:number,wins:number,draws:number,losses:number,qualificationDone:number,qualificationTotal:number,failureReason?:string,owned:boolean,system:boolean,engineKind:'uploaded'|'stockfish',stockfishSkill?:number,avatarUrl:string,avatarStyle:AvatarStyle};
export type RatingRun={id?:number,status:'idle'|'queued'|'running'|'completed'|'failed',totalPairings:number,completedPairings:number,totalGames:number,completedGames:number,currentPairing?:string,error?:string};
export type HistoryGame={id:number;mode:string;status:string;whiteName:string;blackName:string;result:string;termination?:string;timeControl:string;createdAt:string;botColor:'white'|'black';opponentId:number|null;opponentName:string;opponentAvatarUrl?:string;opponentAvatarStyle?:AvatarStyle;outcome:'win'|'draw'|'loss'|'pending'|'no-result'};
export type BotHistoryResponse={bot:Bot;total:number;games:HistoryGame[]};
export type Move={uci:string,san:string,fen:string,elapsedMs:number|null};
export type Analysis={eval:number,mate:number|null,best:string|null,pv:string[],depth:number|null}|null;
export type Game={
 id:number;mode:string;status:string;whiteName:string;blackName:string;whiteBotId?:number;blackBotId?:number;whiteAvatarUrl?:string;blackAvatarUrl?:string;whiteAvatarStyle?:AvatarStyle;blackAvatarStyle?:AvatarStyle;
 result:string;termination?:string;timeControl:string;fen:string;turn:'white'|'black';moves:Move[];analysis:Analysis[];
 whiteClockMs:number|null;blackClockMs:number|null;error?:string;canAbort:boolean;humanColor?:'white'|'black';
 moveTimeMs?:number;stockfishSkill?:number;createdAt:string;pgn?:string;analysed?:boolean;
};
