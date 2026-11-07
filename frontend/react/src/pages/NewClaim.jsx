import React, { useState } from 'react';
import {
    ArrowLeft,
    ArrowRight,
    CheckCircle2,
    FilePlus2,
    ShieldCheck,
    Sparkles,
    UserRound,
    WalletCards,
} from 'lucide-react';
import { api } from '../api';
import { useApp, claimPath } from '../context/AppContext';
import { Alert, Button, PageHeading } from '../components/Shared';

export default function NewClaim({ go }) {
    const { refresh } = useApp();
    const [form, setForm] = useState({
        claimant_name: '',
        policy_number: '',
        claim_type: 'hospitalization',
    });
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const valid =
        form.claimant_name.trim() &&
        form.policy_number.trim() &&
        form.claim_type.trim();

    async function submit(e) {
        e.preventDefault();
        if (!valid) return;

        setBusy(true);
        setError('');

        try {
            const data = await api('/api/claims/', {
                method: 'POST',
                body: {
                    claimant_name: form.claimant_name.trim(),
                    policy_number: form.policy_number.trim(),
                    claim_type: form.claim_type.trim(),
                },
            });
            await refresh();
            go(claimPath(data.claim_id));
        } catch (e) {
            setError(e.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="view-enter">
            <PageHeading
                eyebrow="CLAIM INTAKE"
                title="Create a new claim"
                description="Start with the essentials. You can attach documents and review evidence next."
            />
            <div className="create-layout">
                <section className="card create-card">
                    <div className="steps">
                        <span className="step-number">01</span>
                        <span className="step-line" />
                        <span>Claim details</span>
                        <span className="step-line" />
                        <span className="step-muted">02 Documents & review</span>
                    </div>
                    <div className="create-intro">
                        <div className="create-icon">
                            <FilePlus2 size={22} />
                        </div>
                        <h2>Let's get started</h2>
                        <p>
                            Enter the information below to register a new
                            claim.
                        </p>
                    </div>
                    <Alert
                        message={error}
                        onClose={() => setError('')}
                    />
                    <form onSubmit={submit} className="create-form">
                        <label>
                            Claimant full name <span>*</span>
                            <div className="input-icon">
                                <UserRound size={17} />
                                <input
                                    required
                                    maxLength={120}
                                    value={form.claimant_name}
                                    placeholder="e.g. Arav Sharma"
                                    onChange={(e) =>
                                        setForm((f) => ({
                                            ...f,
                                            claimant_name: e.target.value,
                                        }))
                                    }
                                />
                            </div>
                        </label>
                        <label>
                            Policy number <span>*</span>
                            <div className="input-icon">
                                <WalletCards size={17} />
                                <input
                                    required
                                    maxLength={80}
                                    value={form.policy_number}
                                    placeholder="e.g. POL-123456"
                                    onChange={(e) =>
                                        setForm((f) => ({
                                            ...f,
                                            policy_number: e.target.value,
                                        }))
                                    }
                                />
                            </div>
                        </label>
                        <label>
                            Claim type <span>*</span>
                            <select
                                value={form.claim_type}
                                onChange={(e) =>
                                    setForm((f) => ({
                                        ...f,
                                        claim_type: e.target.value,
                                    }))
                                }
                            >
                                <option value="hospitalization">
                                    Hospitalization
                                </option>
                                <option value="accident">Accident</option>
                                <option value="medical_reimbursement">
                                    Medical reimbursement
                                </option>
                            </select>
                            <small>
                                Other claim types may require different
                                checklists; current checklist is a
                                hospitalization prototype.
                            </small>
                        </label>
                        <div className="create-actions">
                            <Button
                                variant="outline"
                                type="button"
                                onClick={() => go('/claims')}
                            >
                                <ArrowLeft size={16} /> Back to claims
                            </Button>
                            <Button
                                disabled={!valid}
                                busy={busy}
                                type="submit"
                            >
                                Create claim <ArrowRight size={17} />
                            </Button>
                        </div>
                    </form>
                </section>
                <aside className="create-aside">
                    <div className="aside-highlight">
                        <Sparkles size={23} />
                        <h3>An intelligent head start</h3>
                        <p>
                            Once created, your claim gets a dedicated
                            workspace for:
                        </p>
                        <div>
                            <CheckCircle2 size={17} /> Document uploads &
                            classification
                        </div>
                        <div>
                            <CheckCircle2 size={17} /> AI-powered summaries
                        </div>
                        <div>
                            <CheckCircle2 size={17} /> Evidence-backed
                            questions
                        </div>
                        <div>
                            <CheckCircle2 size={17} /> Human verification &
                            review
                        </div>
                    </div>
                    <div className="aside-security">
                        <ShieldCheck size={19} />
                        <span>
                            Final claim decisions always require a human
                            reviewer. AI only supports the process.
                        </span>
                    </div>
                </aside>
            </div>
        </div>
    );
}
