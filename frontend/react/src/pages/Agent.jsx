import React, { useEffect, useRef, useState } from 'react';
import {
    Bot,
    Check,
    CheckCircle2,
    ChevronDown,
    CircleAlert,
    FileText,
    FileUp,
    LoaderCircle,
    MessageCircle,
    Paperclip,
    Plus,
    Send,
    ShieldCheck,
    Sparkles,
    UploadCloud,
    WandSparkles,
    X,
} from 'lucide-react';
import { api } from '../api';
import { Alert, Button } from '../components/Shared';
import { pretty, useApp } from '../context/AppContext';

const initial = [
    {
        role: 'assistant',
        text: 'Hey there! 👋 I’m your claims copilot. I can create claims, guide document uploads, find missing requirements, summarize evidence, and answer document questions. What would you like to do?',
    },
];

export default function Agent() {
    const { refresh } = useApp();
    const [sessionId, setSessionId] = useState(null);
    const [history, setHistory] = useState(initial);
    const [pending, setPending] = useState(null);
    const [message, setMessage] = useState('');
    const [file, setFile] = useState(null);
    const [working, setWorking] = useState(false);
    const [error, setError] = useState('');
    const end = useRef(null);

    useEffect(() => {
        const element = end.current;

        if (typeof element?.scrollIntoView === 'function') {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'end',
            });
        }
    }, [history, pending, working]);

    function accept(data) {
        if (data.session_id) setSessionId(data.session_id);
        if (data.message) {
            setHistory((currentHistory) => [
                ...currentHistory,
                { role: 'assistant', text: data.message },
            ]);
        }

        setPending(
            ['confirm_claim', 'upload_request'].includes(data.type) ? data : null,
        );

        if (data.claim_id || data.type === 'upload_complete') refresh();
    }

    async function send(event, custom) {
        event?.preventDefault();
        const text = (custom || message).trim();

        if (!text || working || pending) return;

        setWorking(true);
        setError('');
        setMessage('');
        setHistory((currentHistory) => [...currentHistory, { role: 'user', text }]);

        try {
            accept(
                await api('/api/chat/message', {
                    method: 'POST',
                    body: { session_id: sessionId, message: text },
                }),
            );
        } catch (error) {
            setError(error.message);
        } finally {
            setWorking(false);
        }
    }

    async function confirm(approved) {
        setWorking(true);
        setError('');

        try {
            accept(
                await api('/api/chat/confirm', {
                    method: 'POST',
                    body: { session_id: sessionId, approved },
                }),
            );
        } catch (error) {
            setError(error.message);
        } finally {
            setWorking(false);
        }
    }

    async function upload() {
        if (!file || !pending) return;

        if (file.size > 10 * 1024 * 1024) {
            setError('File exceeds 10 MB');
            return;
        }

        setWorking(true);
        setError('');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const data = await api(
                `/api/chat/upload?session_id=${encodeURIComponent(sessionId)}`,
                { method: 'POST', form: formData },
            );

            accept(data);

            const result = data.result || {};
            setHistory((currentHistory) => [
                ...currentHistory,
                {
                    role: 'assistant',
                    text: `Uploaded ${result.filename || file.name}. Classification: ${pretty(result.classification?.predicted_type)}. Review status: ${pretty(result.document_status)}. Search indexing: ${pretty(result.rag_indexing?.status)}.`,
                },
            ]);
            setFile(null);
        } catch (error) {
            setError(error.message);
        } finally {
            setWorking(false);
        }
    }

    async function cancelUpload() {
        setWorking(true);
        setError('');

        try {
            accept(
                await api('/api/chat/cancel-upload', {
                    method: 'POST',
                    body: { session_id: sessionId },
                }),
            );
            setFile(null);
        } catch (error) {
            setError(error.message);
        } finally {
            setWorking(false);
        }
    }

    function reset() {
        setSessionId(null);
        setHistory(initial);
        setPending(null);
        setMessage('');
        setFile(null);
        setError('');
    }

    return (
        <div className="agent-page view-enter">
            <div className="agent-header">
                <div className="agent-head-left">
                    <span className="agent-big-icon">
                        <Sparkles size={24} />
                    </span>
                    <div>
                        <span className="eyebrow">YOUR AI WORKMATE</span>
                        <h1>
                            Meet your copilot<span>.</span>
                        </h1>
                        <p>Ask anything about a claim. I'll help you get it done.</p>
                    </div>
                </div>
                <Button variant="outline" onClick={reset}>
                    <Plus size={17} /> New conversation
                </Button>
            </div>

            <div className="agent-workspace">
                <section className="agent-chat">
                    <div className="chat-top">
                        <span className="chat-avatar">
                            <Bot size={20} />
                        </span>
                        <div>
                            <strong>Clarity Copilot</strong>
                            <small>
                                <span className="online-dot" /> Online · MCP connected
                            </small>
                        </div>
                        <span className="chat-model">
                            <Sparkles size={13} /> GPT-4.1-mini
                        </span>
                    </div>

                    <div className="chat-stream">
                        {history.map((item, index) => (
                            <div
                                className={`chat-message ${item.role}`}
                                key={index}
                            >
                                {item.role === 'assistant' && (
                                    <span className="chat-robot">
                                        <Sparkles size={17} />
                                    </span>
                                )}
                                <div className="chat-message-content">
                                    <small>
                                        {item.role === 'assistant' ? 'CLARITY COPILOT' : 'YOU'}
                                    </small>
                                    <p>{item.text}</p>
                                </div>
                            </div>
                        ))}

                        {pending?.type === 'confirm_claim' && (
                            <div className="pending-action">
                                <div className="pending-label">
                                    <ShieldCheck size={19} /> CONFIRM CLAIM CREATION
                                </div>
                                <div className="pending-fields">
                                    <div>
                                        <span>Claimant</span>
                                        <strong>{pending.claim?.claimant_name}</strong>
                                    </div>
                                    <div>
                                        <span>Policy number</span>
                                        <strong>{pending.claim?.policy_number}</strong>
                                    </div>
                                    <div>
                                        <span>Claim type</span>
                                        <strong>{pretty(pending.claim?.claim_type)}</strong>
                                    </div>
                                </div>
                                <div className="pending-actions">
                                    <Button busy={working} onClick={() => confirm(true)}>
                                        <Check size={16} /> Confirm &amp; create
                                    </Button>
                                    <Button
                                        variant="outline"
                                        disabled={working}
                                        onClick={() => confirm(false)}
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </div>
                        )}

                        {pending?.type === 'upload_request' && (
                            <div className="pending-action">
                                <div className="pending-label">
                                    <FileUp size={18} /> DOCUMENT UPLOAD REQUEST
                                </div>
                                <div className="pending-fields">
                                    <div>
                                        <span>Claim ID</span>
                                        <strong className="mono">{pending.claim_id}</strong>
                                    </div>
                                    <div>
                                        <span>Document type</span>
                                        <strong>{pretty(pending.document_type)}</strong>
                                    </div>
                                </div>
                                <label className="file-drop">
                                    <FileUp size={24} />
                                    <strong>{file ? file.name : 'Select a document'}</strong>
                                    <small>PDF, PNG, JPG or TXT · up to 10 MB</small>
                                    <input
                                        type="file"
                                        accept=".pdf,.txt,.png,.jpg,.jpeg"
                                        onChange={(event) =>
                                            setFile(event.target.files?.[0] || null)
                                        }
                                    />
                                </label>
                                <div className="pending-actions">
                                    <Button busy={working} disabled={!file} onClick={upload}>
                                        <UploadCloud size={16} /> Upload file
                                    </Button>
                                    <Button
                                        variant="outline"
                                        disabled={working}
                                        onClick={cancelUpload}
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </div>
                        )}

                        {working && (
                            <div className="chat-typing">
                                <span className="chat-robot">
                                    <Sparkles size={17} />
                                </span>
                                <div>
                                    <i />
                                    <i />
                                    <i />
                                </div>
                                <span>Thinking through your request…</span>
                            </div>
                        )}
                        <div ref={end} />
                    </div>

                    <div className="agent-compose-area">
                        <Alert message={error} onClose={() => setError('')} />
                        <form className="agent-compose" onSubmit={send}>
                            <textarea
                                rows="2"
                                aria-label="Message AI assistant"
                                value={message}
                                disabled={working || !!pending}
                                onChange={(event) => setMessage(event.target.value)}
                                onKeyDown={(event) => {
                                    if (event.key === 'Enter' && !event.shiftKey) {
                                        event.preventDefault();
                                        send(event);
                                    }
                                }}
                                placeholder={
                                    pending
                                        ? 'Complete the pending action first…'
                                        : 'Ask a question or tell me what to do…'
                                }
                            />
                            <button
                                className="agent-send"
                                disabled={!message.trim() || working || !!pending}
                                type="submit"
                                aria-label="Send"
                            >
                                <Send size={20} />
                            </button>
                        </form>
                        <p>
                            <ShieldCheck size={13} /> All AI actions are monitored. Final
                            claim decisions require human review.
                        </p>
                    </div>
                </section>
            </div>
        </div>
    );
}
