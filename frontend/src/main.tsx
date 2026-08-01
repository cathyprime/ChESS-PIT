import React from 'react';
import {createRoot} from 'react-dom/client';
import '@fontsource/unifrakturcook/latin-700.css';
import '@fontsource/metal-mania/latin-400.css';
import '@fontsource/new-rocker/latin-400.css';
import '@fontsource/pirata-one/latin-400.css';
import '@fontsource/oswald/latin-400.css';
import '@fontsource/oswald/latin-600.css';
import '@fontsource/oswald/latin-700.css';
import App from './App';

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
