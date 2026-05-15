# ==============================
# views/about.py
# ==============================
import streamlit as st


def show_about(supabase=None):
    """About page – Company information and mission."""
    st.markdown(
        '<div class="section-heading">About LendAssist Pro</div>',
        unsafe_allow_html=True
    )
    
    st.markdown("""
    <div style="background:linear-gradient(145deg,#111827,#0b1220); 
                border-radius:16px; padding:24px; margin-bottom:24px;
                border:1px solid #1f2a36;">
        <div style="font-size:28px; font-weight:700; color:#60A5FA; 
                    margin-bottom:12px;">🚀 Our Mission</div>
        <p style="color:#F0F4F8; font-size:16px; line-height:1.6;">
            To empower individuals and businesses with intelligent financial tools, 
            transparent loan analysis, and a trusted car marketplace – all in one place.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background:#0f1e30; border-radius:16px; padding:20px; 
                    border:1px solid #1e293b; height:100%;">
            <div style="font-size:24px; margin-bottom:12px;">📊</div>
            <div style="color:#F0F4F8; font-size:18px; font-weight:600;">
                Loan Analysis
            </div>
            <p style="color:#94A3B8; font-size:14px; margin-top:8px;">
                Advanced risk assessment and repayment calculators powered by 
                machine learning models.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="background:#0f1e30; border-radius:16px; padding:20px; 
                    border:1px solid #1e293b; height:100%;">
            <div style="font-size:24px; margin-bottom:12px;">🚗</div>
            <div style="color:#F0F4F8; font-size:18px; font-weight:600;">
                Car Marketplace
            </div>
            <p style="color:#94A3B8; font-size:14px; margin-top:8px;">
                Buy and sell cars with advanced filters, real-time valuation, 
                and instant comparison tools.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="background:linear-gradient(145deg,#111827,#0b1220); 
                border-radius:16px; padding:24px; text-align:center;">
        <div style="color:#94A3B8; font-size:14px; margin-bottom:8px;">
            © 2026 LendAssist Pro. All rights reserved.
        </div>
        <div style="color:#64748B; font-size:12px;">
            Secure · Transparent · Trusted by thousands
        </div>
    </div>
    """, unsafe_allow_html=True)
