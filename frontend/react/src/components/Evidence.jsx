import React from 'react';
import {
    ArrowUpRight,
    BookOpenText,
    CheckCircle2,
    FileSearch,
    Quote,
    ScanEye,
    ShieldCheck,
} from 'lucide-react';

export function Evidence({ result, documents, onView }) {
    const citations = Array.isArray(result?.citations) ? result.citations : [];
    const findings = Array.isArray(result?.findings) ? result.findings : [];

    // Some RAG versions return citation evidence only inside findings.
    const detailedCitations = citations.filter(
        (c) =>
            c &&
            typeof c === 'object' &&
            (c.document_id ||
                c.filename ||
                c.evidence_excerpt ||
                c.quote)
    );
    const sources = detailedCitations.length
        ? detailedCitations
        : findings.filter(
              (f) =>
                  f.filename ||
                  f.document_id ||
                  f.evidence_excerpt
          );
    const extract = (c) => {
        const source = c.source || {};
        return {
            id:
                c.document_id ||
                source.document_id ||
                c.document?.document_id,
            filename:
                c.filename ||
                source.filename ||
                c.document?.filename ||
                c.source_filename,
            page:
                c.page_number ??
                source.page_number ??
                c.page ??
                null,
            quote:
                c.quote ||
                c.excerpt ||
                c.citation_quote ||
                c.supporting_quote ||
                c.evidence_excerpt ||
                c.evidence ||
                c.text ||
                source.quote ||
                '',
            label:
                c.source_id ||
                c.citation_id ||
                c.ref ||
                '',
        };
    };
    const all = sources
        .map(extract)
        .map((c) => ({
            ...c,
            doc:
                documents.find((d) => d.document_id === c.id) ||
                documents.find((d) => d.filename === c.filename),
        }));

    return (
        <div className="evidence-section">
            <div className="evidence-heading">
                <div>
                    <ShieldCheck size={18} />
                    <strong>Evidence & citations</strong>
                </div>
                <span>
                    {all.length} source{all.length !== 1 ? 's' : ''}
                </span>
            </div>
            {!all.length ? (
                <p className="muted-message">
                    No citations were returned. Treat this answer as
                    unverified.
                </p>
            ) : (
                all.map((c, i) => (
                    <div className="citation-card" key={i}>
                        <div className="citation-top">
                            <span className="citation-index">
                                SOURCE {i + 1}
                                {c.label ? ` · ${c.label}` : ''}
                            </span>
                            <span>
                                {c.page
                                    ? `Page ${c.page}`
                                    : 'Page not specified'}
                            </span>
                        </div>
                        <div className="citation-file">
                            <BookOpenText size={17} />
                            <strong>
                                {c.filename || c.doc?.filename || 'Document'}
                            </strong>
                        </div>
                        {c.quote && <blockquote>“{c.quote}”</blockquote>}
                        <button
                            disabled={!c.doc}
                            onClick={() =>
                                c.doc && onView(c.doc, c.page, c.quote)
                            }
                            className="citation-button"
                        >
                            <ScanEye size={16} />
                            {c.doc
                                ? 'Open document & verify'
                                : 'Source document unavailable'}
                            <ArrowUpRight size={15} />
                        </button>
                    </div>
                ))
            )}
            {findings.length > 0 && (
                <details className="findings">
                    <summary>
                        View structured findings ({findings.length})
                    </summary>
                    <pre>{JSON.stringify(findings, null, 2)}</pre>
                </details>
            )}
        </div>
    );
}
