import {Children,createContext,isValidElement,useContext,useEffect,useState,type AnchorHTMLAttributes,type ReactElement,type ReactNode} from 'react';

type RouterState={path:string;navigate:(to:string|number)=>void};
const RouterContext=createContext<RouterState>({path:'/',navigate:()=>{}});
const ParamsContext=createContext<Record<string,string>>({});

export function BrowserRouter({children}:{children:ReactNode}){
 const [path,setPath]=useState(location.pathname);
 useEffect(()=>{const update=()=>setPath(location.pathname);addEventListener('popstate',update);return()=>removeEventListener('popstate',update)},[]);
 const navigate=(to:string|number)=>{if(typeof to==='number'){history.go(to);return}history.pushState(null,'',to);setPath(location.pathname)};
 return <RouterContext.Provider value={{path,navigate}}>{children}</RouterContext.Provider>;
}

type LinkProps={to:string;children:ReactNode}&Omit<AnchorHTMLAttributes<HTMLAnchorElement>,'href'>;
export function Link({to,children,onClick,...props}:LinkProps){const {navigate}=useContext(RouterContext);return <a {...props} href={to} onClick={event=>{onClick?.(event);if(!event.defaultPrevented&&event.button===0&&!event.metaKey&&!event.ctrlKey){event.preventDefault();navigate(to)}}}>{children}</a>}
export function NavLink(props:LinkProps){const {path}=useContext(RouterContext);return <Link {...props} className={[props.className,path===props.to?'active':''].filter(Boolean).join(' ')}/>}
export function useNavigate(){return useContext(RouterContext).navigate}
export function useParams(){return useContext(ParamsContext)}
export function Navigate({to}:{to:string}){const navigate=useNavigate();useEffect(()=>navigate(to),[to]);return null}

type RouteProps={path:string;element:ReactNode};
export function Route(_:RouteProps){return null}
function match(pattern:string,path:string){if(pattern==='*')return {};const expected=pattern.split('/').filter(Boolean),actual=path.split('/').filter(Boolean);if(expected.length!==actual.length)return null;const params:Record<string,string>={};for(let i=0;i<expected.length;i++){if(expected[i].startsWith(':'))params[expected[i].slice(1)]=decodeURIComponent(actual[i]);else if(expected[i]!==actual[i])return null}return params}
export function Routes({children}:{children:ReactNode}){const {path}=useContext(RouterContext);let fallback:ReactElement<RouteProps>|undefined;for(const child of Children.toArray(children)){if(!isValidElement<RouteProps>(child))continue;if(child.props.path==='*'){fallback=child;continue}const params=match(child.props.path,path);if(params)return <ParamsContext.Provider value={params}>{child.props.element}</ParamsContext.Provider>}return fallback?<>{fallback.props.element}</>:null}
