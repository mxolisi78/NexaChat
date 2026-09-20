"""
News fetching service — pulls articles from GNews API and caches them.
"""

import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import NewsArticle

GNEWS_BASE = 'https://gnews.io/api/v4/top-headlines'


def fetch_and_cache(category='general', limit=10):
    """
    Fetch news for a category and store new articles in the DB.
    Returns the number of new articles saved.
    """
    if not settings.GNEWS_API_KEY:
        return 0

    params = {
        'category': category,
        'lang': 'en',
        'max': limit,
        'apikey': settings.GNEWS_API_KEY,
    }

    try:
        resp = requests.get(GNEWS_BASE, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return 0

    saved = 0
    for article in data.get('articles', []):
        url = article.get('url', '')
        if not url:
            continue

        published = article.get('publishedAt', '')
        try:
            published_dt = parse_datetime(published) or timezone.now()
        except (ValueError, TypeError):
            published_dt = timezone.now()

        # Ensure timezone-aware
        if timezone.is_naive(published_dt):
            published_dt = timezone.make_aware(published_dt)

        _, created = NewsArticle.objects.get_or_create(
            url=url,
            defaults={
                'title': article.get('title', '')[:500],
                'description': article.get('description', '') or '',
                'image_url': article.get('image', '') or '',
                'source_name': (article.get('source') or {}).get('name', '')[:200],
                'category': category,
                'published_at': published_dt,
            }
        )
        if created:
            saved += 1

    return saved


def get_recent_articles(category=None, limit=20):
    """Return cached articles, optionally filtered by category."""
    qs = NewsArticle.objects.all()
    if category and category != 'all':
        qs = qs.filter(category=category)
    return qs[:limit]


def cache_is_stale(category='general', hours=6):
    """Check if we need to refresh this category."""
    cutoff = timezone.now() - timedelta(hours=hours)
    return not NewsArticle.objects.filter(
        category=category,
        fetched_at__gte=cutoff,
    ).exists()
