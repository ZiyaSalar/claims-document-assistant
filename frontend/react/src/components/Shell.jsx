import React, { useEffect, useState } from 'react';
import {
    Activity,
    ArrowUpRight,
    Bot,
    ChevronRight,
    CircleHelp,
    Command,
    FilePlus2,
    FolderClosed,
    House,
    Layers3,
    Menu,
    PanelLeftClose,
    Search,
    ShieldCheck,
    Sparkles,
    X,
} from 'lucide-react';
import { useApp } from '../context/AppContext';

const NAV = [
    { href: '/', label: 'Overview', icon: House },
    { href: '/claims', label: 'All claims', icon: FolderClosed },
    { href: '/claims/new', label: 'Create claim', icon: FilePlus2 },
    { href: '/agent', label: 'AI Assistant', icon: Bot },
];
export function Shell({ path, go, children }) {
    const [mobile, setMobile] = useState(false);
    const { claims } = useApp();
    useEffect(() => setMobile(false), [path]);
    const active = (href) =>
        href === '/'
            ? path === '/'
            : href === '/claims'
              ? path === '/claims' ||
                (/^\/claims\/[^/]+/.test(path) && path != '/claims/new')
              : path === href;
    return (
        <div className="shell">
            <aside className={`sidebar ${mobile ? 'mobile-open' : ''}`}>
                <div
                    className="brand"
                    onClick={() => go('/')}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && go('/')}
                >
                    <span className="brand-icon">
                        <Layers3 size={21} strokeWidth={2.3} />
                    </span>
                    <div>
                        <strong>
                            clarity<span>.</span>
                        </strong>
                        <small>CLAIMS INTELLIGENCE</small>
                    </div>
                </div>
                <div className="nav-section">
                    <span className="nav-label">WORKSPACE</span>
                    {NAV.slice(0, 3).map(({ href, label, icon: Icon }) => (
                        <button
                            key={href}
                            className={`nav-item ${active(href) ? 'active' : ''}`}
                            onClick={() => go(href)}
                        >
                            <Icon size={18} />
                            <span>{label}</span>
                            {href === '/claims' && (
                                <span className="nav-count">
                                    {claims.length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
                <div className="nav-section">
                    <span className="nav-label">INTELLIGENCE</span>
                    <button
                        className={`nav-item ${active('/agent') ? 'active' : ''}`}
                        onClick={() => go('/agent')}
                    >
                        <Sparkles size={18} />
                        <span>AI Agent</span>
                        <span className="nav-glint">NEW</span>
                    </button>
                </div>
                <div className="sidebar-spacer" />
                <div className="sidebar-assist">
                    <div className="assist-spark">
                        <Sparkles size={17} />
                    </div>
                    <h4>Work smarter with AI</h4>
                    <p>
                        Search documents, summarize claims and surface evidence
                        in seconds.
                    </p>
                    <button onClick={() => go('/agent')}>
                        Open AI assistant <ArrowUpRight size={14} />
                    </button>
                </div>
                <div className="sidebar-footer">
                    <span className="footer-avatar">D</span>
                    <div>
                        <strong>Demo workspace</strong>
                        <small>Development environment</small>
                    </div>
                    <span className="footer-online" />
                </div>
            </aside>
            {mobile && (
                <button
                    className="mobile-backdrop"
                    aria-label="Close menu"
                    onClick={() => setMobile(false)}
                />
            )}
            <div className="app-main">
                <header className="topbar">
                    <div className="crumbs">
                        <button
                            className="mobile-menu"
                            onClick={() => setMobile(true)}
                            aria-label="Menu"
                        >
                            <Menu size={20} />
                        </button>
                        <span>Workspace</span>
                        <ChevronRight size={14} />
                        <strong>
                            {path === '/'
                                ? 'Overview'
                                : path === '/claims'
                                  ? 'All claims'
                                  : path === '/claims/new'
                                    ? 'New claim'
                                    : path === '/agent'
                                      ? 'AI Agent'
                                      : 'Claim details'}
                        </strong>
                    </div>
                    <div className="topbar-end">
                        <span className="env-chip">
                            <span /> DEMO ENVIRONMENT
                        </span>
                        <button className="top-avatar" title="Demo reviewer">
                            D
                        </button>
                    </div>
                </header>
                <main className="page-content">{children}</main>
            </div>
        </div>
    );
}
