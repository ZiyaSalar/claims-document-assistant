import React from 'react';
import {
    ArrowRight,
    ArrowUpRight,
    Bot,
    CheckCircle2,
    ClipboardCheck,
    Clock3,
    FilePlus2,
    FolderOpen,
    ScanText,
    ShieldCheck,
    Sparkles,
} from 'lucide-react';
import {
    useApp,
    claimPath,
    shortId,
} from '../context/AppContext';
import {
    Badge,
    Button,
    CardTitle,
    Empty,
    Stat,
} from '../components/Shared';

export default function Home({ go }) {
    const { claims } = useApp();
    const approved = claims.filter((c) => c.status === 'approved').length;
    const review = claims.filter(
        (c) =>
            c.verification_status === 'ready_for_review' &&
            c.status !== 'approved'
    ).length;
    const incomplete = claims.filter(
        (c) =>
            c.verification_status !== 'ready_for_review' &&
            c.status !== 'approved'
    ).length;

    return (
        <div className="view-enter">
            <div className="hero">
                <div className="hero-copy">
                    <div className="hero-tag">
                        <Sparkles size={14} /> Intelligent claims workspace
                    </div>
                    <h1>
                        Claim Document Completeness
                        <br />
                        <em>& Case Summarizer</em>
                    </h1>
                    {/* <p>
                        One beautiful workspace for every document, every
                        insight, and every decision. Powered by AI, guided by
                        people.
                    </p> */}
                    <div className="hero-actions">
                        <Button onClick={() => go('/claims/new')}>
                            <FilePlus2 size={17} /> Create a claim{' '}
                            <ArrowRight size={16} />
                        </Button>
                        <Button
                            variant="light"
                            onClick={() => go('/agent')}
                        >
                            <Sparkles size={16} /> Claim AI Agent
                        </Button>
                    </div>
                </div>
                <div className="hero-art" aria-hidden="true">
                    <div className="orbit o1" />
                    <div className="orbit o2" />
                    <div className="hero-mini-card floating">
                        <span>
                            <ScanText size={19} />
                        </span>
                        <div>
                            <small>DOCUMENT ANALYSIS</small>
                            <strong>Evidence, connected.</strong>
                        </div>
                        <CheckCircle2 size={18} />
                    </div>
                    <div className="hero-stack">
                        <div className="stack-top">
                            <div className="mini-dots">
                                <i />
                                <i />
                                <i />
                            </div>
                            <span>CLAIM INTELLIGENCE</span>
                        </div>
                        <div className="stack-icon">
                            <ShieldCheck size={34} />
                        </div>
                        <div className="stack-lines">
                            <b />
                            <b />
                            <b />
                        </div>
                        <div className="stack-status">
                            <span /> Review ready
                        </div>
                    </div>
                </div>
            </div>
            <div className="section-minihead">
                <div>
                    <h2>Workspace</h2>
                    {/* <p>A live look at your claims activity</p> */}
                </div>
                {/* <span className="subtle-label">LIVE OVERVIEW</span> */}
            </div>
            <div className="stats-grid">
                <Stat
                    icon={FolderOpen}
                    label="Total claims"
                    value={claims.length}
                    caption="Across your workspace"
                />
                <Stat
                    icon={Clock3}
                    label="Incomplete"
                    value={incomplete}
                    caption="Awaiting required evidence"
                    tone="amber"
                />
                <Stat
                    icon={ClipboardCheck}
                    label="Ready for review"
                    value={review}
                    caption="Checklist satisfied"
                    tone="cyan"
                />
                <Stat
                    icon={ShieldCheck}
                    label="Approved"
                    value={approved}
                    caption="Human-reviewed claims"
                    tone="green"
                />
            </div>
            <div className="home-grid">
                <section className="card activity-card">
                    <CardTitle
                        title="Recent claims"
                        subtitle=""
                        action={
                            <button
                                className="text-link"
                                onClick={() => go('/claims')}
                            >
                                View all <ArrowRight size={15} />
                            </button>
                        }
                    />
                    {claims.length ? (
                        claims.slice(0, 5).map((c) => (
                            <button
                                className="recent-row"
                                key={c.claim_id}
                                onClick={() => go(claimPath(c.claim_id))}
                            >
                                <span className="recent-icon">
                                    <FolderOpen size={18} />
                                </span>
                                <span className="recent-info">
                                    <strong>{c.claimant_name}</strong>
                                    <small>
                                        {shortId(c.claim_id)} · {c.policy_number}
                                    </small>
                                </span>
                                <Badge
                                    value={
                                        c.status === 'approved'
                                            ? 'approved'
                                            : c.verification_status
                                    }
                                />
                                <ArrowUpRight size={17} />
                            </button>
                        ))
                    ) : (
                        <Empty
                            title="No claims yet"
                            description="Create your first fictional claim to get started."
                            action={
                                <Button onClick={() => go('/claims/new')}>
                                    Create claim
                                </Button>
                            }
                        />
                    )}
                </section>
                <section className="card quick-card">
                    <CardTitle
                        title="Shortcuts"
                        subtitle=""
                    />
                    <button
                        className="shortcut"
                        onClick={() => go('/claims/new')}
                    >
                        <span className="shortcut-icon purple">
                            <FilePlus2 size={19} />
                        </span>
                        <span>
                            <strong>Start a new claim</strong>
                            <small>
                                Register a new claimant in seconds
                            </small>
                        </span>
                        <ArrowRight size={17} />
                    </button>
                    <button
                        className="shortcut"
                        onClick={() => go('/claims')}
                    >
                        <span className="shortcut-icon blue">
                            <FolderOpen size={19} />
                        </span>
                        <span>
                            <strong>Review claim evidence</strong>
                            <small>Documents, summaries and citations</small>
                        </span>
                        <ArrowRight size={17} />
                    </button>
                    <button
                        className="shortcut"
                        onClick={() => go('/agent')}
                    >
                        <span className="shortcut-icon peach">
                            <Bot size={19} />
                        </span>
                        <span>
                            <strong>AI Agent</strong>
                            <small>
                                Handle claims through conversation
                            </small>
                        </span>
                        <ArrowRight size={17} />
                    </button>
                    <div className="quick-note">
                        <ShieldCheck size={17} />
                        <span>
                            Every final decision stays with a human reviewer.
                        </span>
                    </div>
                </section>
            </div>
        </div>
    );
}
