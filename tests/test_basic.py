"""
Basic tests for the Flask application
"""
import pytest
from app import app


def test_app_exists():
    """Test that the Flask app exists"""
    assert app is not None


def test_app_is_flask():
    """Test that app is a Flask instance"""
    assert hasattr(app, 'route')


MOBILE_UA = ('Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 '
             '(KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36')
DESKTOP_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
GOOGLEBOT_UA = ('Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 '
                'Mobile Safari/537.36 (compatible; Googlebot/2.1; '
                '+http://www.google.com/bot.html)')


def test_desktop_ua_not_blocked():
    client = app.test_client()
    response = client.get('/', headers={'User-Agent': DESKTOP_UA})
    assert response.status_code == 200


def test_mobile_ua_redirected_to_notice():
    client = app.test_client()
    response = client.get('/', headers={'User-Agent': MOBILE_UA})
    assert response.status_code == 302
    assert '/mobile-notice' in response.headers['Location']


def test_mobile_ua_blocked_on_all_sections():
    client = app.test_client()
    for path in ('/browse_product', '/login', '/admin', '/seller', '/rider', '/myAccount'):
        response = client.get(path, headers={'User-Agent': MOBILE_UA})
        assert response.status_code == 302, path
        assert '/mobile-notice' in response.headers['Location'], path


def test_crawler_not_blocked():
    client = app.test_client()
    response = client.get('/', headers={'User-Agent': GOOGLEBOT_UA})
    assert response.status_code == 200


def test_mobile_notice_page_loads():
    client = app.test_client()
    response = client.get('/mobile-notice?next=%2Fbrowse_product')
    assert response.status_code == 200
    assert b'desktop only' in response.data.lower()


def test_allow_endpoint_unblocks_mobile_session():
    client = app.test_client()
    with client:
        blocked = client.get('/', headers={'User-Agent': MOBILE_UA})
        assert blocked.status_code == 302

        allowed = client.post('/mobile-notice/allow')
        assert allowed.status_code == 200

        unblocked = client.get('/', headers={'User-Agent': MOBILE_UA})
        assert unblocked.status_code == 200


def test_static_assets_never_blocked():
    client = app.test_client()
    response = client.get('/static/css/mobile_notice.css', headers={'User-Agent': MOBILE_UA})
    assert response.status_code == 200
