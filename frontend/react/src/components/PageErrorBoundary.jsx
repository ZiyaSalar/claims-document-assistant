import React from "react";

export default class PageErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { error: null };
    }

    static getDerivedStateFromError(error) {
        return { error };
    }

    componentDidCatch(error, info) {
        console.error("Page rendering failed:", error, info);
    }

    componentDidUpdate(previousProps) {
        if (
            previousProps.resetKey !== this.props.resetKey &&
            this.state.error
        ) {
            this.setState({ error: null });
        }
    }

    render() {
        if (this.state.error) {
            return (
                <section className="card" style={{ padding: 32 }}>
                    <h2>We couldn't open this page</h2>
                    <p>{this.state.error.message}</p>

                    <button
                        className="primary-button"
                        onClick={() => {
                            this.setState({ error: null });
                            window.history.pushState({}, "", "/");
                            window.dispatchEvent(
                                new PopStateEvent("popstate")
                            );
                        }}
                    >
                        Return to dashboard
                    </button>
                </section>
            );
        }

        return this.props.children;
    }
}
