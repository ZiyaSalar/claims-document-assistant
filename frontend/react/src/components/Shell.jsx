import React, { useEffect, useState } from 'react';
import {
    Activity,
    Bot,
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
    { href: '/', label: 'Home', icon: House },
    { href: '/claims/new', label: 'Create Claim', icon: FilePlus2 },
    { href: '/claims', label: 'All claims', icon: FolderClosed },
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
                        {/* <span className="nav-glint">NEW</span> */}
                    </button>
                </div>
                <div className="sidebar-spacer" />
                {/* <div className="sidebar-footer">
                    <span className="footer-avatar">D</span>
                    <div>
                        <strong>Demo workspace</strong>
                        <small>Development environment</small>
                    </div>
                    <span className="footer-online" />
                </div> */}
            </aside>
            {mobile && (
                <button
                    className="mobile-backdrop"
                    aria-label="Close menu"
                    onClick={() => setMobile(false)}
                />
            )}
            <div className="app-main">
                <button
                    className="mobile-menu"
                    onClick={() => setMobile(true)}
                    aria-label="Open menu"
                >
                    <Menu size={20} />
                </button>
                <main className="page-content">{children}</main>
            </div>
        </div>
    );
}
