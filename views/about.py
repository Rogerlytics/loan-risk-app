# ==============================
# views/about.py
# ==============================
import streamlit as st


def show_about_page():
    st.markdown(
        '<div class="page-title">AI Loan Risk Platform</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="page-subtitle">'
        'Intelligent credit evaluation for smarter lending'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown('<div class="about-card">', unsafe_allow_html=True)

        st.markdown(
            '<div class="about-heading" style="text-align:center;">'
            'About This Platform</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p class="about-text" style="text-align:center;">'
            'The AI Loan Risk Platform is a state-of-the-art credit '
            'assessment tool that leverages machine learning to provide '
            'real-time risk evaluation for vehicle loans. Designed for '
            'both financial institutions and individual borrowers, it '
            'delivers transparent, data-driven insights to support '
            'smarter lending decisions.</p>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="about-heading" style="text-align:center;">'
            'Key Features</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <ul class="feature-list" style="text-align:center;
            list-style-position:inside;">
            <li><strong>Instant Risk Scoring</strong> — Proprietary ML
                model evaluates applicant profiles in milliseconds.</li>
            <li><strong>Repayment Calculator</strong> — View monthly,
                weekly, and daily instalments instantly.</li>
            <li><strong>Integrated Support Chat</strong> — Real-time
                conversation with customer service.</li>
            <li><strong>Admin Dashboard</strong> — Comprehensive overview
                of all conversations and system metrics.</li>
            <li><strong>Secure Authentication</strong> — Role-based access
                with full audit logging.</li>
            <li><strong>Premium Dark Interface</strong> — Optimised for
                long-duration use with minimal eye strain.</li>
        </ul>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="about-heading" style="text-align:center;">'
            'Contact & Support</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p class="about-text" style="text-align:center;">'
            'For inquiries, feedback, or technical support, please use '
            'the <strong>Contact</strong> page within the app. Our team '
            'typically responds within a few hours during business days.'
            '</p>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="about-heading" style="text-align:center;">'
            'Version</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p class="about-text" style="text-align:center;">'
            'v2.0.0 — May 2026</p>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
