import React from 'react';
import {
    AlertCircle,
    ArrowRight,
    CheckCircle2,
    FileText,
    Info,
    LoaderCircle,
    X,
} from 'lucide-react';
import { pretty } from '../context/AppContext';

export function Badge({ value, children }) {
    const v = String(value || '').toLowerCase();
    const tone = [
        'approved',
        'received',
        'ready_for_review',
        'completed',
        'synchronized',
        'grounded',
    ].includes(v)
        ? 'success'
        : ['needs_review', 'incomplete', 'pending', 'submitted'].includes(v)
          ? 'warning'
          : v === 'missing' || v === 'failed'
            ? 'danger'
            : 'neutral';

    return (
        <span className={`pill pill-${tone}`}>
            {children || pretty(value)}
        </span>
    );
}

export function Button({
    children,
    variant = 'primary',
    busy,
    ...props
}) {
    return (
        <button
            className={`btn btn-${variant}`}
            disabled={busy || props.disabled}
            {...props}
        >
            {busy ? (
                <LoaderCircle size={16} className="spin" />
            ) : (
                children
            )}
        </button>
    );
}

export function Alert({ message, onClose, kind = 'error' }) {
    return message ? (
        <div className={`alert alert-${kind}`} role="alert">
            <AlertCircle size={17} />
            <span>{message}</span>
            {onClose && (
                <button onClick={onClose} aria-label="Dismiss">
                    <X size={17} />
                </button>
            )}
        </div>
    ) : null;
}

export function Empty({
    icon: Icon = FileText,
    title,
    description,
    action,
}) {
    return (
        <div className="empty-state">
            <span className="empty-symbol">
                <Icon size={28} />
            </span>
            <h3>{title}</h3>
            <p>{description}</p>
            {action}
        </div>
    );
}

export function PageHeading({
    eyebrow,
    title,
    description,
    action,
}) {
    return (
        <div className="page-heading">
            <div>
                <div className="eyebrow">{eyebrow}</div>
                <h1>{title}</h1>
                {description && <p>{description}</p>}
            </div>
            {action && <div className="page-actions">{action}</div>}
        </div>
    );
}

export function Stat({
    label,
    value,
    caption,
    icon: Icon,
    tone = 'indigo',
}) {
    return (
        <div className="stat">
            <div className={`stat-icon tone-${tone}`}>
                <Icon size={21} />
            </div>
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
            {caption && <div className="stat-caption">{caption}</div>}
        </div>
    );
}

export function CardTitle({ title, subtitle, action }) {
    return (
        <div className="card-heading">
            <div>
                <h3>{title}</h3>
                {subtitle && <p>{subtitle}</p>}
            </div>
            {action}
        </div>
    );
}
