"""Styles and small HTML blocks for the travel planner UI."""

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Poppins', sans-serif;
}

/* Page background: deep navy with purple and blue glow */
.stApp {
    background:
        radial-gradient(circle at 80% 0%, rgba(120, 80, 255, 0.35), transparent 45%),
        radial-gradient(circle at 10% 90%, rgba(0, 140, 255, 0.20), transparent 40%),
        #0a0e1f;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1229 0%, #0a0e1f 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

/* Sidebar brand block */
.brand {
    text-align: center;
    padding: 1rem 0 1.5rem;
}
.brand-logo {
    font-size: 2.4rem;
    filter: drop-shadow(0 0 12px rgba(140, 90, 255, 0.8));
}
.brand-name {
    color: #ffffff;
    font-weight: 700;
    font-size: 1.15rem;
    margin-top: 0.3rem;
}
.brand-tag {
    color: #8a93b8;
    font-size: 0.78rem;
    letter-spacing: 0.5px;
}

/* Hero section */
.hero {
    padding: 1.5rem 0 1rem;
    animation: fadeInUp 0.8s ease-out;
}
.hero-badge {
    display: inline-block;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #e6e9ff;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}
.hero-title {
    color: #ffffff;
    font-size: 3rem;
    font-weight: 700;
    line-height: 1.15;
    margin: 0 0 0.5rem;
}
.hero-accent {
    background: linear-gradient(90deg, #4cc9f0, #7b61ff, #c77dff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-subtitle {
    color: #cfd6f2;
    font-size: 1.05rem;
    margin: 0;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
"""

SIDEBAR_BRAND_HTML = """
<div class="brand">
<div class="brand-logo">✈️</div>
<div class="brand-name">AI Travel Agent</div>
<div class="brand-tag">Plan · Explore · Travel</div>
</div>
"""

HERO_HTML = """
<div class="hero">
<span class="hero-badge">✨ AI-Powered Travel Planning</span>
<h1 class="hero-title">Dream. Plan. <span class="hero-accent">Travel.</span></h1>
<p class="hero-subtitle">Let AI plan your perfect journey around the world ✈️</p>
</div>
"""
