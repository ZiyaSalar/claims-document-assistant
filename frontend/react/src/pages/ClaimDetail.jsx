import React, { useCallback, useEffect, useState } from 'react';
import {
    Activity,
    AlertTriangle,
    ArrowLeft,
    ArrowRight,
    BookOpenText,
    Bot,
    CheckCircle2,
    ChevronRight,
    ClipboardCheck,
    Clock3,
    FileSearch,
    FileText,
    FileUp,
    FolderOpen,
    LoaderCircle,
    MessageCircle,
    MessageSquareText,
    RefreshCcw,
    ScanEye,
    Send,
    ShieldCheck,
    Sparkles,
    Trash2,
    UploadCloud,
    WandSparkles,
} from 'lucide-react';
import { api } from '../api';
import {
    TYPES,
    claimPath,
    pretty,
    shortId,
    useApp,
} from '../context/AppContext';
import {
    Alert,
    Badge,
    Button,
    CardTitle,
    Empty,
    PageHeading,
} from '../components/Shared';
import { DocumentViewer } from '../components/DocumentViewer';
import { Evidence } from '../components/Evidence';

const TAB_DATA = [
    ['overview', 'Overview', FolderOpen],
    ['documents', 'Documents', FileText],
    ['summary', 'AI Summary', Sparkles],
    ['ask', 'Ask AI', MessageSquareText],
    ['review', 'Final review', ShieldCheck],
];
export default function ClaimDetail({ id, go }) {
    const { refresh: refreshClaims } = useApp();
    const [claim, setClaim] = useState(null);
    const [docs, setDocs] = useState([]);
    const [verification, setVerification] = useState(null);
    const [tab, setTab] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [working, setWorking] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [docType, setDocType] = useState('hospital_bill');
    const [file, setFile] = useState(null);
    const [inputKey, setInputKey] = useState(0);
    const [summary, setSummary] = useState(null);
    const [question, setQuestion] = useState('');
    const [questions, setQuestions] = useState([]);
    const [viewedDocumentIds, setViewedDocumentIds] = useState(new Set());
    const [viewer, setViewer] = useState(null);
    const [reviewer, setReviewer] = useState('');
    const [ack, setAck] = useState(false);
    const [confirmText, setConfirmText] = useState('');
    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [c, d, v] = await Promise.all([
                api(`/api/claims/${encodeURIComponent(id)}`),
                api(`/api/claims/${encodeURIComponent(id)}/documents`),
                api(`/api/claims/${encodeURIComponent(id)}/verification`),
            ]);
            setClaim(c);
            setDocs(d || []);
            setVerification(v);
            setError('');
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [id]);
    useEffect(() => {
        setTab('overview');
        setSummary(null);
        setQuestions([]);
        load();
    }, [load]);
    const view = (doc, page = null, quote = '') => {
        setViewedDocumentIds((previous) => {
            const updated = new Set(previous);
            updated.add(doc.document_id);
            return updated;
        });

        setViewer({ doc, page, quote });
    };
    async function upload(e) {
        e.preventDefault();
        if (!file) return;
        setWorking('upload');
        setError('');
        setSuccess('');
        try {
            const form = new FormData();
            form.append('file', file);
            form.append('document_type', docType);
            if (file.size > 10 * 1024 * 1024)
                throw new Error('File exceeds 10 MB.');
            const r = await api(
                `/api/claims/${encodeURIComponent(id)}/documents`,
                { method: 'POST', form }
            );
            setSuccess(
                `${file.name} uploaded · ${r.rag_indexing?.status === 'synchronized' ? 'Search indexing synchronized' : 'Check indexing status'}`
            );
            setFile(null);
            setInputKey((k) => k + 1);
            setSummary(null);
            setQuestions([]);
            await load();
            await refreshClaims();
        } catch (e) {
            setError(e.message);
        } finally {
            setWorking('');
        }
    }
    async function remove(doc) {
        if (!window.confirm(`Delete ${doc.filename}? This cannot be undone.`))
            return;
        setWorking('delete' + doc.document_id);
        setError('');
        try {
            await api(
                `/api/claims/${encodeURIComponent(id)}/documents/${encodeURIComponent(doc.document_id)}`,
                { method: 'DELETE' }
            );
            setSuccess(
                'Document deleted and indexing synchronization requested.'
            );
            setSummary(null);
            setQuestions([]);
            await load();
            await refreshClaims();
        } catch (e) {
            setError(e.message);
        } finally {
            setWorking('');
        }
    }
    async function getSummary() {
        setWorking('summary');
        setError('');
        try {
            const r = await api(
                `/api/claims/${encodeURIComponent(id)}/summary?llm=true`
            );
            setSummary(r);
        } catch (e) {
            setError(e.message);
        } finally {
            setWorking('');
        }
    }
    async function ask(e, asked) {
        e?.preventDefault();
        const q = (asked || question).trim();
        if (!q) return;
        setWorking('ask');
        setError('');
        setQuestion('');
        setQuestions((h) => [...h, { question: q, result: null }]);
        try {
            const r = await api(`/api/claims/${encodeURIComponent(id)}/ask`, {
                method: 'POST',
                body: { question: q },
            });
            setQuestions((h) =>
                h.map((x, i) => (i === h.length - 1 ? { ...x, result: r } : x))
            );
        } catch (e) {
            setError(e.message);
            setQuestions((h) => h.slice(0, -1));
        } finally {
            setWorking('');
        }
    }
    async function acceptDocument(doc) {
        if (!viewedDocumentIds.has(doc.document_id)) {
            setError('Open the original document before accepting it.');
            view(doc);
            return;
        }

        const reviewerName = window.prompt('Enter reviewer name:')?.trim();

        if (!reviewerName) return;

        const selectedDocumentType = window
            .prompt(
                `Enter the correct document category:\n${TYPES.map(
                    ([type, label]) => `${type} — ${label}`
                ).join('\n')}`,
                doc.document_type
            )
            ?.trim();

        if (!TYPES.some(([type]) => type === selectedDocumentType)) {
            setError('Please select a valid document type.');
            return;
        }

        const reason = window
            .prompt('Explain why this document is correct:')
            ?.trim();

        if (!reason || reason.length < 10) {
            setError(
                'Please provide a review reason of at least 10 characters.'
            );
            return;
        }

        const confirmed = window.confirm(
            `Accept "${doc.filename}" as ` +
                `"${pretty(selectedDocumentType)}"?\n\n` +
                'Confirm only after inspecting the original file.'
        );

        if (!confirmed) return;

        setWorking(`accept-${doc.document_id}`);
        setError('');
        setSuccess('');

        try {
            await api(
                `/api/claims/${encodeURIComponent(id)}` +
                    `/documents/${encodeURIComponent(doc.document_id)}` +
                    '/accept',
                {
                    method: 'POST',
                    body: {
                        reviewer_name: reviewerName,
                        reason,
                        reviewed_original: true,
                        document_type: selectedDocumentType,
                    },
                }
            );

            setSuccess(`${doc.filename} accepted by human reviewer.`);

            await load();
            await refreshClaims();
        } catch (error) {
            setError(error.message);
        } finally {
            setWorking('');
        }
    }
    const ready =
        verification?.can_proceed === true &&
        verification?.received_count === verification?.required_count &&
        claim?.status !== 'approved';
    async function approve(e) {
        e.preventDefault();
        if (!ready || !ack || confirmText !== 'APPROVE' || !reviewer.trim())
            return;
        setWorking('approve');
        setError('');
        try {
            const result = await api(
                `/api/claims/${encodeURIComponent(id)}/review/approve`,
                {
                    method: 'POST',
                    body: {
                        reviewer_name: reviewer.trim(),
                        confirmation: 'APPROVE',
                        evidence_reviewed: true,
                    },
                }
            );
            setSuccess(
                `Demo approval recorded for claim ${shortId(id)}. This is not an insurer authorization.`
            );
            await load();
            await refreshClaims();
        } catch (e) {
            setError(e.message);
        } finally {
            setWorking('');
        }
    }
    if (loading && !claim)
        return (
            <div className="page-loader">
                <LoaderCircle className="spin" size={32} /> Loading claim
                workspace…
            </div>
        );
    return (
        <div className="view-enter">
            <div className="detail-back">
                <button onClick={() => go('/claims')}>
                    <ArrowLeft size={16} /> All claims
                </button>
                <ChevronRight size={15} />
                <span>Claim {shortId(id)}</span>
            </div>
            <PageHeading
                eyebrow={`CLAIM · ${shortId(id)}`}
                title={claim?.claimant_name || 'Claim details'}
                description={
                    <>
                        <span className="mono">{id}</span> ·{' '}
                        {claim?.policy_number} · {pretty(claim?.claim_type)}
                    </>
                }
                action={
                    <div className="detail-heading-actions">
                        <Badge
                            value={
                                claim?.status === 'approved'
                                    ? 'approved'
                                    : claim?.verification_status
                            }
                        />
                        <Button variant="outline" onClick={load}>
                            <RefreshCcw size={16} /> Refresh
                        </Button>
                    </div>
                }
            />
            <Alert message={error} onClose={() => setError('')} />
            <Alert
                message={success}
                kind="success"
                onClose={() => setSuccess('')}
            />
            <div className="detail-tabs">
                {TAB_DATA.map(([key, label, Icon]) => (
                    <button
                        key={key}
                        className={tab === key ? 'selected' : ''}
                        onClick={() => setTab(key)}
                    >
                        <Icon size={17} />
                        {label}
                    </button>
                ))}
            </div>
            {tab === 'overview' && (
                <div className="detail-grid">
                    <section className="card">
                        <CardTitle
                            title="Claim overview"
                            subtitle="Important details at a glance"
                        />
                        <div className="facts-grid">
                            <div>
                                <span>Claimant</span>
                                <strong>{claim?.claimant_name}</strong>
                            </div>
                            <div>
                                <span>Policy number</span>
                                <strong>{claim?.policy_number}</strong>
                            </div>
                            <div>
                                <span>Claim type</span>
                                <strong>{pretty(claim?.claim_type)}</strong>
                            </div>
                            <div>
                                <span>Claim status</span>
                                <Badge value={claim?.status} />
                            </div>
                            <div>
                                <span>Verification</span>
                                <Badge
                                    value={verification?.verification_status}
                                />
                            </div>
                            <div>
                                <span>Files uploaded</span>
                                <strong>{docs.length}</strong>
                            </div>
                        </div>
                    </section>
                    <section className="card">
                        <CardTitle
                            title="Document readiness"
                            subtitle="Requirements satisfied by current evidence"
                            action={
                                <span className="fraction">
                                    {verification?.received_count || 0} /{' '}
                                    {verification?.required_count || 4}
                                </span>
                            }
                        />
                        <div className="progress-track">
                            <div
                                style={{
                                    width: `${((verification?.received_count || 0) / (verification?.required_count || 4)) * 100}%`,
                                }}
                            />
                        </div>
                        <div className="checklist">
                            {TYPES.map(([key, label]) => {
                                const satisfied =
                                    !verification?.missing_documents?.includes(
                                        key
                                    );
                                const files = docs.filter(
                                    (d) => d.document_type === key
                                );
                                return (
                                    <div className="checkitem" key={key}>
                                        <span
                                            className={`check-circle ${satisfied ? 'done' : ''}`}
                                        >
                                            {satisfied ? (
                                                <CheckCircle2 size={17} />
                                            ) : (
                                                <Clock3 size={17} />
                                            )}
                                        </span>
                                        <div>
                                            <strong>{label}</strong>
                                            <small>
                                                {satisfied
                                                    ? 'Requirement satisfied'
                                                    : files.length
                                                      ? 'Uploaded · requires review or incomplete'
                                                      : 'Not yet satisfied'}
                                            </small>
                                        </div>
                                        <Badge
                                            value={
                                                satisfied
                                                    ? 'received'
                                                    : files.length
                                                      ? 'needs_review'
                                                      : 'missing'
                                            }
                                        />
                                    </div>
                                );
                            })}
                        </div>
                        <Button
                            variant="outline"
                            onClick={() => setTab('review')}
                        >
                            Go to final review <ArrowRight size={16} />
                        </Button>
                    </section>
                </div>
            )}
            {tab === 'documents' && (
                <div className="detail-grid">
                    <section className="card">
                        <CardTitle
                            title="Uploaded documents"
                            subtitle={`${docs.length} file${docs.length !== 1 ? 's' : ''} in this claim`}
                        />
                        {docs.length ? (
                            <div className="document-cards">
                                {docs.map((d) => (
                                    <div
                                        className="document-card"
                                        key={d.document_id}
                                    >
                                        <span className="document-avatar">
                                            <FileText size={22} />
                                        </span>
                                        <div className="document-meta">
                                            <strong>{d.filename}</strong>
                                            <small>
                                                {pretty(d.document_type)} ·{' '}
                                                {d.file_type?.toUpperCase() ||
                                                    'FILE'}
                                            </small>
                                            <div className="doc-badges">
                                                <Badge
                                                    value={d.document_status}
                                                />
                                                {d.classification?.confidence !=
                                                    null && (
                                                    <span>
                                                        {(
                                                            d.classification
                                                                .confidence *
                                                            100
                                                        ).toFixed(1)}
                                                        % classification
                                                        confidence
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <button
                                            title="View original"
                                            className="icon-btn"
                                            onClick={() => view(d)}
                                        >
                                            <ScanEye size={18} />
                                        </button>
                                        {d.document_status === 'needs_review' &&
                                            claim?.status !== 'approved' && (
                                                <Button
                                                    variant="outline"
                                                    busy={
                                                        working ===
                                                        `accept-${d.document_id}`
                                                    }
                                                    disabled={!!working}
                                                    onClick={() =>
                                                        acceptDocument(d)
                                                    }
                                                >
                                                    <CheckCircle2 size={16} />
                                                    Accept document
                                                </Button>
                                            )}
                                        <button
                                            title="Delete document"
                                            className="icon-btn danger-hover"
                                            disabled={!!working}
                                            onClick={() => remove(d)}
                                        >
                                            <Trash2 size={17} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <Empty
                                title="No documents"
                                description="Attach a PDF, image, or TXT to get started."
                            />
                        )}
                    </section>
                    <section className="card">
                        <CardTitle
                            title="Upload a document"
                            subtitle="OCR, classification and hybrid indexing run automatically"
                        />
                        <form className="upload-area" onSubmit={upload}>
                            <label>
                                Document category
                                <select
                                    value={docType}
                                    onChange={(e) => setDocType(e.target.value)}
                                >
                                    {TYPES.map(([key, label]) => (
                                        <option key={key} value={key}>
                                            {label}
                                        </option>
                                    ))}
                                </select>
                            </label>
                            <label className="file-drop">
                                <FileUp size={27} />
                                <strong>
                                    {file
                                        ? file.name
                                        : 'Choose a file to upload'}
                                </strong>
                                <small>PDF, PNG, JPEG or TXT · max 10 MB</small>
                                <input
                                    key={inputKey}
                                    required
                                    type="file"
                                    accept=".pdf,.png,.jpg,.jpeg,.txt"
                                    onChange={(e) =>
                                        setFile(e.target.files?.[0] || null)
                                    }
                                />
                            </label>
                            <Button
                                busy={working === 'upload'}
                                disabled={!file}
                                type="submit"
                            >
                                <UploadCloud size={17} /> Upload & process
                            </Button>
                        </form>
                        <div className="upload-info">
                            <ShieldCheck size={17} /> Files are claim-scoped. AI
                            classification may mark a file as needing human
                            review.
                        </div>
                    </section>
                </div>
            )}
            {tab === 'summary' && (
                <div className="detail-grid summary-layout">
                    <section className="card summary-main">
                        <CardTitle
                            title="AI claim summary"
                            subtitle="Evidence-informed overview of this specific claim"
                            action={
                                <span className="ai-chip">
                                    <Sparkles size={14} /> GPT-4.1-mini
                                </span>
                            }
                        />
                        {summary ? (
                            <div className="summary-body">
                                <div className="summary-label">
                                    <CheckCircle2 size={17} /> Summary generated
                                </div>
                                <SummaryContent data={summary} />
                                <Button
                                    variant="outline"
                                    busy={working === 'summary'}
                                    onClick={getSummary}
                                >
                                    <RefreshCcw size={16} /> Regenerate summary
                                </Button>
                            </div>
                        ) : (
                            <div className="generate-summary">
                                <span>
                                    <Sparkles size={34} />
                                </span>
                                <h2>Make sense of every detail.</h2>
                                <p>
                                    Get an AI-generated overview that brings
                                    together your claim documents and key review
                                    considerations.
                                </p>
                                <Button
                                    disabled={!docs.length}
                                    busy={working === 'summary'}
                                    onClick={getSummary}
                                >
                                    <WandSparkles size={18} /> Generate AI
                                    summary
                                </Button>
                                {!docs.length && (
                                    <small>
                                        Upload a document first to generate an
                                        evidence-based summary.
                                    </small>
                                )}
                            </div>
                        )}
                    </section>
                    <aside className="card summary-aside">
                        <CardTitle
                            title="Verification snapshot"
                            subtitle="Authoritative checklist status"
                        />
                        <div className="checklist">
                            {TYPES.map(([key, label]) => {
                                const ok =
                                    !verification?.missing_documents?.includes(
                                        key
                                    );
                                return (
                                    <div className="checkitem" key={key}>
                                        <span
                                            className={`check-circle ${ok ? 'done' : ''}`}
                                        >
                                            {ok ? (
                                                <CheckCircle2 size={16} />
                                            ) : (
                                                <Clock3 size={16} />
                                            )}
                                        </span>
                                        <div>
                                            <strong>{label}</strong>
                                        </div>
                                        <Badge
                                            value={ok ? 'received' : 'missing'}
                                        />
                                    </div>
                                );
                            })}
                        </div>
                        <div className="summary-note">
                            <ShieldCheck size={18} /> AI summaries assist
                            review; they do not approve a claim or override the
                            verification checklist.
                        </div>
                    </aside>
                </div>
            )}
            {tab === 'ask' && (
                <div className="qa-layout">
                    <section className="card qa-card">
                        <div className="qa-heading">
                            <span className="qa-heading-icon">
                                <MessageSquareText size={23} />
                            </span>
                            <div>
                                <h3>Ask about this claim</h3>
                                <p>
                                    Answers are grounded in this claim's
                                    uploaded documents, with verifiable sources.
                                </p>
                            </div>
                        </div>
                        <div className="qa-thread">
                            {!questions.length && (
                                <div className="qa-empty">
                                    <span>
                                        <Sparkles size={28} />
                                    </span>
                                    <h3>Find answers in your evidence.</h3>
                                    <p>
                                        Ask about hospital charges, dates,
                                        diagnoses, or information recorded in
                                        the documents.
                                    </p>
                                    <div className="qa-suggestions">
                                        {[
                                            'What is the total hospital bill?',
                                            'What is the admission date?',
                                            'What treatment is documented?',
                                        ].map((q) => (
                                            <button
                                                onClick={() => ask(null, q)}
                                                key={q}
                                            >
                                                {q} <ArrowRight size={15} />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {questions.map((item, i) => (
                                <div key={i} className="qa-exchange">
                                    <div className="qa-question">
                                        <span>You asked</span>
                                        <strong>{item.question}</strong>
                                    </div>
                                    {item.result ? (
                                        <div className="qa-answer">
                                            <div className="answer-heading">
                                                <Sparkles size={17} /> AI answer{' '}
                                                <Badge
                                                    value={
                                                        item.result
                                                            .answer_status
                                                    }
                                                />
                                            </div>
                                            <p>
                                                {item.result.answer ||
                                                    'No answer returned.'}
                                            </p>
                                            <Evidence
                                                result={item.result}
                                                documents={docs}
                                                onView={view}
                                            />
                                            {item.result
                                                .human_review_required && (
                                                <div className="review-reminder">
                                                    <ShieldCheck size={16} />{' '}
                                                    Requires human review before
                                                    any final claim decision.
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="typing-answer">
                                            <LoaderCircle
                                                size={17}
                                                className="spin"
                                            />{' '}
                                            Searching claim evidence…
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                        <form className="qa-form" onSubmit={ask}>
                            <input
                                aria-label="Ask question"
                                value={question}
                                placeholder="Ask a question about the documents…"
                                onChange={(e) => setQuestion(e.target.value)}
                            />
                            <Button
                                type="submit"
                                busy={working === 'ask'}
                                disabled={!question.trim()}
                            >
                                <Send size={17} /> Ask AI
                            </Button>
                        </form>
                    </section>
                </div>
            )}
            {tab === 'review' && (
                <div className="detail-grid">
                    <section className="card">
                        <CardTitle
                            title="Final claim review"
                            subtitle="A human decision, informed by AI and verified documents"
                        />
                        <div
                            className={`review-readiness ${ready ? 'ready' : 'blocked'}`}
                        >
                            <span>
                                {ready ? (
                                    <CheckCircle2 size={25} />
                                ) : (
                                    <AlertTriangle size={25} />
                                )}
                            </span>
                            <div>
                                <strong>
                                    {claim?.status === 'approved'
                                        ? 'Demo approval recorded'
                                        : ready
                                          ? 'Checklist complete — ready for human review'
                                          : 'Not ready for approval'}
                                </strong>
                                <p>
                                    {claim?.status === 'approved'
                                        ? 'This is a prototype approval record, not an insurer authorization.'
                                        : ready
                                          ? 'All required categories currently have accepted evidence. Verify the originals before continuing.'
                                          : `There are ${verification?.missing_documents?.length || 0} unsatisfied document requirements. Resolve these before approval.`}
                                </p>
                            </div>
                        </div>
                        <div className="review-steps">
                            <div>
                                <strong>
                                    1. Review all original documents
                                </strong>
                                <p>
                                    Open each file and compare it with the
                                    extracted details and citation evidence.
                                </p>
                                <Button
                                    variant="outline"
                                    onClick={() => setTab('documents')}
                                >
                                    <ScanEye size={16} /> View documents
                                </Button>
                            </div>
                            <div>
                                <strong>
                                    2. Verify the claim requirements
                                </strong>
                                <p>
                                    AI classifications and checklist completion
                                    are supporting signals, not final decisions.
                                </p>
                                <ul>
                                    {TYPES.map(([key, label]) => (
                                        <li key={key}>
                                            <span>{label}</span>
                                            <Badge
                                                value={
                                                    verification?.missing_documents?.includes(
                                                        key
                                                    )
                                                        ? 'missing'
                                                        : 'received'
                                                }
                                            />
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div>
                                <strong>3. Record the reviewer decision</strong>
                                <p>
                                    Demo-only approval requires explicit
                                    acknowledgement and backend eligibility
                                    validation.
                                </p>
                                {claim?.status === 'approved' ? (
                                    <div className="review-approved">
                                        <CheckCircle2 size={20} /> Approved in
                                        local demonstration mode
                                    </div>
                                ) : (
                                    <form
                                        className="approval-form"
                                        onSubmit={approve}
                                    >
                                        <label>
                                            Reviewer name
                                            <input
                                                value={reviewer}
                                                maxLength={100}
                                                onChange={(e) =>
                                                    setReviewer(e.target.value)
                                                }
                                                placeholder="Your reviewer name"
                                                disabled={!ready}
                                            />
                                        </label>
                                        <label className="check-label">
                                            <input
                                                type="checkbox"
                                                checked={ack}
                                                onChange={(e) =>
                                                    setAck(e.target.checked)
                                                }
                                                disabled={!ready}
                                            />
                                            <span>
                                                I have inspected the original
                                                documents and reviewed the
                                                evidence. I understand this is a
                                                demonstration action.
                                            </span>
                                        </label>
                                        <label>
                                            Type <strong>APPROVE</strong> to
                                            confirm
                                            <input
                                                value={confirmText}
                                                placeholder="APPROVE"
                                                onChange={(e) =>
                                                    setConfirmText(
                                                        e.target.value
                                                    )
                                                }
                                                disabled={!ready}
                                            />
                                        </label>
                                        <Button
                                            busy={working === 'approve'}
                                            disabled={
                                                !ready ||
                                                !ack ||
                                                !reviewer.trim() ||
                                                confirmText !== 'APPROVE'
                                            }
                                            type="submit"
                                        >
                                            <ShieldCheck size={17} />
                                            Record demo approval
                                        </Button>
                                    </form>
                                )}
                            </div>
                        </div>
                    </section>
                    <section className="card">
                        <CardTitle
                            title="Review guardrails"
                            subtitle="Built for responsible decisions"
                        />
                        <div className="guardrail">
                            <ShieldCheck size={23} />
                            <div>
                                <strong>Human decision only</strong>
                                <p>
                                    The AI never calls the approval endpoint. A
                                    reviewer initiates the action.
                                </p>
                            </div>
                        </div>
                        <div className="guardrail">
                            <ClipboardCheck size={23} />
                            <div>
                                <strong>
                                    Server-side checklist enforcement
                                </strong>
                                <p>
                                    The backend rechecks all required document
                                    categories and review flags.
                                </p>
                            </div>
                        </div>
                        <div className="guardrail">
                            <FileSearch size={23} />
                            <div>
                                <strong>Transparent evidence</strong>
                                <p>
                                    Use the citation viewer to compare AI
                                    statements against original files.
                                </p>
                            </div>
                        </div>
                        <div className="guardrail-warning">
                            Prototype approval is disabled unless{' '}
                            <code>ENABLE_DEMO_APPROVAL=true</code>. This is not
                            production insurance adjudication.
                        </div>
                    </section>
                </div>
            )}
            {viewer && (
                <DocumentViewer
                    claimId={id}
                    document={viewer.doc}
                    page={viewer.page}
                    quote={viewer.quote}
                    onClose={() => setViewer(null)}
                />
            )}
        </div>
    );
}
function SummaryContent({ data }) {
    if (typeof data === 'string')
        return <div className="formatted-answer">{data}</div>;
    const obj = data || {};
    const narrative =
        obj.llm_summary ||
        obj.ai_summary ||
        obj.summary ||
        obj.narrative ||
        obj.overview ||
        obj.response;
    return (
        <div className="summary-output">
            {typeof narrative === 'string' ? (
                <div className="formatted-answer">{narrative}</div>
            ) : typeof narrative === 'object' && narrative ? (
                <div className="summary-object">
                    {Object.entries(narrative).map(([key, value]) => (
                        <div key={key}>
                            <strong>{pretty(key)}</strong>
                            <p>
                                {typeof value === 'string'
                                    ? value
                                    : JSON.stringify(value, null, 2)}
                            </p>
                        </div>
                    ))}
                </div>
            ) : (
                <pre>{JSON.stringify(obj, null, 2)}</pre>
            )}
            {obj.citations?.length > 0 && (
                <div className="summary-citation-note">
                    <BookOpenText size={16} /> Summary references:{' '}
                    {obj.citations.length}. Open the claim documents to verify
                    source details.
                </div>
            )}
        </div>
    );
}
