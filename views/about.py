# ==============================
# views/about.py (original)
# ==============================
import streamlit as st


def show_about_page():
    """Original about page – company mission and features."""
    st.markdown(
        '<div class="section-heading">About LendAssist Pro</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div style="background:linear-gradient(145deg,#111827,#0b1220); 
                border-radius:16px; padding:24px; margin-bottom:24px;">
        <div style="font-size:24px; font-weight:700; color:#60A5FA;">Our Mission</div>
        <p style="color:#F0F4F8; margin-top:12px;">
            To democratize access to fair credit and provide a trusted car marketplace 
            for Kenyan consumers. We combine machine learning with transparent 
            financial insights to help you make better decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background:#0f1e30; border-radius:12px; padding:20px; text-align:center;">
            <div style="font-size:32px;">🤖</div>
            <div style="font-weight:700;">AI Risk Engine</div>
            <div style="font-size:12px; color:#94A3B8;">Real‑time credit scoring</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:#0f1e30; border-radius:12px; padding:20px; text-align:center;">
            <div style="font-size:32px;">🚗</div>
            <div style="font-weight:700;">Car Marketplace</div>
            <div style="font-size:12px; color:#94A3B8;">Verified listings, valuation tools</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background:#0f1e30; border-radius:12px; padding:20px; text-align:center;">
            <div style="font-size:32px;">💬</div>
            <div style="font-weight:700;">24/7 Support</div>
            <div style="font-size:12px; color:#94A3B8;">Instant chat with our team</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#64748B; font-size:12px;">
        © 2026 LendAssist Pro · Secure · Transparent
    </div>
    """, unsafe_allow_html=True)
