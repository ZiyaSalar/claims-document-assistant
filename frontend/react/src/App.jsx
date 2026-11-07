import React, { useEffect, useState } from 'react';
import { AppProvider } from './context/AppContext';
import { Shell } from './components/Shell';
import PageErrorBoundary from './components/PageErrorBoundary';
import Home from './pages/Home';
import Claims from './pages/Claims';
import NewClaim from './pages/NewClaim';
import ClaimDetail from './pages/ClaimDetail';
import Agent from './pages/Agent';

function readPath() {
    return window.location.pathname.replace(/\/$/, '') || '/';
}

function RoutedApp() {
    const [path, setPath] = useState(readPath);

    useEffect(() => {
        const handlePopState = () => setPath(readPath());
        window.addEventListener('popstate', handlePopState);

        return () => window.removeEventListener('popstate', handlePopState);
    }, []);

    function go(next) {
        if (next === path) return;

        window.history.pushState({}, '', next);
        setPath(readPath());
        window.scrollTo({ top: 0, behavior: 'auto' });
    }

    let page;

    if (path === '/') {
        page = <Home go={go} />;
    } else if (path === '/claims') {
        page = <Claims go={go} />;
    } else if (path === '/claims/new') {
        page = <NewClaim go={go} />;
    } else if (path === '/agent') {
        page = <Agent />;
    } else if (path.startsWith('/claims/') && path.split('/').length === 3) {
        page = (
            <ClaimDetail
                key={path}
                id={decodeURIComponent(path.split('/')[2])}
                go={go}
            />
        );
    } else {
        page = <Home go={go} />;
    }

    return (
        <Shell path={path} go={go}>
            <PageErrorBoundary resetKey={path}>{page}</PageErrorBoundary>
        </Shell>
    );
}

export default function App() {
    return (
        <AppProvider>
            <RoutedApp />
        </AppProvider>
    );
}
