"""Tests for HTML parsing and article extraction."""
import pytest
from ingestion.parser import parse_article, ParsedArticle, ParsedImage

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>How to Configure Payment Gateways - Brilliant Directories</title>
</head>
<body>
    <div class="breadcrumb">
        <a href="/">Home</a> &gt;
        <a href="/category/finance">Finance & Billing</a> &gt;
        <span>Payment Gateways</span>
    </div>
    
    <main class="article-content">
        <h1>How to Configure Payment Gateways</h1>
        <p>This guide explains how to connect Stripe and PayPal to your directory website.</p>
        
        <h2>Prerequisites</h2>
        <p>Before beginning, ensure you have an active merchant account with Stripe or PayPal.</p>
        
        <img src="https://example.com/images/stripe-setup.png" alt="Stripe Setup Screen" />
        
        <h2>Step 1: Connecting Stripe</h2>
        <p>Navigate to Settings &gt; Payment Gateways in the admin dashboard. Enter your API keys.</p>
        
        <table>
            <tr><th>Gateway</th><th>Supported Currencies</th><th>Transaction Fee</th></tr>
            <tr><td>Stripe</td><td>135+</td><td>2.9% + 30c</td></tr>
            <tr><td>PayPal</td><td>25+</td><td>3.49% + 49c</td></tr>
        </table>
        
        <p>For more help, visit the <a href="https://example.com/billing-faq">Billing FAQ</a>.</p>
    </main>
</body>
</html>
"""


def test_parse_article_title_and_text():
    url = "https://support.brilliantdirectories.com/support/solutions/articles/123-how-to-configure-payment-gateways"
    parsed = parse_article(SAMPLE_HTML, url)

    assert isinstance(parsed, ParsedArticle)
    assert "Payment Gateways" in parsed.title
    assert "Stripe and PayPal" in parsed.content_text
    assert parsed.content_hash != ""
    assert len(parsed.content_hash) == 16


def test_parse_article_headings():
    url = "https://example.com/article"
    parsed = parse_article(SAMPLE_HTML, url)

    heading_texts = [h["text"] for h in parsed.headings]
    assert any("Prerequisites" in t for t in heading_texts)
    assert any("Connecting Stripe" in t for t in heading_texts)


def test_parse_article_images():
    url = "https://example.com/article"
    parsed = parse_article(SAMPLE_HTML, url)

    assert len(parsed.images) >= 1
    img = parsed.images[0]
    assert img.url == "https://example.com/images/stripe-setup.png"
    assert img.alt_text == "Stripe Setup Screen"


def test_parse_article_tables():
    url = "https://example.com/article"
    parsed = parse_article(SAMPLE_HTML, url)

    assert len(parsed.tables) >= 1
    assert "Stripe" in parsed.tables[0]
    assert "135+" in parsed.tables[0]


def test_parse_article_links():
    url = "https://example.com/article"
    parsed = parse_article(SAMPLE_HTML, url)

    assert any("billing-faq" in link["url"] for link in parsed.links)
